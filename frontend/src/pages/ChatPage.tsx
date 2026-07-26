import { useCallback, useRef, useState } from 'react';
import { MessageSquareText, Plus, Send, Square } from 'lucide-react';
import { useAuth } from '../auth/AuthProvider';
import { MessageList } from '../components/chat/MessageList';
import { SessionSidebar } from '../components/chat/SessionSidebar';
import { useChatStream } from '../hooks/useChatStream';
import { useConversations } from '../hooks/useConversations';
import type { ChatItem } from '../lib/chat';

export function ChatPage() {
  const { user } = useAuth();
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState<ChatItem[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToLatest = useCallback(() => {
    window.requestAnimationFrame(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'auto' }));
  }, []);

  const conversations = useConversations({ setMessages, scrollRef, scrollToLatest });
  const {
    filteredSessions,
    sessionCursor,
    activeSession,
    setActiveSession,
    activeTitle,
    query,
    setQuery,
    hasMoreMessages,
    loadingOlder,
    loadingMoreSessions,
    sessionError,
    refreshSessions,
    openSession,
    loadOlderMessages,
    loadMoreSessions,
    claimHistory,
    startNewChat,
    resetPagination,
  } = conversations;

  const onStreamSettled = useCallback(() => { void refreshSessions(); }, [refreshSessions]);

  const { isStreaming, progress, elapsedSeconds, run, cancelStream } = useChatStream({
    activeSession,
    setActiveSession,
    setMessages,
    resetPagination,
    onSettled: onStreamSettled,
    scrollToLatest,
  });

  const submitDraft = () => {
    const question = draft.trim();
    if (!question || isStreaming) return;
    setDraft('');
    void run(question);
  };

  return (
    <div className="mx-auto flex h-[calc(100dvh-108px)] max-w-[1440px] overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-soft md:h-[calc(100dvh-124px)]">
      <SessionSidebar
        sessions={filteredSessions}
        activeSession={activeSession}
        query={query}
        onQueryChange={setQuery}
        onOpenSession={(sessionId) => void openSession(sessionId)}
        onStartNewChat={startNewChat}
        sessionCursor={sessionCursor}
        loadingMoreSessions={loadingMoreSessions}
        onLoadMoreSessions={() => void loadMoreSessions()}
        canClaimHistory={user?.role === 'admin'}
        onClaimHistory={() => void claimHistory()}
      />

      <section className="flex min-h-0 min-w-0 flex-1 flex-col bg-white">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-stone-100 px-4">
          <div className="flex min-w-0 items-center gap-2">
            <MessageSquareText className="h-4 w-4 shrink-0 text-accent" />
            <span className="truncate text-sm font-semibold text-stone-900">{activeTitle}</span>
          </div>
          <button type="button" onClick={startNewChat} className="secondary-btn px-3 text-xs md:hidden" title="新建对话">
            <Plus className="h-4 w-4" /> 新对话
          </button>
        </header>

        {sessionError ? (
          <div className="shrink-0 border-b border-warning/40 bg-warning-soft px-4 py-2 text-sm text-stone-700">
            {sessionError}
          </div>
        ) : null}

        <MessageList
          messages={messages}
          scrollRef={scrollRef}
          hasMoreMessages={hasMoreMessages}
          loadingOlder={loadingOlder}
          onLoadOlder={() => void loadOlderMessages()}
          isStreaming={isStreaming}
          progress={progress}
          elapsedSeconds={elapsedSeconds}
          onPickStarter={setDraft}
        />

        <div className="shrink-0 border-t border-stone-100 bg-white p-3 md:p-4">
          <div className="mx-auto flex max-w-4xl items-end gap-3 rounded-2xl border border-stone-200 bg-white p-2 shadow-soft transition duration-150 focus-within:border-accent-300 focus-within:shadow-[0_0_0_3px_rgba(201,100,66,0.12)]">
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  submitDraft();
                }
              }}
              className="min-h-12 max-h-40 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-6 text-stone-800 outline-none"
              placeholder="输入问题"
            />
            <button type="button" onClick={isStreaming ? cancelStream : submitDraft} disabled={!isStreaming && !draft.trim()} className="primary-btn h-10 w-10 shrink-0 p-0 bg-accent-600 hover:bg-accent-700" title={isStreaming ? '取消分析' : '发送'}>
              {isStreaming ? <Square className="h-4 w-4" /> : <Send className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
