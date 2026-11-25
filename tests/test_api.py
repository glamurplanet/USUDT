from datetime import datetime,timezone,timedelta

def make_message(i):
    return {'source_code':'I01','external_id':f'unit-{i}','signal_code':'S01','observed_at':(datetime.now(timezone.utc)-timedelta(minutes=i)).isoformat(),'vehicle_count':15+i,'period_seconds':60,'occupancy':25}

def test_health_and_signals(client):
    assert client.get('/health').json()['status']=='ok'
    assert len(client.get('/api/signals').json())==5

def test_input_checks_and_duplicate(client):
    bad=make_message(0);bad['vehicle_count']=-1
    assert client.post('/api/measurements',json=bad).status_code==422
    payload=make_message(0)
    assert client.post('/api/measurements',json=payload).json()['status']=='created'
    assert client.post('/api/measurements',json=payload).json()['status']=='duplicate'

def test_forecast_and_decision_guard(client):
    for i in range(15):assert client.post('/api/measurements',json=make_message(i)).status_code==200
    result=client.get('/api/forecast/S01').json()
    assert result['available'] is True and result['horizons_min']==[5,10,15]
    p=client.post('/api/programs',json={'signal_code':'S01','code':'P1','name':'Режим 1'}).json()['id']
    d=client.post('/api/decisions',json={'signal_code':'S01','program_id':p,'engineer':'Инженер','reason':'Выбор программы'}).json()['id']
    assert client.post(f'/api/decisions/{d}/confirm',json={'engineer':'Другой'}).status_code==403
    confirm=client.post(f'/api/decisions/{d}/confirm',json={'engineer':'Инженер'}).json()
    assert confirm['status']=='confirmed'
    assert 'asu_dd_package' in confirm

def test_program_requires_model(client):
    for i in range(15):client.post('/api/measurements',json=make_message(i))
    client.post('/api/programs',json={'signal_code':'S01','code':'P1','name':'Режим 1'})
    r=client.get('/api/programs/compare/S01').json()
    assert r['available'] is False and 'оценки' in r['reason']

def test_incident_appeal_and_report(client):
    assert client.post('/api/incidents',json={'signal_code':'S02','category':'отказ','description':'нет связи'}).status_code==200
    a={'signal_code':'S02','registry_code':'A-100','summary':'жалоба на задержки','period_start':'2026-10-01T10:00:00+03:00','period_end':'2026-10-01T11:00:00+03:00'}
    assert client.post('/api/appeals',json=a).status_code==200
    r=client.get('/api/report').json()
    assert next(x for x in r['objects'] if x['signal']=='S02')['appeals']==1
