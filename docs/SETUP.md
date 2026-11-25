# Развёртывание УСУДТ

Основные требования: Python 3.11+, PostgreSQL 16 и рабочая станция с браузером.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose up -d db
python -m app.init_db
uvicorn app.main:app --reload
```

Откройте `http://127.0.0.1:8000/docs`. Перед запуском проверьте параметры `DATABASE_URL` в собственном файле `.env`. Файл `.env` нельзя публиковать.

Для создания аналитических индексов выполните из `psql`:
`psql -h localhost -U usudt -d usudt -f sql/lab5_indexes.sql`.

Проверка: `pytest -q`. Проверка приложений из `tests/conftest.py` выполняется в отдельной временной базе SQLite. В GitHub Actions предварительно создаются таблицы PostgreSQL.

Функция изменения светофорной программы не отправляет команды контроллерам: пакет передаётся инженеру для самостоятельного ввода через штатную АСУДД.
