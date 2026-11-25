# Структура программного обеспечения

```mermaid
flowchart BT
  DB[(PostgreSQL)]
  ORM[SQLAlchemy / models.py]
  Q[Запросы и выборки]
  A[analytics.py: прогноз, очередь, MAE]
  API[FastAPI / main.py]
  S[schemas.py: Pydantic]
  WEB[Браузер / Swagger UI]
  EX[АСУДД, ИТС, реестры]
  DB <--> ORM
  ORM <--> Q
  Q --> A
  A --> API
  S --> API
  WEB <--> API
  EX -. согласованные файлы / будущие интерфейсы .-> API
```

Описаны программные классы `Signal`, `Source`, `Measurement`, `Program`,
`ModelEstimate`, `Forecast`, `Decision`, `Incident`, `Appeal`.
Их связи являются отношениями данных через внешние ключи в PostgreSQL,
не иерархией наследования классов.

Типичные запросы: последние измерения для выбранного СО по `signal_id`
и `observed_at`; утверждённые программы по `signal_id` и `approved`;
оценка задержек по `program_id` и `scenario`; агрегирование количества
обращений и событий по объектам. Индексы для частых временных выборок
описаны в `sql/lab5_indexes.sql`.

УСУДТ не соединяется напрямую с контроллерами. Данные от внешних систем
поступают через согласованные файлы или интерфейсы, которые должны быть
разработаны и проверены отдельно.
