-- Дополнительные индексы для аналитических запросов УСУДТ.
-- Выполняется после создания существующих таблиц приложения.
-- Команды идемпотентны и не удаляют накопленные данные.
CREATE INDEX IF NOT EXISTS ix_measurements_signal_time
    ON measurements (signal_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS ix_decisions_signal_time
    ON decisions (signal_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_incidents_signal_time
    ON incidents (signal_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS ix_forecasts_signal_horizon
    ON forecasts (signal_id, horizon_min, calculated_at DESC);
CREATE INDEX IF NOT EXISTS ix_appeals_signal_period
    ON appeals (signal_id, period_start, period_end);
