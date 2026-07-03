import { Play, RotateCcw, TableProperties } from 'lucide-react';

type QuestionInputProps = {
  value: string;
  onChange: (value: string) => void;
  onRun: () => void;
  running: boolean;
};

export function QuestionInput({ value, onChange, onRun, running }: QuestionInputProps) {
  return (
    <section className="panel p-5">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-slate-950">数据问答</h3>
        <p className="text-sm text-slate-500">用自然语言查询本地 PostgreSQL 数据库</p>
      </div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="例如「最近 30 天销售额按天变化如何？」"
        className="control min-h-32 w-full resize-none text-base shadow-[0_0_0_1px_rgba(34,211,238,0.03)] focus:shadow-[0_0_0_4px_rgba(34,211,238,0.18)]"
      />
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button className="primary-btn" onClick={onRun} disabled={running}>
          <Play className="h-4 w-4" /> {running ? '分析中' : '运行分析'}
        </button>
        <button className="secondary-btn" onClick={() => onChange('')}>
          <RotateCcw className="h-4 w-4" /> 清空
        </button>
        <button className="secondary-btn">
          <TableProperties className="h-4 w-4" /> 查看数据结构
        </button>
      </div>
    </section>
  );
}
