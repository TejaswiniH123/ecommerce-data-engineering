
CREATE TABLE IF NOT EXISTS etl_run_log (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    load_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    rows_processed BIGINT NOT NULL DEFAULT 0,
    source_name VARCHAR(255),
    error_message TEXT,

    CONSTRAINT chk_etl_run_status
        CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),

    CONSTRAINT chk_etl_load_type
        CHECK (load_type IN ('FULL_REFRESH', 'INCREMENTAL'))
);

CREATE INDEX IF NOT EXISTS idx_etl_run_log_started_at
    ON etl_run_log (started_at DESC);

CREATE INDEX IF NOT EXISTS idx_etl_run_log_status
    ON etl_run_log (status);
