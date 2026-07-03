CREATE TABLE IF NOT EXISTS schema_metadata (
  id BIGSERIAL PRIMARY KEY,
  table_name TEXT NOT NULL,
  column_name TEXT NOT NULL,
  data_type TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  business_meaning TEXT NOT NULL DEFAULT '',
  example_values TEXT[] NOT NULL DEFAULT '{}',
  embedding vector(1536),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

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

CREATE TABLE IF NOT EXISTS sql_memories (
  id UUID PRIMARY KEY,
  canonical_question TEXT NOT NULL,
  normalized_question TEXT NOT NULL,
  question_pattern TEXT NOT NULL DEFAULT '',
  question_embedding vector(1536),
  sql_embedding vector(1536),
  intent TEXT NOT NULL DEFAULT '',
  sql_template TEXT NOT NULL,
  final_sql TEXT NOT NULL,
  param_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
  parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
  tables TEXT[] NOT NULL DEFAULT '{}',
  metrics TEXT[] NOT NULL DEFAULT '{}',
  dimensions TEXT[] NOT NULL DEFAULT '{}',
  filters JSONB NOT NULL DEFAULT '{}'::jsonb,
  dialect TEXT NOT NULL DEFAULT 'postgresql',
  schema_version TEXT NOT NULL DEFAULT 'v1',
  success_count INTEGER NOT NULL DEFAULT 0,
  failure_count INTEGER NOT NULL DEFAULT 0,
  avg_latency_ms INTEGER NOT NULL DEFAULT 0,
  last_result_columns TEXT[] NOT NULL DEFAULT '{}',
  last_row_count INTEGER NOT NULL DEFAULT 0,
  last_used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS query_runs (
  id UUID PRIMARY KEY,
  user_question TEXT NOT NULL,
  rewritten_question TEXT,
  memory_hit BOOLEAN NOT NULL DEFAULT false,
  memory_id UUID,
  generated_sql TEXT,
  final_sql TEXT,
  guard_status TEXT NOT NULL DEFAULT 'pending',
  execution_status TEXT NOT NULL DEFAULT 'pending',
  row_count INTEGER NOT NULL DEFAULT 0,
  latency_ms INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tool_calls (
  id UUID PRIMARY KEY,
  query_run_id UUID REFERENCES query_runs(id),
  tool_name TEXT NOT NULL,
  input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL,
  latency_ms INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS embedding_documents (
  id UUID PRIMARY KEY,
  doc_type TEXT NOT NULL,
  doc_key TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  embedding vector(1536),
  embedding_model TEXT NOT NULL DEFAULT 'text-embedding-v4',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_metric_definitions_status ON metric_definitions (status);
CREATE INDEX IF NOT EXISTS idx_sql_memories_question_trgm ON sql_memories USING gin (normalized_question gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_schema_metadata_embedding ON schema_metadata USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_metric_definitions_embedding ON metric_definitions USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_sql_memories_question_embedding ON sql_memories USING hnsw (question_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_sql_memories_sql_embedding ON sql_memories USING hnsw (sql_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_embedding_documents_embedding ON embedding_documents USING hnsw (embedding vector_cosine_ops);
