# Модель данных УСУДТ

## Логическая модель

Справочники: светофорный объект, источник данных, программа регулирования.
Оперативные сущности: измерение, оценка транспортной модели, прогноз,
решение инженера, событие, обращение.

```mermaid
erDiagram
    SIGNAL ||--o{ MEASUREMENT : "измерения"
    SOURCE ||--o{ MEASUREMENT : "передает"
    SIGNAL ||--o{ PROGRAM : "допустимые режимы"
    PROGRAM ||--o{ MODEL_ESTIMATE : "варианты сценариев"
    SIGNAL ||--o{ FORECAST : "прогнозы"
    SIGNAL ||--o{ DECISION : "решения"
    PROGRAM ||--o{ DECISION : "выбрана в"
    SIGNAL ||--o{ INCIDENT : "события"
    SIGNAL ||--o{ APPEAL : "обращения"
```

## Физическая модель PostgreSQL

```mermaid
erDiagram
    signals {
      integer id PK
      varchar code UK
      varchar name
    }
    sources {
      integer id PK
      varchar code UK
      varchar name
    }
    measurements {
      integer id PK
      integer signal_id FK
      integer source_id FK
      varchar external_id
      timestamptz observed_at
      timestamptz received_at
      integer vehicle_count
      integer period_seconds
      double_precision occupancy
      double_precision speed_kmh
    }
    programs {
      integer id PK
      integer signal_id FK
      varchar code
      varchar name
      boolean approved
      boolean current
    }
    model_estimates {
      integer id PK
      integer program_id FK
      varchar scenario
      double_precision cars_delay
      double_precision buses_delay
      double_precision trolley_delay
      double_precision tram_delay
      integer buses_count
      integer trolley_count
      integer tram_count
    }
    forecasts {
      integer id PK
      integer signal_id FK
      timestamptz calculated_at
      integer horizon_min
      double_precision intensity_per_hour
      varchar method
    }
    decisions {
      integer id PK
      integer signal_id FK
      integer program_id FK
      varchar engineer
      text reason
      varchar status
      timestamptz created_at
      timestamptz confirmed_at
    }
    incidents {
      integer id PK
      integer signal_id FK
      varchar category
      text description
      varchar status
      timestamptz occurred_at
    }
    appeals {
      integer id PK
      integer signal_id FK
      varchar registry_code UK
      text summary
      timestamptz period_start
      timestamptz period_end
      varchar status
    }
    signals ||--o{ measurements : "signal_id"
    sources ||--o{ measurements : "source_id"
    signals ||--o{ programs : "signal_id"
    programs ||--o{ model_estimates : "program_id"
    signals ||--o{ forecasts : "signal_id"
    signals ||--o{ decisions : "signal_id"
    programs ||--o{ decisions : "program_id"
    signals ||--o{ incidents : "signal_id"
    signals ||--o{ appeals : "signal_id"
```

Обозначения FK означают внешние ключи, PK первичные ключи, UK уникальные значения.
При поступлении одного идентификатора сообщения от одного источника повторная запись
не создаётся благодаря ограничению `uq_source_message`. Код программы уникален
в пределах конкретного СО. Контактные данные заявителей не хранятся.

Справочники СО и источников вынесены в отдельные таблицы, оценки по сценариям
отделены от программ. В `decisions` поле `signal_id` хранится наряду с `program_id`
для выборки по объекту. При создании решения проверяется соответствие этих ссылок,
поэтому строгая третья нормальная форма всей физической схемы не заявляется.

Составные ограничения уникальности: `(source_id, external_id)`, `(signal_id, code)`,
`(program_id, scenario)`. Первичные и внешние ключи имеют тип INTEGER.
Поля обязательны, кроме `measurements.speed_kmh` и `decisions.confirmed_at`.
Значения `default` в ORM задаются приложением при вставке.
