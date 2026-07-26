import { useCallback, useEffect, useRef, useState, type Dispatch, type SetStateAction } from 'react';
import { streamAnalyzeQuestion } from '../api/analysisClient';
import { toChatError, type ChatItem } from '../lib/chat';
import type { AgentStep } from '../types/analysis';

export type StreamProgress = {
  question: string;
  stageText: string;
  steps: AgentStep[];
  startedAt: number;
};

type UseChatStreamOptions = {
  activeSession: string | null;
  setActiveSession: (id: string) => void;
  setMessages: Dispatch<SetStateAction<ChatItem[]>>;
  resetPagination: () => void;
  onSettled: () => void;
  scrollToLatest: () => void;
};

/**
 * SSE 生命周期：发起 / 取消 / 阶段事件 / 流式占位状态。
 * 阶段进度保存在独立的 progress 状态里，阶段刷新不会遍历整个 messages 数组；
 * 只有最终结果（或错误）才会合并进 messages。
 */
export function useChatStream({
  activeSession,
  setActiveSession,
  setMessages,
  resetPagination,
  onSettled,
  scrollToLatest,
}: UseChatStreamOptions) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [progress, setProgress] = useState<StreamProgress | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const streamAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!isStreaming || !progress) return;
    const startedAt = progress.startedAt;
    setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    const timer = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [isStreaming, progress]);

  const run = useCallback(async (rawQuestion: string) => {
    const question = rawQuestion.trim();
    if (!question || isStreaming) return;
    const controller = new AbortController();
    const conversationId = activeSession;
    streamAbortRef.current = controller;
    setIsStreaming(true);
    const startedAt = Date.now();
    setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'user', text: question }]);
    setProgress({ question, stageText: '正在连接分析服务...', steps: [], startedAt });
    scrollToLatest();
    try {
      await streamAnalyzeQuestion(question, conversationId, {
        onStage: (stage) => {
          setProgress((current) => {
            if (!current) return current;
            const finished: AgentStep[] = current.steps.map((step) => (
              step.status === '运行中' ? { ...step, status: '已完成' } : step
            ));
            const elapsed = `${Math.max(0, Math.round((Date.now() - current.startedAt) / 1000))}s`;
            return {
              ...current,
              stageText: `正在${stage.name}...`,
              steps: [...finished, { name: stage.name, status: '运行中', time: elapsed }],
            };
          });
          scrollToLatest();
        },
        onResult: (data) => {
          if (data.conversation_id) setActiveSession(data.conversation_id);
          setMessages((current) => [...current, {
            id: crypto.randomUUID(),
            role: 'assistant',
            text: data.summary,
            sql: data.sql || undefined,
            rows: data.rows,
            visualization: data.visualization,
            metrics: data.metrics,
            steps: data.steps,
          }]);
          resetPagination();
          scrollToLatest();
        },
      }, controller.signal);
    } catch (error) {
      if (!controller.signal.aborted) {
        const friendlyError = toChatError(error);
        setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'assistant', text: friendlyError.message, error: friendlyError }]);
      }
      scrollToLatest();
    } finally {
      if (streamAbortRef.current === controller) streamAbortRef.current = null;
      setIsStreaming(false);
      setProgress(null);
      onSettled();
    }
  }, [activeSession, isStreaming, onSettled, resetPagination, scrollToLatest, setActiveSession, setMessages]);

  const cancelStream = useCallback(() => streamAbortRef.current?.abort(), []);

  return { isStreaming, progress, elapsedSeconds, run, cancelStream };
}
