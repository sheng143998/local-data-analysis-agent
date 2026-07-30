-- 017: 记忆生命周期与热点索引（第二轮优化 1a / 4a）

-- sql_memories 去重（保留最新一条），为唯一索引与 ON CONFLICT 铺路
DELETE FROM sql_memories a
USING sql_memories b
WHERE a.normalized_question = b.normalized_question
  AND a.created_at < b.created_at;

CREATE UNIQUE INDEX IF NOT EXISTS uq_sql_memories_normalized_question
  ON sql_memories (normalized_question);

-- 热点查询路径索引
CREATE INDEX IF NOT EXISTS idx_tool_calls_query_run
  ON tool_calls (query_run_id, created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_states_owner_updated
  ON conversation_states (owner_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_runs_created_at
  ON query_runs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sql_memories_last_used
  ON sql_memories (last_used_at DESC NULLS LAST);

-- pgvector ANN 索引：没有它们时每次 <=> 检索都是全表排序
CREATE INDEX IF NOT EXISTS idx_metric_definitions_embedding_hnsw
  ON metric_definitions USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_schema_metadata_embedding_hnsw
  ON schema_metadata USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_sql_memories_question_embedding_hnsw
  ON sql_memories USING hnsw (question_embedding vector_cosine_ops);
