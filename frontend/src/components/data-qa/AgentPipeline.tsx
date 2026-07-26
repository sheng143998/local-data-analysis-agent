import { Check } from 'lucide-react';
import type { AgentStep } from '../../types/analysis';

type AgentPipelineProps = {
  running: boolean;
  steps: AgentStep[];
};

/**
 * 分析过程竖向 stepper：
 * 完成项灰绿打勾、当前项主色呼吸点、右侧展示耗时（秒数）。
 * 阶段名由后端下发，保持业务语言（理解问题 / 检索口径 / 生成查询…）。
 */
export function AgentPipeline({ running, steps }: AgentPipelineProps) {
  if (!steps.length) return null;

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-4 shadow-soft">
      <p className="mb-3 text-sm font-semibold text-stone-800">分析过程</p>
      <ol className="space-y-0">
        {steps.map((step, index) => {
          const isCurrent = running && step.status === '运行中';
          const isDone = step.status === '已完成' || (!running && step.status === '运行中');
          const isSkipped = step.status === '已跳过';
          const isLast = index === steps.length - 1;
          return (
            <li key={`${step.name}-${index}`} className="relative flex gap-3 pb-0">
              {/* 连接线 */}
              {!isLast ? (
                <span className="absolute left-[11px] top-6 h-[calc(100%-14px)] w-px bg-stone-200" aria-hidden="true" />
              ) : null}
              <span className="relative z-[1] mt-0.5 grid h-[22px] w-[22px] shrink-0 place-items-center">
                {isCurrent ? (
                  <span className="step-dot-current" />
                ) : isDone ? (
                  <span className="grid h-[22px] w-[22px] place-items-center rounded-full bg-success-soft">
                    <Check className="h-3.5 w-3.5 text-success" strokeWidth={3} />
                  </span>
                ) : (
                  <span className="h-2 w-2 rounded-full bg-stone-300" />
                )}
              </span>
              <div className={['flex min-w-0 flex-1 items-baseline justify-between gap-3', isLast ? '' : 'pb-4'].join(' ')}>
                <p
                  className={[
                    'truncate text-sm',
                    isCurrent ? 'font-semibold text-accent-700' : isSkipped ? 'text-stone-400' : 'text-stone-700',
                  ].join(' ')}
                >
                  {step.name}
                  {isSkipped ? <span className="ml-2 text-xs text-stone-400">未涉及</span> : null}
                </p>
                <span className="nums shrink-0 text-xs text-stone-400">{isSkipped ? '' : step.time}</span>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
