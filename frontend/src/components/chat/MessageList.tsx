import { useVirtualizer } from '@tanstack/react-virtual';
import { ChevronUp, Loader2, Sparkles } from 'lucide-react';
import type { RefObject } from 'react';
import { AgentPipeline } from '../data-qa/AgentPipeline';
import { MessageBubble } from './MessageBubble';
import type { ChatItem } from '../../lib/chat';
import type { StreamProgress } from '../../hooks/useChatStream';

const starterQuestions = [
  '当前订单总数是多少？',
  '2017 年订单金额是多少？',
  '销售额最高的前 5 个品类是什么？',
];

type MessageListProps = {
  messages: ChatItem[];
  scrollRef: RefObject<HTMLDivElement | null>;
  hasMoreMessages: boolean;
  loadingOlder: boolean;
  onLoadOlder: () => void;
  isStreaming: boolean;
  progress: StreamProgress | null;
  elapsedSeconds: number;
  onPickStarter: (question: string) => void;
};

function StreamingPlaceholder({ progress, elapsedSeconds }: { progress: StreamProgress; elapsedSeconds: number }) {
  return (
    <div className="px-4 py-4 md:px-8">
      <div className="mx-auto flex max-w-5xl gap-3">
        <div className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-accent text-white">
          <Sparkles className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1 space-y-4">
          <div className="flex items-center gap-2 text-sm text-stone-500">
            <span className="step-dot-current" />
            <span>{progress.stageText}</span>
            <span className="nums text-xs text-stone-400">已耗时 {elapsedSeconds}s</span>
          </div>
          <AgentPipeline running steps={progress.steps} />
          {/* 图表与表格的骨架占位 */}
          <div className="space-y-3">
            <div className="h-48 animate-pulse rounded-2xl border border-stone-200 bg-stone-100" />
            <div className="space-y-2 rounded-2xl border border-stone-200 bg-white p-4 shadow-soft">
              <div className="h-4 w-1/3 animate-pulse rounded bg-stone-100" />
              <div className="h-4 animate-pulse rounded bg-stone-100" />
              <div className="h-4 animate-pulse rounded bg-stone-100" />
              <div className="h-4 w-2/3 animate-pulse rounded bg-stone-100" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function MessageList({
  messages,
  scrollRef,
  hasMoreMessages,
  loadingOlder,
  onLoadOlder,
  isStreaming,
  progress,
  elapsedSeconds,
  onPickStarter,
}: MessageListProps) {
  const messageVirtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 190,
    overscan: 6,
  });

  return (
    <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto scroll-smooth">
      {hasMoreMessages ? (
        <div className="flex justify-center border-b border-stone-100 py-3">
          <button type="button" onClick={onLoadOlder} disabled={loadingOlder} className="secondary-btn px-3 text-xs">
            {loadingOlder ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronUp className="h-4 w-4" />}
            加载更早消息
          </button>
        </div>
      ) : null}

      {messages.length || isStreaming ? (
        <>
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
                  <MessageBubble message={message} />
                </article>
              );
            })}
          </div>
          {isStreaming && progress ? <StreamingPlaceholder progress={progress} elapsedSeconds={elapsedSeconds} /> : null}
        </>
      ) : (
        <div className="mx-auto flex h-full max-w-2xl flex-col justify-center px-6 pb-24">
          <div className="flex items-center gap-3 text-stone-900">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-accent text-white"><Sparkles className="h-5 w-5" /></div>
            <h1 className="text-xl font-semibold">今天想分析什么？</h1>
          </div>
          <div className="mt-7 grid gap-2 sm:grid-cols-2">
            {starterQuestions.map((question) => (
              <button
                key={question}
                type="button"
                onClick={() => onPickStarter(question)}
                className="rounded-xl border border-stone-200 bg-white px-4 py-3 text-left text-sm text-stone-700 transition duration-150 ease-swift hover:border-accent-200 hover:bg-accent-50"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
