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
      bigint id PK
      varchar code UK
      varchar name
    }
    sources {
      bigint id PK
      varchar code UK
      varchar name
    }
    measurements {
      bigint id PK
      bigint signal_id FK
      bigint source_id FK
      varchar external_id
      timestamptz observed_at
      integer vehicle_count
      integer period_seconds
      double_precision occupancy
      double_precision speed_kmh
    }
    programs {
      bigint id PK
      bigint signal_id FK
      varchar code
      varchar name
      boolean approved
      boolean current
    }
    model_estimates {
      bigint id PK
      bigint program_id FK
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
      bigint id PK
      bigint signal_id FK
      timestamptz calculated_at
      integer horizon_min
      double_precision intensity_per_hour
      varchar method
    }
    decisions {
      bigint id PK
      bigint signal_id FK
      bigint program_id FK
      varchar engineer
      text reason
      varchar status
      timestamptz created_at
      timestamptz confirmed_at
    }
    incidents {
      bigint id PK
      bigint signal_id FK
      varchar category
      text description
      varchar status
      timestamptz occurred_at
    }
    appeals {
      bigint id PK
      bigint signal_id FK
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

Структура находится как минимум в третьей нормальной форме: названия СО и источников
не повторяются в измерениях, сведения о программах не дублируются в решениях,
а оценки по сценариям выделены в отдельную таблицу.
