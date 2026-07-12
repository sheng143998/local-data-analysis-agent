export type AnalysisValue = string | number | boolean | null;

export type AnalysisRow = Record<string, AnalysisValue>;

export type AnalysisMetric = {
  label: string;
  value: string;
  delta: string;
  hint: string;
};

export type AnalysisTrace = {
  toolCalls: number;
  modelCalls: number;
  memoryCandidates: number;
  totalTime: string;
};

export type AgentStep = {
  name: string;
  status: '已完成' | '运行中' | '已跳过';
  time: string;
};

export type AnalysisResponse = {
  question: string;
  path: 'fast_path' | 'rewrite_path' | 'cold_path';
  summary: string;
  sql: string;
  metrics: AnalysisMetric[];
  rows: AnalysisRow[];
  source: {
    dataset: string;
    tables: string[];
    fields: string[];
    metricDefinition: string;
    range: string;
    returnedRows: number;
    queryTime: string;
    security: string;
  };
  trace: AnalysisTrace;
  steps: AgentStep[];
  conversation_id?: string | null;
  pending_clarification: boolean;
  conversation_status: 'active' | 'waiting_for_clarification' | 'cancelled';
};

export type ConversationMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  response?: { summary?: string; failure?: boolean } | null;
};

export type ConversationSummary = {
  id: string;
  title: string;
  updated_at: string;
  status: 'active' | 'waiting_for_clarification' | 'cancelled';
};

export type ConversationDetail = ConversationSummary & { messages: ConversationMessage[] };
