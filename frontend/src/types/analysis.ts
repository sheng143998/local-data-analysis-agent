export type AnalysisValue = string | number | boolean | null;

export type AnalysisRow = Record<string, AnalysisValue>;

export type AnalysisMetric = {
  label: string;
  value: string;
  delta: string;
  hint: string;
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
};
