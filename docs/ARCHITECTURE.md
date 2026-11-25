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

## Объектная модель

Диаграмма показывает классы ORM с ключевыми атрибутами и ассоциациями по внешним ключам. Все классы наследуются от `Base` SQLAlchemy.

```mermaid
classDiagram
    class Signal {
        id
        code
        name
    }
    class Source {
        id
        code
        name
    }
    class Measurement {
        signal_id
        source_id
        observed_at
        vehicle_count
    }
    class Program {
        signal_id
        code
        approved
    }
    class ModelEstimate {
        program_id
        scenario
        cars_delay
    }
    class Forecast {
        signal_id
        horizon_min
        intensity_per_hour
    }
    class Decision {
        signal_id
        program_id
        engineer
        status
    }
    class Incident {
        signal_id
        category
        status
    }
    class Appeal {
        signal_id
        registry_code
        status
    }
    Signal "1" -- "0..*" Measurement
    Source "1" -- "0..*" Measurement
    Signal "1" -- "0..*" Program
    Program "1" -- "0..*" ModelEstimate
    Signal "1" -- "0..*" Forecast
    Signal "1" -- "0..*" Decision
    Program "1" -- "0..*" Decision
    Signal "1" -- "0..*" Incident
    Signal "1" -- "0..*" Appeal
```

Диаграмма не подразумевает наличие ORM-свойств `relationship`: ассоциации реализованы через поля FK.

Типичные запросы: последние измерения для выбранного СО по `signal_id`
и `observed_at`; утверждённые программы по `signal_id` и `approved`;
оценка задержек по `program_id` и `scenario`; агрегирование количества
обращений и событий по объектам. Индексы для частых временных выборок
описаны в `sql/lab5_indexes.sql`.

УСУДТ не соединяется напрямую с контроллерами. Данные от внешних систем
поступают через согласованные файлы или интерфейсы, которые должны быть
разработаны и проверены отдельно.
