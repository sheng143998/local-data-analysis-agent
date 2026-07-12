CREATE TABLE IF NOT EXISTS memory_subjects (
  id UUID PRIMARY KEY,
  app_user_id UUID NOT NULL UNIQUE REFERENCES app_users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS long_term_memories (
  id UUID PRIMARY KEY,
  subject_id UUID NOT NULL REFERENCES memory_subjects(id) ON DELETE CASCADE,
  memory_key TEXT NOT NULL,
  category TEXT NOT NULL,
  value JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'superseded', 'revoked')),
  version INTEGER NOT NULL DEFAULT 1,
  source_conversation_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_long_term_memories_active_key
ON long_term_memories(subject_id, memory_key) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_long_term_memories_subject_status ON long_term_memories(subject_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS long_term_memory_events (
  id UUID PRIMARY KEY,
  memory_id UUID REFERENCES long_term_memories(id) ON DELETE SET NULL,
  subject_id UUID NOT NULL REFERENCES memory_subjects(id) ON DELETE CASCADE,
  action TEXT NOT NULL CHECK (action IN ('created', 'superseded', 'revoked')),
  reason TEXT NOT NULL DEFAULT '',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_long_term_memory_events_subject ON long_term_memory_events(subject_id, created_at DESC);
