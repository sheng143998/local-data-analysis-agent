import { Edit3, Plus, Search, Trash2, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import { metricDefinitions } from '../../data/mock';

type MetricDefinition = {
  id: string;
  name: string;
  definition: string;
  formula: string;
  tables: string;
  fields: string;
  example: string;
  owner: string;
  status: '启用' | '草稿';
};

const initialMetrics: MetricDefinition[] = metricDefinitions.map(
  ([name, definition, formula, tables, fields, example], index) => ({
    id: `metric-${index + 1}`,
    name,
    definition,
    formula,
    tables,
    fields,
    example,
    owner: index < 4 ? '经营分析组' : '增长分析组',
    status: '启用',
  }),
);

const emptyMetric: MetricDefinition = {
  id: '',
  name: '',
  definition: '',
  formula: '',
  tables: '',
  fields: '',
  example: '',
  owner: '经营分析组',
  status: '启用',
};

export function MetricDefinitionCards() {
  const [query, setQuery] = useState('');
  const [metrics, setMetrics] = useState(initialMetrics);
  const [selectedId, setSelectedId] = useState(initialMetrics[0]?.id ?? '');
  const [editing, setEditing] = useState<MetricDefinition | null>(null);
  const [mode, setMode] = useState<'create' | 'edit' | null>(null);

  const rows = useMemo(
    () =>
      metrics.filter((item) =>
        [item.name, item.definition, item.formula, item.tables, item.fields, item.example].join('').includes(query),
      ),
    [metrics, query],
  );

  const selected = metrics.find((item) => item.id === selectedId) ?? rows[0];

  const openCreate = () => {
    setMode('create');
    setEditing({ ...emptyMetric, id: `metric-${Date.now()}` });
  };

  const openEdit = (metric: MetricDefinition) => {
    setMode('edit');
    setEditing({ ...metric });
  };

  const saveMetric = () => {
    if (!editing || !editing.name.trim()) return;
    if (mode === 'create') {
      setMetrics((current) => [editing, ...current]);
      setSelectedId(editing.id);
    } else {
      setMetrics((current) => current.map((item) => (item.id === editing.id ? editing : item)));
    }
    setEditing(null);
    setMode(null);
  };

  const deleteMetric = (id: string) => {
    setMetrics((current) => current.filter((item) => item.id !== id));
    if (selectedId === id) {
      setSelectedId(metrics.find((item) => item.id !== id)?.id ?? '');
    }
  };

  return (
    <section className="grid gap-5 xl:grid-cols-[1fr_380px]">
      <div>
        <div className="mb-4 flex flex-wrap gap-3">
          <div className="flex min-w-72 flex-1 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2">
            <Search className="h-4 w-4 text-slate-400" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="w-full outline-none"
              placeholder="搜索指标"
            />
          </div>
          <button className="primary-btn" onClick={openCreate}>
            <Plus className="h-4 w-4" /> 新建指标
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          {rows.map((metric) => (
            <article
              key={metric.id}
              className={[
                'panel cursor-pointer p-5 transition hover:-translate-y-0.5',
                selected?.id === metric.id ? 'border-cyan-300 shadow-[0_0_0_3px_rgba(34,211,238,0.12)]' : '',
              ].join(' ')}
              onClick={() => setSelectedId(metric.id)}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-bold text-slate-950">{metric.name}</h3>
                  <p className="mt-2 text-sm text-slate-600">{metric.definition}</p>
                </div>
                <span className={metric.status === '启用' ? 'rounded bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700' : 'rounded bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700'}>
                  {metric.status}
                </span>
              </div>
              <div className="mt-4 space-y-2 text-xs text-slate-500">
                <p><span className="font-semibold text-slate-700">计算公式：</span>{metric.formula}</p>
                <p><span className="font-semibold text-slate-700">依赖数据表：</span>{metric.tables}</p>
                <p><span className="font-semibold text-slate-700">依赖字段：</span>{metric.fields}</p>
                <p><span className="font-semibold text-slate-700">示例问题：</span>{metric.example}</p>
              </div>
              <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                <span className="text-xs text-slate-500">负责人：{metric.owner}</span>
                <div className="flex gap-2">
                  <button
                    className="grid h-8 w-8 place-items-center rounded-md border border-slate-200 text-slate-600 hover:border-cyan-300 hover:text-cyan-700"
                    onClick={(event) => {
                      event.stopPropagation();
                      openEdit(metric);
                    }}
                    title="编辑"
                  >
                    <Edit3 className="h-4 w-4" />
                  </button>
                  <button
                    className="grid h-8 w-8 place-items-center rounded-md border border-slate-200 text-slate-600 hover:border-rose-300 hover:text-rose-600"
                    onClick={(event) => {
                      event.stopPropagation();
                      deleteMetric(metric.id);
                    }}
                    title="删除"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>

      <aside className="panel h-fit p-5">
        <h3 className="text-lg font-bold text-slate-950">指标详情</h3>
        {selected ? (
          <div className="mt-4 space-y-4 text-sm">
            <div>
              <p className="text-slate-500">指标名称</p>
              <p className="mt-1 font-semibold text-slate-950">{selected.name}</p>
            </div>
            <div>
              <p className="text-slate-500">业务定义</p>
              <p className="mt-1 leading-6 text-slate-700">{selected.definition}</p>
            </div>
            <div>
              <p className="text-slate-500">计算公式</p>
              <p className="mt-1 rounded-md bg-slate-950 p-3 font-mono text-xs text-cyan-100">{selected.formula}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="sub-panel p-3">
                <p className="text-xs text-slate-500">依赖表</p>
                <p className="mt-1 font-medium text-slate-800">{selected.tables}</p>
              </div>
              <div className="sub-panel p-3">
                <p className="text-xs text-slate-500">负责人</p>
                <p className="mt-1 font-medium text-slate-800">{selected.owner}</p>
              </div>
            </div>
            <button className="secondary-btn w-full" onClick={() => openEdit(selected)}>
              <Edit3 className="h-4 w-4" /> 编辑这个指标
            </button>
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-500">暂无指标，请新建一个指标口径。</p>
        )}
      </aside>

      {editing ? (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl border border-slate-200 bg-white p-5 shadow-2xl" style={{ borderRadius: 8 }}>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-950">{mode === 'create' ? '新建指标' : '编辑指标'}</h3>
              <button className="grid h-8 w-8 place-items-center rounded-md border border-slate-200" onClick={() => setEditing(null)}>
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <MetricInput label="指标名称" value={editing.name} onChange={(value) => setEditing({ ...editing, name: value })} />
              <MetricInput label="负责人" value={editing.owner} onChange={(value) => setEditing({ ...editing, owner: value })} />
              <MetricInput label="业务定义" value={editing.definition} onChange={(value) => setEditing({ ...editing, definition: value })} wide />
              <MetricInput label="计算公式" value={editing.formula} onChange={(value) => setEditing({ ...editing, formula: value })} wide />
              <MetricInput label="依赖数据表" value={editing.tables} onChange={(value) => setEditing({ ...editing, tables: value })} />
              <MetricInput label="依赖字段" value={editing.fields} onChange={(value) => setEditing({ ...editing, fields: value })} />
              <MetricInput label="示例问题" value={editing.example} onChange={(value) => setEditing({ ...editing, example: value })} wide />
              <label className="text-sm text-slate-600">
                状态
                <select
                  className="control mt-2 w-full"
                  value={editing.status}
                  onChange={(event) => setEditing({ ...editing, status: event.target.value as MetricDefinition['status'] })}
                >
                  <option value="启用">启用</option>
                  <option value="草稿">草稿</option>
                </select>
              </label>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button className="secondary-btn" onClick={() => setEditing(null)}>取消</button>
              <button className="primary-btn" onClick={saveMetric}>保存指标</button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

type MetricInputProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  wide?: boolean;
};

function MetricInput({ label, value, onChange, wide }: MetricInputProps) {
  return (
    <label className={`text-sm text-slate-600 ${wide ? 'md:col-span-2' : ''}`}>
      {label}
      <input className="control mt-2 w-full" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}
