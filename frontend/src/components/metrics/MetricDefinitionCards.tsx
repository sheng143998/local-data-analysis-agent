import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Edit3, Loader2, Plus, Search, Trash2, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import { createMetric, deleteMetric, listMetrics, updateMetric } from '../../api/metricClient';
import type { MetricDefinition, MetricPayload, MetricStatus } from '../../types/metric';

type MetricForm = {
  id?: string;
  metric_name: string;
  display_name: string;
  description: string;
  formula: string;
  required_tables: string;
  required_fields: string;
  example_question: string;
  owner: string;
  status: MetricStatus;
};

const emptyMetric: MetricForm = {
  metric_name: '',
  display_name: '',
  description: '',
  formula: '',
  required_tables: '',
  required_fields: '',
  example_question: '',
  owner: '经营分析组',
  status: 'enabled',
};

const statusLabel: Record<MetricStatus, string> = {
  enabled: '启用',
  draft: '草稿',
  disabled: '停用',
};

function toForm(metric: MetricDefinition): MetricForm {
  return {
    id: metric.id,
    metric_name: metric.metric_name,
    display_name: metric.display_name,
    description: metric.description,
    formula: metric.formula,
    required_tables: metric.required_tables.join(', '),
    required_fields: metric.required_fields.join(', '),
    example_question: metric.example_question,
    owner: metric.owner,
    status: metric.status,
  };
}

function toPayload(form: MetricForm): MetricPayload {
  return {
    metric_name: form.metric_name,
    display_name: form.display_name,
    description: form.description,
    formula: form.formula,
    required_tables: splitList(form.required_tables),
    required_fields: splitList(form.required_fields),
    default_filters: {},
    example_question: form.example_question,
    owner: form.owner,
    status: form.status,
  };
}

function splitList(value: string): string[] {
  return value.split(',').map((item) => item.trim()).filter(Boolean);
}

