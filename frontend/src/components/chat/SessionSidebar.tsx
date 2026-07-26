import { ArchiveRestore, ChevronDown, Loader2, Plus, Search } from 'lucide-react';
import type { Session } from '../../lib/chat';

type SessionSidebarProps = {
  sessions: Session[];
  activeSession: string | null;
  query: string;
  onQueryChange: (value: string) => void;
  onOpenSession: (sessionId: string) => void;
  onStartNewChat: () => void;
  sessionCursor: string | null;
  loadingMoreSessions: boolean;
  onLoadMoreSessions: () => void;
  canClaimHistory: boolean;
  onClaimHistory: () => void;
};

export function SessionSidebar({
  sessions,
  activeSession,
  query,
  onQueryChange,
  onOpenSession,
  onStartNewChat,
  sessionCursor,
  loadingMoreSessions,
  onLoadMoreSessions,
  canClaimHistory,
  onClaimHistory,
}: SessionSidebarProps) {
  return (
    <aside className="flex w-[280px] shrink-0 flex-col border-r border-stone-200 bg-stone-50/80 max-md:hidden">
      <div className="space-y-3 border-b border-stone-200 p-3">
        <button type="button" onClick={onStartNewChat} className="primary-btn w-full justify-start bg-accent-600 hover:bg-accent-700">
          <Plus className="h-4 w-4" /> 新建对话
        </button>
        <label className="flex items-center gap-2 border border-stone-200 bg-white px-3 py-2 text-stone-500" style={{ borderRadius: 6 }}>
          <Search className="h-4 w-4" />
          <input value={query} onChange={(event) => onQueryChange(event.target.value)} className="min-w-0 flex-1 bg-transparent text-sm text-stone-800 outline-none" placeholder="搜索已加载会话" />
        </label>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        <div className="space-y-1">
          {sessions.map((session) => (
            <button
              key={session.id}
              type="button"
              onClick={() => onOpenSession(session.id)}
              className={[
                'w-full px-3 py-3 text-left transition',
                activeSession === session.id ? 'bg-accent-50 text-accent-900' : 'text-stone-700 hover:bg-white',
              ].join(' ')}
              style={{ borderRadius: 6 }}
            >
              <p className="truncate text-sm font-medium">{session.title}</p>
              <p className="mt-1 text-xs text-stone-500">{session.status === 'waiting_for_clarification' ? '等待补充' : new Date(session.updatedAt).toLocaleString()}</p>
            </button>
          ))}
        </div>
        {sessionCursor && !query ? (
          <button type="button" onClick={onLoadMoreSessions} disabled={loadingMoreSessions} className="secondary-btn mt-3 w-full text-xs">
            {loadingMoreSessions ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronDown className="h-4 w-4" />}
            加载更多会话
          </button>
        ) : null}
        {canClaimHistory ? (
          <button type="button" onClick={onClaimHistory} className="secondary-btn mt-3 w-full text-xs" title="迁移本机匿名历史">
            <ArchiveRestore className="h-4 w-4" /> 迁移本机历史
          </button>
        ) : null}
      </div>
    </aside>
  );
}
