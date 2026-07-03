DELETE FROM schema_metadata a
USING schema_metadata b
WHERE a.id > b.id
  AND a.table_name = b.table_name
  AND a.column_name = b.column_name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_schema_metadata_table_column
ON schema_metadata (table_name, column_name);