export function MetricDefinitionCards() {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const [editing, setEditing] = useState<MetricForm | null>(null);
  const [mode, setMode] = useState<'create' | 'edit' | null>(null);

  const metricsQuery = useQuery({ queryKey: ['metrics'], queryFn: listMetrics });

  const createMutation = useMutation({
    mutationFn: createMetric,
    onSuccess: (metric) => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      setSelectedId(metric.id);
      closeEditor();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: MetricPayload }) => updateMetric(id, payload),
    onSuccess: (metric) => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      setSelectedId(metric.id);
      closeEditor();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteMetric,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
    },
  });

  const metrics = metricsQuery.data ?? [];
  const rows = useMemo(
    () =>
      metrics.filter((item) =>
        [
          item.display_name,
          item.metric_name,
          item.description,
          item.formula,
          item.required_tables.join(','),
          item.required_fields.join(','),
          item.example_question,
        ]
          .join('')
          .includes(query),
      ),
    [metrics, query],
  );

  const selected = metrics.find((item) => item.id === selectedId) ?? rows[0];

  const openCreate = () => {
    setMode('create');
    setEditing({ ...emptyMetric });
  };

  const openEdit = (metric: MetricDefinition) => {
    setMode('edit');
    setEditing(toForm(metric));
  };

  const closeEditor = () => {
    setEditing(null);
    setMode(null);
  };

  const saveMetric = () => {
    if (!editing || !editing.metric_name.trim() || !editing.display_name.trim()) return;
    const payload = toPayload(editing);
    if (mode === 'create') {
      createMutation.mutate(payload);
    } else if (editing.id) {
      updateMutation.mutate({ id: editing.id, payload });
    }
  };

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <section className="grid gap-5 xl:grid-cols-[1fr_380px]">
      <div>
        <div className="mb-4 flex flex-wrap gap-3">
          <div className="flex min-w-72 flex-1 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2">
            <Search className="h-4 w-4 text-slate-400" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} className="w-full outline-none" placeholder="搜索指标" />
          </div>
          <button className="primary-btn" onClick={openCreate}>
            <Plus className="h-4 w-4" /> 新建指标
          </button>
        </div>

        {metricsQuery.isLoading ? (
          <div className="panel flex h-56 items-center justify-center gap-2 text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" /> 正在加载指标
          </div>
        ) : metricsQuery.isError ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            指标 API 暂不可用，请先启动后端：`npm run backend:dev`
          </div>
        ) : (
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
                    <h3 className="text-lg font-bold text-slate-950">{metric.display_name}</h3>
                    <p className="mt-2 text-sm text-slate-600">{metric.description}</p>
                  </div>
                  <span className={metric.status === 'enabled' ? 'rounded bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700' : 'rounded bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700'}>
                    {statusLabel[metric.status]}
                  </span>
                </div>
                <div className="mt-4 space-y-2 text-xs text-slate-500">
                  <p><span className="font-semibold text-slate-700">计算公式：</span>{metric.formula}</p>
                  <p><span className="font-semibold text-slate-700">依赖数据表：</span>{metric.required_tables.join(', ')}</p>
                  <p><span className="font-semibold text-slate-700">依赖字段：</span>{metric.required_fields.join(', ')}</p>
                  <p><span className="font-semibold text-slate-700">示例问题：</span>{metric.example_question}</p>
                </div>
                <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                  <span className="text-xs text-slate-500">负责人：{metric.owner}</span>
                  <div className="flex gap-2">
                    <button className="grid h-8 w-8 place-items-center rounded-md border border-slate-200 text-slate-600 hover:border-cyan-300 hover:text-cyan-700" onClick={(event) => { event.stopPropagation(); openEdit(metric); }} title="编辑">
                      <Edit3 className="h-4 w-4" />
                    </button>
                    <button className="grid h-8 w-8 place-items-center rounded-md border border-slate-200 text-slate-600 hover:border-rose-300 hover:text-rose-600" onClick={(event) => { event.stopPropagation(); deleteMutation.mutate(metric.id); }} title="删除">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      <aside className="panel h-fit p-5">
        <h3 className="text-lg font-bold text-slate-950">指标详情</h3>
        {selected ? (
          <div className="mt-4 space-y-4 text-sm">
            <div>
              <p className="text-slate-500">指标名称</p>
              <p className="mt-1 font-semibold text-slate-950">{selected.display_name}</p>
            </div>
            <div>
              <p className="text-slate-500">业务定义</p>
              <p className="mt-1 leading-6 text-slate-700">{selected.description}</p>
            </div>
            <div>
              <p className="text-slate-500">计算公式</p>
              <p className="mt-1 rounded-md bg-slate-950 p-3 font-mono text-xs text-cyan-100">{selected.formula}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="sub-panel p-3">
                <p className="text-xs text-slate-500">依赖表</p>
                <p className="mt-1 font-medium text-slate-800">{selected.required_tables.join(', ')}</p>
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
              <button className="grid h-8 w-8 place-items-center rounded-md border border-slate-200" onClick={closeEditor}>
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <MetricInput label="指标编码" value={editing.metric_name} onChange={(value) => setEditing({ ...editing, metric_name: value })} />
              <MetricInput label="指标名称" value={editing.display_name} onChange={(value) => setEditing({ ...editing, display_name: value })} />
              <MetricInput label="负责人" value={editing.owner} onChange={(value) => setEditing({ ...editing, owner: value })} />
              <label className="text-sm text-slate-600">
                状态
                <select className="control mt-2 w-full" value={editing.status} onChange={(event) => setEditing({ ...editing, status: event.target.value as MetricStatus })}>
                  <option value="enabled">启用</option>
                  <option value="draft">草稿</option>
                  <option value="disabled">停用</option>
                </select>
              </label>
              <MetricInput label="业务定义" value={editing.description} onChange={(value) => setEditing({ ...editing, description: value })} wide />
              <MetricInput label="计算公式" value={editing.formula} onChange={(value) => setEditing({ ...editing, formula: value })} wide />
              <MetricInput label="依赖数据表" value={editing.required_tables} onChange={(value) => setEditing({ ...editing, required_tables: value })} />
              <MetricInput label="依赖字段" value={editing.required_fields} onChange={(value) => setEditing({ ...editing, required_fields: value })} />
              <MetricInput label="示例问题" value={editing.example_question} onChange={(value) => setEditing({ ...editing, example_question: value })} wide />
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button className="secondary-btn" onClick={closeEditor}>取消</button>
              <button className="primary-btn" onClick={saveMetric} disabled={isSaving}>
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : null} 保存指标
              </button>
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
