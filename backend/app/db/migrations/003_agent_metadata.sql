CREATE TABLE IF NOT EXISTS metric_definitions (
  id UUID PRIMARY KEY,
  metric_name TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  description TEXT NOT NULL,
  formula TEXT NOT NULL,
  required_tables TEXT[] NOT NULL DEFAULT '{}',
  required_fields TEXT[] NOT NULL DEFAULT '{}',
  default_filters JSONB NOT NULL DEFAULT '{}'::jsonb,
  example_question TEXT NOT NULL DEFAULT '',
  owner TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'enabled',
  embedding vector(1536),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_metric_definitions_status
ON metric_definitions (status);

CREATE INDEX IF NOT EXISTS idx_metric_definitions_embedding
ON metric_definitions
USING hnsw (embedding vector_cosine_ops);
