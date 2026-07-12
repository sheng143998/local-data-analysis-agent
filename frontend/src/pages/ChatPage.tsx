import { useEffect, useMemo, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { AlertTriangle, ArchiveRestore, Bot, Loader2, MessageSquareText, Send, Sparkles, Table2 } from 'lucide-react';
import { useAuth } from '../auth/AuthProvider';
import { PageHeader } from '../components/common/PageHeader';
import { SqlPanel } from '../components/data-qa/SqlPanel';
import { analyzeQuestion, claimDevelopmentConversations, getConversation, listConversations } from '../api/analysisClient';
import { ApiError } from '../api/client';
import type { AnalysisResponse, AnalysisRow, AnalysisValue, ConversationDetail } from '../types/analysis';

type ChatError = {
  message: string;
  status?: number;
  detail?: string;
};

type ChatItem = {
  id: string;
  role: 'user' | 'assistant';
  title?: string;
  text: string;
  sql?: string;
  rows?: AnalysisResponse['rows'];
  summary?: string;
  error?: ChatError;
  streaming?: boolean;
};

type Session = {
  id: string;
  title: string;
  updatedAt: string;
  status: 'active' | 'waiting_for_clarification' | 'cancelled';
};

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
  rows.forEach((row) => {
    Object.keys(row).forEach((key) => seen.add(key));
  });
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
  if (typeof value !== 'number') return String(value);

  if (column.includes('rate') || column.includes('margin')) {
    return `${value.toFixed(2)}%`;
  }
  if (column.includes('sales') || column.includes('amount') || column.includes('value')) {
    return `¥${Math.round(value).toLocaleString()}`;
  }
  if (Number.isInteger(value)) {
    return value.toLocaleString();
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function toChatError(error: unknown): ChatError {
  if (error instanceof ApiError) {
    if (error.status === 0) {
      return {
        message: '暂时连不上本地分析服务，请确认后端服务已启动后再试。',
        status: error.status,
        detail: error.detail ?? error.message,
      };
    }

    if (error.status >= 500) {
      return {
        message: '分析服务暂时没有完成这次查询，请稍后重试或换一个更具体的问题。',
        status: error.status,
        detail: error.detail ?? error.message,
      };
    }

    return {
      message: error.message || '这次问题没有通过校验，请调整问题后再试。',
      status: error.status,
      detail: error.detail,
    };
  }

  return { message: '分析过程被中断了，请稍后重试。' };
}

function ErrorCard({ error }: { error: ChatError }) {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 p-4" style={{ borderRadius: 8 }}>
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded bg-amber-100 p-1 text-amber-700">
          <AlertTriangle className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <div className="text-sm font-semibold text-amber-950">本次分析未完成</div>
          <p className="mt-1 text-sm leading-6 text-amber-900">{error.message}</p>
          {error.status ? <p className="mt-2 text-xs text-amber-700">错误码：{error.status}</p> : null}
        </div>
      </div>
    </div>
  );
}

export function ChatPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState<ChatItem[]>([
    {
      id: 'a1',
      role: 'assistant',
      title: '本次分析',
      text: '你好，我可以帮你直接询问本地业务数据。你可以像聊天一样提问，比如“最近 30 天销售额按天变化如何？”',
      streaming: false,
    },
  ]);

  const mutation = useMutation({
    mutationFn: (question: string) => analyzeQuestion(question, activeSession),
    onSuccess: (data) => {
      if (data.conversation_id) setActiveSession(data.conversation_id);
      setMessages((current) => [
        ...current.filter((item) => !item.streaming),
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          title: '分析结果',
          text: data.summary,
          sql: data.sql,
          rows: data.rows.slice(0, 5),
          summary: data.summary,
        },
      ]);
      void refreshSessions();
    },
    onError: (error) => {
      const friendlyError = toChatError(error);
      setMessages((current) => [
        ...current.filter((item) => !item.streaming),
        {
          id: `e-${Date.now()}`,
          role: 'assistant',
          title: '分析遇到问题',
          text: friendlyError.message,
          error: friendlyError,
        },
      ]);
      void refreshSessions();
    },
  });

  const refreshSessions = async () => {
    try {
      const items = await listConversations();
      setSessions(items.map((item) => ({ id: item.id, title: item.title, updatedAt: item.updated_at, status: item.status })));
    } catch {
      setSessions([]);
    }
  };

  useEffect(() => { void refreshSessions(); }, []);

  const openSession = async (sessionId: string) => {
    try {
      const detail: ConversationDetail = await getConversation(sessionId);
      setActiveSession(sessionId);
      setMessages(detail.messages.map((message) => ({
        id: message.id,
        role: message.role,
        title: message.role === 'assistant' ? '助手' : undefined,
        text: message.content,
        summary: message.response?.summary,
        error: message.response?.failure ? { message: message.content } : undefined,
      })));
    } catch (error) {
      const friendlyError = toChatError(error);
      setMessages([{ id: `e-${Date.now()}`, role: 'assistant', title: '读取会话失败', text: friendlyError.message, error: friendlyError }]);
    }
  };

  const claimHistory = async () => {
    try {
      await claimDevelopmentConversations();
      await refreshSessions();
    } catch (error) {
      const friendlyError = toChatError(error);
      setMessages([{ id: `e-${Date.now()}`, role: 'assistant', title: '迁移历史失败', text: friendlyError.message, error: friendlyError }]);
    }
  };

  const activeQuestion = useMemo(() => sessions.find((session) => session.id === activeSession)?.title ?? '新会话', [activeSession, sessions]);

  const run = () => {
    const question = draft.trim();
    if (!question) return;
    setMessages((current) => [
      ...current,
      { id: `u-${Date.now()}`, role: 'user', text: question },
      { id: `a-${Date.now()}`, role: 'assistant', text: '正在分析中...', streaming: true },
    ]);
    mutation.mutate(question);
  };

  return (
    <>
      <PageHeader title="数据问答" description="像聊天一样提问，系统会逐步给出自然语言结论、SQL 和简洁结果表。" />
      <div className="grid gap-5 xl:grid-cols-[260px_1fr]">
        <aside className="panel p-4">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900">
            <MessageSquareText className="h-4 w-4 text-cyan-600" /> 会话历史
          </div>
          {user?.role === 'admin' ? (
            <button onClick={() => void claimHistory()} className="mb-3 flex w-full items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50" title="迁移本机匿名历史">
              <ArchiveRestore className="h-4 w-4" /> 迁移本机历史
            </button>
          ) : null}
          <div className="space-y-2">
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => void openSession(session.id)}
                className={[
                  'w-full rounded-md border px-3 py-3 text-left transition',
                  activeSession === session.id ? 'border-cyan-300 bg-cyan-50' : 'border-slate-200 bg-white hover:bg-slate-50',
                ].join(' ')}
              >
                <p className="text-sm font-semibold text-slate-900">{session.title}</p>
                <p className="mt-1 text-xs text-slate-500">{session.status === 'waiting_for_clarification' ? '等待补充信息' : new Date(session.updatedAt).toLocaleString()}</p>
              </button>
            ))}
          </div>
        </aside>

        <section className="panel flex min-h-[780px] flex-col overflow-hidden">
          <div className="border-b border-slate-200 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-900">当前会话</p>
                <p className="text-xs text-slate-500">{activeQuestion}</p>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className="status-dot" />
                只读安全分析
              </div>
            </div>
          </div>

          <div className="flex-1 space-y-5 overflow-auto p-5">
            {messages.map((message) => (
              <article key={message.id} className="space-y-3">
                {message.role === 'user' ? (
                  <div className="ml-auto max-w-3xl rounded-md bg-slate-950 px-4 py-3 text-sm leading-6 text-white" style={{ borderRadius: 8 }}>
                    {message.text}
                  </div>
                ) : (
                  <div className="max-w-5xl space-y-3">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                      <Bot className="h-4 w-4 text-cyan-600" /> {message.title ?? '助手'}
                      {message.streaming ? <Loader2 className="h-4 w-4 animate-spin text-cyan-600" /> : null}
                    </div>

                    {message.error ? (
                      <ErrorCard error={message.error} />
                    ) : (
                      <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm" style={{ borderRadius: 8 }}>
                        <div className="flex items-center gap-2 text-sm font-semibold text-slate-950">
                          <Sparkles className="h-4 w-4 text-emerald-600" /> 回答摘要
                        </div>
                        <p className="mt-2 text-sm leading-7 text-slate-700">{message.text}</p>
                      </div>
                    )}

                    {message.sql ? <SqlPanel sql={message.sql} compact title="生成 SQL" /> : null}

                    {message.rows ? (
                      <div className="sub-panel overflow-hidden bg-white">
                        <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
                          <Table2 className="h-4 w-4 text-cyan-600" /> 简要结果表
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full min-w-[640px] text-sm">
                            <thead className="bg-slate-50 text-left text-xs text-slate-500">
                              <tr>
                                {getResultColumns(message.rows).map((column) => (
                                  <th
                                    key={column}
                                    className={[
                                      'px-4 py-3',
                                      message.rows?.some((row) => isNumericLike(row[column])) ? 'text-right' : '',
                                    ].join(' ')}
                                  >
                                    {formatColumnLabel(column)}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {message.rows.map((row, rowIndex) => (
                                <tr key={`${rowIndex}-${JSON.stringify(row).slice(0, 40)}`} className="border-t border-slate-100">
                                  {getResultColumns(message.rows ?? []).map((column) => {
                                    const value = row[column];
                                    const numeric = isNumericLike(value);
                                    return (
                                      <td
                                        key={column}
                                        className={[
                                          'px-4 py-3 text-slate-700',
                                          numeric ? 'text-right font-mono' : '',
                                        ].join(' ')}
                                      >
                                        {formatCellValue(column, value)}
                                      </td>
                                    );
                                  })}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ) : null}
                  </div>
                )}
              </article>
            ))}
          </div>

          <div className="border-t border-slate-200 p-4">
            <div className="flex items-end gap-3">
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                className="control min-h-20 flex-1 resize-none text-base"
                placeholder="输入你的问题，比如：最近 30 天销售额按天变化如何？"
              />
              <button onClick={run} disabled={mutation.isPending} className="primary-btn h-12 px-5">
                {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />} 发送
              </button>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
