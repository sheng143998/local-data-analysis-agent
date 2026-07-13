CREATE TABLE IF NOT EXISTS semantic_contracts (
  id UUID PRIMARY KEY,
  contract_key TEXT NOT NULL,
  version INTEGER NOT NULL CHECK (version > 0),
  contract_type TEXT NOT NULL CHECK (contract_type IN ('metric', 'dimension', 'entity', 'relationship')),
  display_name TEXT NOT NULL,
  business_definition TEXT NOT NULL,
  source_tables TEXT[] NOT NULL DEFAULT '{}',
  source_fields TEXT[] NOT NULL DEFAULT '{}',
  synonyms TEXT[] NOT NULL DEFAULT '{}',
  default_filters JSONB NOT NULL DEFAULT '{}'::jsonb,
  time_grain TEXT NOT NULL DEFAULT '',
  aggregation TEXT NOT NULL DEFAULT '',
  semantic_config JSONB NOT NULL DEFAULT '{}'::jsonb,
  owner TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('enabled', 'draft', 'disabled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (contract_key, version)
);

-- 业务目的：按当前可用语义契约读取时避免全表扫描，历史版本仍保留以支持口径追溯。
CREATE INDEX IF NOT EXISTS idx_semantic_contracts_key_status_version
ON semantic_contracts (contract_key, status, version DESC);

CREATE INDEX IF NOT EXISTS idx_semantic_contracts_type_status
ON semantic_contracts (contract_type, status);
