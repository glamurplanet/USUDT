from datetime import datetime, timezone, timedelta
from statistics import mean
from fastapi import HTTPException


def completeness_and_freshness(measurements, now=None):
    """15 минут: пропущенные минутные интервалы, возраст последней записи."""
    now = now or datetime.now(timezone.utc)
    if not measurements:
        return False, 'Нет измерений за последние 15 минут'
    timestamps = [m.observed_at.replace(tzinfo=timezone.utc) if m.observed_at.tzinfo is None else m.observed_at.astimezone(timezone.utc) for m in measurements]
    if (now - max(timestamps)).total_seconds() > 120:
        return False, 'Данные старше двух минут'
    slots = {t.replace(second=0,microsecond=0) for t in timestamps if now-t <= timedelta(minutes=15)}
    # 15 ожидаемых минутных интервалов: меньше 12 означает пропуски > 20%.
    if len(slots) < 12:
        return False, 'Пропуски измерений превышают 20% за 15 минут'
    return True, 'Данные актуальны'


def predict_intensity(measurements):
    """Среднее последних 5 значений, выраженных в ТС/ч. Это базовая модель."""
    sorted_items = sorted(measurements, key=lambda m: m.observed_at)
    if not sorted_items:
        raise ValueError('Недостаточно измерений')
    recent = sorted_items[-5:]
    intensities = [m.vehicle_count*3600/m.period_seconds for m in recent]
    baseline = intensities[-1]
    prediction = mean(intensities)
    return {'method':'moving_average_5', 'intensity_per_hour':round(prediction,1), 'last_value_baseline':round(baseline,1)}


def weighted_delay(cars_delay, buses_delay, trolley_delay, tram_delay, buses_count, trolley_count, tram_count, car_weight=0.7):
    if not 0 <= car_weight <= 1:
        raise ValueError('Вес легкового транспорта должен быть от 0 до 1')
    n = buses_count+trolley_count+tram_count
    if n <= 0:
        raise ValueError('Нет оценок числа единиц общественного транспорта')
    public = (buses_delay*buses_count+trolley_delay*trolley_count+tram_delay*tram_count)/n
    return round(car_weight*cars_delay+(1-car_weight)*public,2),round(public,2)
