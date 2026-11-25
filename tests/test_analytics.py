from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pytest

from app.analytics import (
    hourly_intensity, queue_remainder, mean_absolute_error,
    horizon_forecasts, compare_periods,
)


def test_hourly_intensity():
    assert hourly_intensity(20, 60)==1200
    with pytest.raises(ValueError):hourly_intensity(20,0)


def test_queue_remainder():
    assert queue_remainder(5,12,20)==0
    assert queue_remainder(5,12,8)==9
    with pytest.raises(ValueError):queue_remainder(5,12,None)


def test_mae():
    assert mean_absolute_error([10,20],[12,18])==2


def test_unverified_horizons_not_fabricated():
    base=datetime(2026,1,1,tzinfo=timezone.utc)
    rows=[SimpleNamespace(observed_at=base+timedelta(minutes=i),vehicle_count=10+i,period_seconds=60) for i in range(6)]
    result=horizon_forecasts(rows)
    assert set(result)=={5,10,15}
    assert result[15]["validation_pairs"]==0
    assert result[15]["method"]=="moving_average_5_unverified"


def test_validation_per_horizon():
    base=datetime(2026,1,1,tzinfo=timezone.utc)
    rows=[SimpleNamespace(observed_at=base+timedelta(minutes=i),vehicle_count=10+i,period_seconds=60) for i in range(50)]
    result=horizon_forecasts(rows)
    assert result[5]["validation_pairs"]>result[15]["validation_pairs"]>0
    assert result[5]["mae_last"] is not None


def test_period_comparison():
    assert compare_periods([100]*5,[110]*5,"dry","dry")["available"]
    assert not compare_periods([100]*5,[150]*5,"dry","dry")["available"]
    assert not compare_periods([100]*5,[100]*5,"dry","rain")["available"]
