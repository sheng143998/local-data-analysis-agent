export type MetricStatus = 'enabled' | 'draft' | 'disabled';

export type MetricDefinition = {
  id: string;
  metric_name: string;
  display_name: string;
  description: string;
  formula: string;
  required_tables: string[];
  required_fields: string[];
  default_filters: Record<string, string>;
  example_question: string;
  owner: string;
  status: MetricStatus;
  created_at: string;
  updated_at: string;
};

export type MetricPayload = Omit<MetricDefinition, 'id' | 'created_at' | 'updated_at'>;
