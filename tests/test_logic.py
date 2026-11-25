from datetime import datetime,timezone,timedelta
from types import SimpleNamespace
from app.logic import predict_intensity,weighted_delay,completeness_and_freshness

def test_forecast_average():
    now=datetime.now(timezone.utc)
    items=[SimpleNamespace(observed_at=now+timedelta(minutes=i),vehicle_count=c,period_seconds=60) for i,c in enumerate([10,20,30,40,50])]
    r=predict_intensity(items)
    assert r['intensity_per_hour']==1800
    assert r['last_value_baseline']==3000

def test_weighted_transport():
    score,public=weighted_delay(10,20,30,40,2,1,1)
    assert public==27.5 and score==15.25

def test_missing_blocks_recommendations():
    now=datetime.now(timezone.utc)
    items=[SimpleNamespace(observed_at=now-timedelta(minutes=i)) for i in range(11)]
    assert completeness_and_freshness(items,now)[0] is False
