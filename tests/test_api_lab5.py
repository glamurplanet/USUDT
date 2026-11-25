from datetime import datetime,timezone,timedelta

def measurement(index,stamp,signal='S01'):
    return {
        'source_code':'I01', 'external_id':f'lab5-{index}',
        'signal_code':signal,'observed_at':stamp.isoformat(),
        'vehicle_count':20,'period_seconds':60,'occupancy':25
    }


def test_queue_requires_known_service_count(client):
    assert client.get('/api/queue/S01',params={'previous':4,'arrivals':10}).status_code==422
    assert client.get('/api/queue/S01',params={'previous':4,'arrivals':10,'served':8}).json()['queue_vehicles']==6


def test_report_distinguishes_incomparable_periods(client):
    t=datetime(2026,10,1,10,tzinfo=timezone.utc)
    for i in range(5):
        assert client.post('/api/measurements',json=measurement(i,t+timedelta(minutes=i))).status_code==200
        assert client.post('/api/measurements',json=measurement(i+5,t+timedelta(hours=1,minutes=i))).status_code==200
    params={
        'before_start':t.isoformat(), 'before_end':(t+timedelta(minutes=5)).isoformat(),
        'after_start':(t+timedelta(hours=1)).isoformat(),
        'after_end':(t+timedelta(hours=1,minutes=5)).isoformat(),
        'before_conditions':'dry','after_conditions':'rain'
    }
    assert client.get('/api/report/periods/S01',params=params).json()['available'] is False
    params['after_conditions']='dry'
    assert client.get('/api/report/periods/S01',params=params).json()['available'] is True


def test_status_change_validation(client):
    item=client.post('/api/incidents',json={'signal_code':'S01','category':'ДТП','description':'Перекрытие полосы'}).json()
    ident=item['id']
    assert client.patch(f'/api/incidents/{ident}/status',params={'status':'unknown'}).status_code==422
    assert client.patch(f'/api/incidents/{ident}/status',params={'status':'in_progress'}).json()['status']=='in_progress'
