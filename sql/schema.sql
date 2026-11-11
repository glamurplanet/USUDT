-- Воспроизводимая схема создаётся автоматически SQLAlchemy из app/models.py.
-- Этот файл содержит пример ручной проверки после создания таблиц:
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE'
ORDER BY table_name;
-- Для генерации структуры выполните: python -m app.init_db
