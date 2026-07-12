CREATE TABLE IF NOT EXISTS conversation_states (
  id UUID PRIMARY KEY,
  owner_id UUID REFERENCES app_users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active', 'waiting_for_clarification', 'cancelled')),
  state JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_conversation_states_owner_updated
ON conversation_states (owner_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversation_states_expires_at
ON conversation_states (expires_at);
