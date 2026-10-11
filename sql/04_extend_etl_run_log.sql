
ALTER TABLE etl_run_log
    ADD COLUMN IF NOT EXISTS input_rows BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS inserted_rows BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS updated_rows BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS unchanged_rows BIGINT NOT NULL DEFAULT 0;

COMMENT ON COLUMN etl_run_log.input_rows
    IS 'Number of records read from the input batch';

COMMENT ON COLUMN etl_run_log.inserted_rows
    IS 'Number of new records inserted';

COMMENT ON COLUMN etl_run_log.updated_rows
    IS 'Number of existing records updated';

COMMENT ON COLUMN etl_run_log.unchanged_rows
    IS 'Number of records skipped because their values were unchanged';
