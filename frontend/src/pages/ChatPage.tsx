import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import {
  ArchiveRestore,
  Bot,
  ChevronDown,
  ChevronUp,
  Loader2,
  MessageSquareText,
  Plus,
  Search,
  Send,
  Sparkles,
  Square,
  Table2,
} from 'lucide-react';
import { useAuth } from '../auth/AuthProvider';
import { SqlPanel } from '../components/data-qa/SqlPanel';
import { ResultChart } from '../components/data-qa/ResultChart';
import { claimDevelopmentConversations, getConversation, listConversations, streamAnalyzeQuestion } from '../api/analysisClient';
import { ApiError } from '../api/client';
import type { AnalysisResponse, AnalysisRow, AnalysisValue, ConversationDetail, ConversationMessage } from '../types/analysis';

type ChatError = {
  message: string;
  status?: number;
  detail?: string;
};

type ChatItem = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  sql?: string;
  rows?: AnalysisResponse['rows'];
  visualization?: AnalysisResponse['visualization'];
  error?: ChatError;
  streaming?: boolean;
};

type Session = {
  id: string;
  title: string;
  updatedAt: string;
  status: 'active' | 'waiting_for_clarification' | 'cancelled';
};

const starterQuestions = [
  '当前订单总数是多少？',
  '2017 年订单金额是多少？',
  '销售额最高的前 5 个品类是什么？',
];

const columnLabels: Record<string, string> = {
  order_date: '日期',
  month: '月份',
  daily_sales: '销售额',
  sales_amount: '销售额',
  order_count: '订单数',
  avg_order_value: '平均客单价',
  refund_rate: '退款率',
  success_rate: '成功率',
  failure_rate: '失败率',
  gross_margin: '毛利率',
  repeat_rate: '复购率',
  category_label: '品类',
  product_label: '商品',
  city_label: '城市',
  payment_method_label: '支付方式',
  segment_label: '分组',
};

function getResultColumns(rows: AnalysisRow[]) {
  const seen = new Set<string>();
  rows.forEach((row) => Object.keys(row).forEach((key) => seen.add(key)));
  return Array.from(seen).slice(0, 6);
}

function formatColumnLabel(column: string) {
  return columnLabels[column] ?? column.replaceAll('_', ' ');
}

function isNumericLike(value: AnalysisValue) {
  return typeof value === 'number';
}

