import { CheckCircle2, CircleDashed, Loader2 } from 'lucide-react';
import { pipelineSteps } from '../../data/mock';

type AgentPipelineProps = {
  running: boolean;
};

export function AgentPipeline({ running }: AgentPipelineProps) {
  return (
    <section className="panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-950">Agent 执行链路</h3>
          <p className="text-sm text-slate-500">节点逐步激活，仅展示可信执行状态</p>
        </div>
        <span className="rounded-md bg-slate-950 px-3 py-1.5 text-xs font-semibold text-cyan-100">LangGraph</span>
      </div>
      <div className="grid gap-3 md:grid-cols-7">
        {pipelineSteps.map((step, index) => {
          const active = running ? index <= 5 : step.status !== '已跳过';
          const isRunning = running && index === 5;
          return (
            <div key={step.name} className="relative">
              <div
                className={[
                  'min-h-32 border p-3 transition duration-500',
                  active ? 'border-cyan-300 bg-cyan-50/80 shadow-[0_0_22px_rgba(34,211,238,0.18)]' : 'border-slate-200 bg-slate-50',
                ].join(' ')}
                style={{ borderRadius: 8, transitionDelay: `${index * 90}ms` }}
              >
                <div className="mb-3 flex items-center justify-between">
                  {isRunning ? (
                    <Loader2 className="h-5 w-5 animate-spin text-cyan-600" />
                  ) : active ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  ) : (
                    <CircleDashed className="h-5 w-5 text-slate-400" />
                  )}
                  <span className="font-mono text-xs text-slate-500">{step.time}</span>
                </div>
                <p className="font-semibold text-slate-900">{step.name}</p>
                <p className="mt-2 text-xs text-slate-500">{isRunning ? '运行中' : step.status}</p>
              </div>
              {index < pipelineSteps.length - 1 ? (
                <div className="absolute right-[-14px] top-1/2 hidden h-px w-7 bg-cyan-300 md:block" />
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}
