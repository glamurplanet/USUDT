"""Проверяемые расчёты для мониторинга и оценки движения."""
from datetime import timezone
from statistics import mean


def hourly_intensity(vehicle_count: int, period_seconds: int) -> float:
    """Интенсивность, транспортных средств в час."""
    if vehicle_count < 0 or period_seconds <= 0:
        raise ValueError("Недопустимые параметры измерения")
    return vehicle_count * 3600.0 / period_seconds


def queue_remainder(previous: float, arrivals: float, served: float | None) -> float:
    """Остаточная очередь при известных параметрах обслуживания."""
    if served is None:
        raise ValueError("Нет оценки числа обслуженных транспортных средств")
    if min(previous, arrivals, served) < 0:
        raise ValueError("Число транспортных средств не может быть отрицательным")
    return max(0.0, previous + arrivals - served)


def mean_absolute_error(actual: list[float], predicted: list[float]) -> float:
    if not actual or len(actual) != len(predicted):
        raise ValueError("Нужны сопоставимые непустые ряды")
    return mean(abs(a-p) for a,p in zip(actual,predicted))


def utc_minute(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(second=0,microsecond=0)


def horizon_forecasts(measurements, horizons=(5,10,15)):
    """Сравнивает среднее пяти минут и последнее значение по MAE для каждого горизонта.

    Оценка допускается только на точных минутных парах наблюдений. При отсутствии
    контрольных пар используется среднее пяти минут без заявления о проверенной точности.
    """
    points={}
    for sample in measurements:
        slot=utc_minute(sample.observed_at)
        points[slot]=hourly_intensity(sample.vehicle_count,sample.period_seconds)
    slots=sorted(points)
    if len(slots)<5:
        raise ValueError("Для прогноза требуется пять измерений")
    from datetime import timedelta
    newest=slots[-1]
    window=[newest-timedelta(minutes=k) for k in range(4,-1,-1)]
    if any(s not in points for s in window):
        raise ValueError("В последних пяти минутах есть пропуски")
    last_values=[points[s] for s in window]
    average=mean(last_values)
    last=last_values[-1]
    result={}
    for horizon in horizons:
        if horizon not in (5,10,15):
            raise ValueError("Поддерживаются горизонты 5, 10 и 15 минут")
        actual=[]
        avg_preds=[]
        last_preds=[]
        for slot in slots:
            hist=[slot-timedelta(minutes=k) for k in range(4,-1,-1)]
            target=slot+timedelta(minutes=horizon)
            if target in points and all(t in points for t in hist):
                actual.append(points[target])
                avg_preds.append(mean(points[t] for t in hist))
                last_preds.append(points[slot])
        if actual:
            err_avg=mean_absolute_error(actual,avg_preds)
            err_last=mean_absolute_error(actual,last_preds)
            method="moving_average_5" if err_avg<=err_last else "last_observation"
            predicted=average if method=="moving_average_5" else last
        else:
            err_avg=err_last=None
            method="moving_average_5_unverified"
            predicted=average
        result[horizon]={
            "intensity_per_hour": round(predicted,1),
            "method": method,
            "validation_pairs": len(actual),
            "mae_average": round(err_avg,2) if err_avg is not None else None,
            "mae_last": round(err_last,2) if err_last is not None else None,
        }
    return result


def compare_periods(before: list[float], after: list[float], before_conditions: str, after_conditions: str):
    """Сопоставление загрузки допустимо лишь при близких условиях."""
    if before_conditions!=after_conditions:
        return {"available":False,"reason":"Несопоставимые дорожные условия"}
    if len(before)<5 or len(after)<5:
        return {"available":False,"reason":"Недостаточно измерений в одном из периодов"}
    old=mean(before)
    new=mean(after)
    if old==0:
        return {"available":False,"reason":"Нулевая базовая интенсивность"}
    if abs(new-old)/old>0.20:
        return {"available":False,"reason":"Различие загрузки превышает 20%"}
    return {
        "available":True,
        "before_intensity":round(old,2),
        "after_intensity":round(new,2),
        "change_percent":round(100*(new-old)/old,2),
        "note":"Изменение интенсивности не является оценкой задержки без данных транспортной модели"
    }