function formatCellValue(column: string, value: AnalysisValue) {
  if (value === null || value === undefined || value === '') return '--';
  if (typeof value === 'boolean') return value ? '是' : '否';
  if (typeof value !== 'number') {
    const text = String(value);
    if ((column.includes('date') || column.includes('month')) && /^\d{4}-\d{2}-\d{2}T/.test(text)) {
      return column.includes('month') ? text.slice(0, 7) : text.slice(0, 10);
    }
    return text;
  }
  if (column.includes('rate') || column.includes('margin')) return `${value.toFixed(2)}%`;
  if (column.includes('sales') || column.includes('amount') || column.includes('value')) return `¥${Math.round(value).toLocaleString()}`;
  if (Number.isInteger(value)) return value.toLocaleString();
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function toChatError(error: unknown): ChatError {
  if (error instanceof ApiError) {
    if (error.status === 0) return { message: '暂时连不上本地分析服务，请确认后端服务已启动后再试。', status: error.status, detail: error.detail ?? error.message };
    if (error.status === 503) return { message: '模型未生成符合已确认业务口径的安全查询，系统未执行数据库。请稍后重试。', status: error.status, detail: error.detail ?? error.message };
    if (error.status >= 500) return { message: '分析服务暂时没有完成这次查询，请稍后重试。', status: error.status, detail: error.detail ?? error.message };
    return { message: error.message || '这次问题没有通过校验，请调整问题后再试。', status: error.status, detail: error.detail };
  }
  return { message: '分析过程被中断了，请稍后重试。' };
}

function messageFromHistory(message: ConversationMessage): ChatItem {
  return {
    id: message.id,
    role: message.role,
    text: message.content,
    error: message.role === 'assistant' && message.response?.failure ? { message: message.content } : undefined,
  };
}

function prependUnique(older: ChatItem[], current: ChatItem[]) {
  const ids = new Set(current.map((message) => message.id));
  return [...older.filter((message) => !ids.has(message.id)), ...current];
}

function ErrorCard({ error }: { error: ChatError }) {
  return (
    <div className="border border-amber-200 bg-amber-50 p-4" style={{ borderRadius: 8 }}>
      <p className="text-sm font-semibold text-amber-950">本次分析未完成</p>
      <p className="mt-1 text-sm leading-6 text-amber-900">{error.message}</p>
      {error.status ? <p className="mt-2 text-xs text-amber-700">错误码：{error.status}</p> : null}
    </div>
  );
}

function ResultTable({ rows }: { rows: AnalysisRow[] }) {
  const columns = getResultColumns(rows);
  if (!columns.length) return null;
  return (
    <div className="overflow-hidden border border-slate-200 bg-white" style={{ borderRadius: 8 }}>
      <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
        <Table2 className="h-4 w-4 text-teal-600" /> 查询结果
      </div>
      <div className="max-h-80 overflow-auto">
        <table className="w-full min-w-[620px] text-sm">
          <thead className="bg-slate-50 text-left text-xs text-slate-500">
            <tr>
              {columns.map((column) => <th key={column} className="px-4 py-3 font-medium">{formatColumnLabel(column)}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={`${index}-${JSON.stringify(row).slice(0, 40)}`} className="border-t border-slate-100">
                {columns.map((column) => (
                  <td key={column} className={['px-4 py-3 text-slate-700', isNumericLike(row[column]) ? 'text-right font-mono' : ''].join(' ')}>
                    {formatCellValue(column, row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AnalysisDetails({ sql, rows, visualization }: Pick<ChatItem, 'sql' | 'rows' | 'visualization'>) {
  const [open, setOpen] = useState(false);
  if (!sql && !rows?.length) return null;
  return (
    <section className="overflow-hidden border border-slate-200 bg-slate-50/70" style={{ borderRadius: 8 }}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-semibold text-slate-800 hover:bg-slate-100"
        aria-expanded={open}
      >
        <span>查询详情{rows?.length ? ` (${rows.length} 行)` : ''}</span>
        {open ? <ChevronUp className="h-4 w-4 text-teal-700" /> : <ChevronDown className="h-4 w-4 text-teal-700" />}
      </button>
      {open ? (
        <div className="max-h-[min(62vh,720px)] space-y-4 overflow-y-auto border-t border-slate-200 p-4">
          {sql ? <SqlPanel sql={sql} compact title="已执行 SQL" /> : null}
          {rows?.length && visualization ? <ResultChart rows={rows} visualization={visualization} /> : null}
          {rows?.length ? <ResultTable rows={rows.slice(0, 30)} /> : null}
        </div>
      ) : null}
    </section>
  );
}

export function ChatPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionCursor, setSessionCursor] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<ChatItem[]>([]);
  const [hasMoreMessages, setHasMoreMessages] = useState(false);
  const [nextBefore, setNextBefore] = useState<string | null>(null);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [loadingMoreSessions, setLoadingMoreSessions] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const streamAbortRef = useRef<AbortController | null>(null);

  const messageVirtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 190,
    overscan: 6,
  });

  const refreshSessions = useCallback(async () => {
    try {
      const page = await listConversations();
      setSessions(page.items.map((item) => ({ id: item.id, title: item.title, updatedAt: item.updated_at, status: item.status })));
      setSessionCursor(page.next_cursor);
    } catch {
      setSessions([]);
      setSessionCursor(null);
    }
  }, []);

  useEffect(() => { void refreshSessions(); }, [refreshSessions]);

  const scrollToLatest = useCallback(() => {
    window.requestAnimationFrame(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'auto' }));
  }, []);

  const openSession = useCallback(async (sessionId: string) => {
    try {
      const detail: ConversationDetail = await getConversation(sessionId);
      setActiveSession(sessionId);
      setMessages(detail.messages.map(messageFromHistory));
      setHasMoreMessages(detail.has_more);
      setNextBefore(detail.next_before);
      scrollToLatest();
    } catch (error) {
      const friendlyError = toChatError(error);
      setMessages([{ id: `e-${Date.now()}`, role: 'assistant', text: friendlyError.message, error: friendlyError }]);
      setHasMoreMessages(false);
      setNextBefore(null);
    }
  }, [scrollToLatest]);

  const loadOlderMessages = useCallback(async () => {
    if (!activeSession || !nextBefore || loadingOlder) return;
    setLoadingOlder(true);
    const beforeHeight = scrollRef.current?.scrollHeight ?? 0;
    try {
      const detail = await getConversation(activeSession, nextBefore);
      setMessages((current) => prependUnique(detail.messages.map(messageFromHistory), current));
      setHasMoreMessages(detail.has_more);
      setNextBefore(detail.next_before);
      window.requestAnimationFrame(() => {
        const container = scrollRef.current;
        if (container) container.scrollTop += container.scrollHeight - beforeHeight;
      });
    } catch (error) {
      const friendlyError = toChatError(error);
      setMessages((current) => [...current, { id: `e-${Date.now()}`, role: 'assistant', text: friendlyError.message, error: friendlyError }]);
    } finally {
      setLoadingOlder(false);
    }
  }, [activeSession, loadingOlder, nextBefore]);

  const loadMoreSessions = useCallback(async () => {
    if (!sessionCursor || loadingMoreSessions) return;
    setLoadingMoreSessions(true);
    try {
      const page = await listConversations(sessionCursor);
      setSessions((current) => {
        const existing = new Set(current.map((session) => session.id));
        return [...current, ...page.items.filter((item) => !existing.has(item.id)).map((item) => ({ id: item.id, title: item.title, updatedAt: item.updated_at, status: item.status }))];
      });
      setSessionCursor(page.next_cursor);
    } finally {
      setLoadingMoreSessions(false);
    }
  }, [loadingMoreSessions, sessionCursor]);

  const claimHistory = async () => {
    try {
      await claimDevelopmentConversations();
      await refreshSessions();
    } catch (error) {
      const friendlyError = toChatError(error);
      setMessages([{ id: `e-${Date.now()}`, role: 'assistant', text: friendlyError.message, error: friendlyError }]);
    }
  };

  const startNewChat = () => {
    setActiveSession(null);
    setMessages([]);
    setHasMoreMessages(false);
    setNextBefore(null);
    setDraft('');
  };

  const run = async () => {
    const question = draft.trim();
    if (!question || isStreaming) return;
    const assistantId = `a-${Date.now()}`;
    const controller = new AbortController();
    const conversationId = activeSession;
    streamAbortRef.current = controller;
    setIsStreaming(true);
    setDraft('');
    setMessages((current) => [
      ...current,
      { id: `u-${Date.now()}`, role: 'user', text: question },
      { id: assistantId, role: 'assistant', text: '正在连接分析服务...', streaming: true },
    ]);
    scrollToLatest();
    try {
      await streamAnalyzeQuestion(question, conversationId, {
        onStage: (stage) => {
          setMessages((current) => current.map((item) => (
            item.id === assistantId ? { ...item, text: `正在${stage.name}...`, streaming: true } : item
          )));
          scrollToLatest();
        },
        onResult: (data) => {
          if (data.conversation_id) setActiveSession(data.conversation_id);
          setMessages((current) => current.map((item) => (
            item.id === assistantId
              ? { ...item, text: data.summary, sql: data.sql || undefined, rows: data.rows, visualization: data.visualization, streaming: false }
              : item
          )));
          setHasMoreMessages(false);
          setNextBefore(null);
          scrollToLatest();
        },
      }, controller.signal);
    } catch (error) {
      if (controller.signal.aborted) {
        setMessages((current) => current.filter((item) => item.id !== assistantId));
      } else {
        const friendlyError = toChatError(error);
        setMessages((current) => current.map((item) => (
          item.id === assistantId ? { ...item, text: friendlyError.message, error: friendlyError, streaming: false } : item
        )));
      }
      scrollToLatest();
    } finally {
      if (streamAbortRef.current === controller) streamAbortRef.current = null;
      setIsStreaming(false);
      void refreshSessions();
    }
  };

  const cancelStream = () => streamAbortRef.current?.abort();

  const filteredSessions = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    if (!normalized) return sessions;
    return sessions.filter((session) => session.title.toLocaleLowerCase().includes(normalized));
  }, [query, sessions]);

  const activeTitle = useMemo(
    () => sessions.find((session) => session.id === activeSession)?.title ?? '新对话',
    [activeSession, sessions],
  );

  return (
    <div className="mx-auto flex h-[calc(100dvh-120px)] max-w-[1440px] overflow-hidden border border-slate-200 bg-white shadow-sm md:h-[calc(100dvh-136px)]" style={{ borderRadius: 8 }}>
      <aside className="flex w-[280px] shrink-0 flex-col border-r border-slate-200 bg-slate-50/80 max-md:hidden">
        <div className="space-y-3 border-b border-slate-200 p-3">
          <button type="button" onClick={startNewChat} className="primary-btn w-full justify-start bg-teal-700 hover:bg-teal-800">
            <Plus className="h-4 w-4" /> 新建对话
          </button>
          <label className="flex items-center gap-2 border border-slate-200 bg-white px-3 py-2 text-slate-500" style={{ borderRadius: 6 }}>
            <Search className="h-4 w-4" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} className="min-w-0 flex-1 bg-transparent text-sm text-slate-800 outline-none" placeholder="搜索已加载会话" />
          </label>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-2">
          <div className="space-y-1">
            {filteredSessions.map((session) => (
              <button
                key={session.id}
                type="button"
                onClick={() => void openSession(session.id)}
                className={[
                  'w-full px-3 py-3 text-left transition',
                  activeSession === session.id ? 'bg-teal-50 text-teal-950' : 'text-slate-700 hover:bg-white',
                ].join(' ')}
                style={{ borderRadius: 6 }}
              >
                <p className="truncate text-sm font-medium">{session.title}</p>
                <p className="mt-1 text-xs text-slate-500">{session.status === 'waiting_for_clarification' ? '等待补充' : new Date(session.updatedAt).toLocaleString()}</p>
              </button>
            ))}
          </div>
          {sessionCursor && !query ? (
            <button type="button" onClick={() => void loadMoreSessions()} disabled={loadingMoreSessions} className="secondary-btn mt-3 w-full text-xs">
              {loadingMoreSessions ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronDown className="h-4 w-4" />}
              加载更多会话
            </button>
          ) : null}
          {user?.role === 'admin' ? (
            <button type="button" onClick={() => void claimHistory()} className="secondary-btn mt-3 w-full text-xs" title="迁移本机匿名历史">
              <ArchiveRestore className="h-4 w-4" /> 迁移本机历史
            </button>
          ) : null}
        </div>
      </aside>

      <section className="flex min-h-0 min-w-0 flex-1 flex-col bg-white">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 px-4">
          <div className="flex min-w-0 items-center gap-2">
            <MessageSquareText className="h-4 w-4 shrink-0 text-teal-700" />
            <span className="truncate text-sm font-semibold text-slate-900">{activeTitle}</span>
          </div>
          <button type="button" onClick={startNewChat} className="secondary-btn px-3 text-xs md:hidden" title="新建对话">
            <Plus className="h-4 w-4" /> 新对话
          </button>
        </header>

        <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto scroll-smooth">
          {hasMoreMessages ? (
            <div className="flex justify-center border-b border-slate-100 py-3">
              <button type="button" onClick={() => void loadOlderMessages()} disabled={loadingOlder} className="secondary-btn px-3 text-xs">
                {loadingOlder ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronUp className="h-4 w-4" />}
                加载更早消息
              </button>
            </div>
          ) : null}

          {messages.length ? (
            <div style={{ height: messageVirtualizer.getTotalSize(), position: 'relative' }}>
              {messageVirtualizer.getVirtualItems().map((virtualRow) => {
                const message = messages[virtualRow.index];
                return (
                  <article
                    key={message.id}
                    ref={messageVirtualizer.measureElement}
                    data-index={virtualRow.index}
                    className="absolute left-0 w-full px-4 py-4 md:px-8"
                    style={{ transform: `translateY(${virtualRow.start}px)` }}
                  >
                    {message.role === 'user' ? (
                      <div className="ml-auto max-w-3xl bg-slate-900 px-4 py-3 text-sm leading-6 text-white" style={{ borderRadius: 8 }}>
                        {message.text}
                      </div>
                    ) : (
                      <div className="mx-auto flex max-w-5xl gap-3">
                        <div className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center bg-teal-700 text-white" style={{ borderRadius: 6 }}>
                          <Bot className="h-4 w-4" />
                        </div>
                        <div className="min-w-0 flex-1 space-y-4">
                          {message.error ? <ErrorCard error={message.error} /> : (
                            <div className="text-sm leading-7 text-slate-700">
                              {message.streaming ? <span className="inline-flex items-center gap-2 text-slate-500"><Loader2 className="h-4 w-4 animate-spin text-teal-700" /> {message.text}</span> : message.text}
                            </div>
                          )}
                          <AnalysisDetails sql={message.sql} rows={message.rows} visualization={message.visualization} />
                        </div>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="mx-auto flex h-full max-w-2xl flex-col justify-center px-6 pb-24">
              <div className="flex items-center gap-3 text-slate-900">
                <div className="grid h-10 w-10 place-items-center bg-teal-700 text-white" style={{ borderRadius: 8 }}><Sparkles className="h-5 w-5" /></div>
                <h1 className="text-xl font-semibold">今天想分析什么？</h1>
              </div>
              <div className="mt-7 grid gap-2 sm:grid-cols-2">
                {starterQuestions.map((question) => (
                  <button key={question} type="button" onClick={() => setDraft(question)} className="border border-slate-200 bg-white px-4 py-3 text-left text-sm text-slate-700 transition hover:border-teal-300 hover:bg-teal-50" style={{ borderRadius: 6 }}>
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="shrink-0 border-t border-slate-200 bg-white p-3 md:p-4">
          <div className="mx-auto flex max-w-4xl items-end gap-3 border border-slate-300 bg-white p-2 shadow-sm" style={{ borderRadius: 8 }}>
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void run();
                }
              }}
              className="min-h-12 max-h-40 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-6 text-slate-800 outline-none"
              placeholder="输入问题"
            />
            <button type="button" onClick={isStreaming ? cancelStream : () => void run()} disabled={!isStreaming && !draft.trim()} className="primary-btn h-10 w-10 shrink-0 p-0 bg-teal-700 hover:bg-teal-800" title={isStreaming ? '取消分析' : '发送'}>
              {isStreaming ? <Square className="h-4 w-4" /> : <Send className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
