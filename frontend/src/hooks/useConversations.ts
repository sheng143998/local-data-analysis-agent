import { useCallback, useEffect, useMemo, useState, type Dispatch, type RefObject, type SetStateAction } from 'react';
import { claimDevelopmentConversations, getConversation, listConversations } from '../api/analysisClient';
import { messageFromHistory, prependUnique, toChatError, type ChatItem, type Session } from '../lib/chat';
import type { ConversationDetail } from '../types/analysis';

type UseConversationsOptions = {
  setMessages: Dispatch<SetStateAction<ChatItem[]>>;
  scrollRef: RefObject<HTMLDivElement | null>;
  scrollToLatest: () => void;
};

/** 会话列表状态：加载 / 分页 / 搜索 / 迁移历史 / 打开会话 / 新建会话。 */
export function useConversations({ setMessages, scrollRef, scrollToLatest }: UseConversationsOptions) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionCursor, setSessionCursor] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [hasMoreMessages, setHasMoreMessages] = useState(false);
  const [nextBefore, setNextBefore] = useState<string | null>(null);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [loadingMoreSessions, setLoadingMoreSessions] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);

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

  const openSession = useCallback(async (sessionId: string) => {
    try {
      const detail: ConversationDetail = await getConversation(sessionId);
      setActiveSession(sessionId);
      setMessages(detail.messages.map(messageFromHistory));
      setHasMoreMessages(detail.has_more);
      setNextBefore(detail.next_before);
      setSessionError(null);
      scrollToLatest();
    } catch (error) {
      // 打开失败时仅展示行内提示，不清空当前已展示的消息。
      setSessionError(toChatError(error).message);
    }
  }, [scrollToLatest, setMessages]);

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
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'assistant', text: friendlyError.message, error: friendlyError }]);
    } finally {
      setLoadingOlder(false);
    }
  }, [activeSession, loadingOlder, nextBefore, scrollRef, setMessages]);

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

  const claimHistory = useCallback(async () => {
    try {
      await claimDevelopmentConversations();
      await refreshSessions();
      setSessionError(null);
    } catch (error) {
      setSessionError(toChatError(error).message);
    }
  }, [refreshSessions]);

  const startNewChat = useCallback(() => {
    setActiveSession(null);
    setMessages([]);
    setHasMoreMessages(false);
    setNextBefore(null);
    setSessionError(null);
  }, [setMessages]);

  const resetPagination = useCallback(() => {
    setHasMoreMessages(false);
    setNextBefore(null);
  }, []);

  const filteredSessions = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    if (!normalized) return sessions;
    return sessions.filter((session) => session.title.toLocaleLowerCase().includes(normalized));
  }, [query, sessions]);

  const activeTitle = useMemo(
    () => sessions.find((session) => session.id === activeSession)?.title ?? '新对话',
    [activeSession, sessions],
  );

  return {
    sessions,
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
    setSessionError,
    refreshSessions,
    openSession,
    loadOlderMessages,
    loadMoreSessions,
    claimHistory,
    startNewChat,
    resetPagination,
  };
}
