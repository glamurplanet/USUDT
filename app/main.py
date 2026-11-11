from datetime import datetime, timezone, timedelta
from pathlib import Path
import csv, io
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import models as m, schemas as s
from .logic import completeness_and_freshness, predict_intensity, weighted_delay

app = FastAPI(title='УСУДТ', description='Анализ дорожного движения и поддержка решений инженера по ОДД',version='0.1.0')
BASE = Path(__file__).resolve().parent


def get_signal(db, code):
    signal = db.scalar(select(m.Signal).where(m.Signal.code==code))
    if not signal: raise HTTPException(404, f'СО {code} не найден')
    return signal


def add_measurement(db, data: s.MeasurementIn):
    signal = get_signal(db, data.signal_code)
    source = db.scalar(select(m.Source).where(m.Source.code==data.source_code))
    if not source: raise HTTPException(404, f'Источник {data.source_code} не найден')
    exists = db.scalar(select(m.Measurement).where(m.Measurement.source_id==source.id,m.Measurement.external_id==data.external_id))
    if exists: return {'status':'duplicate','id':exists.id}
    item = m.Measurement(signal_id=signal.id,source_id=source.id,external_id=data.external_id,observed_at=data.observed_at,vehicle_count=data.vehicle_count,period_seconds=data.period_seconds,occupancy=data.occupancy,speed_kmh=data.speed_kmh)
    db.add(item)
    try: db.commit()
    except IntegrityError: db.rollback(); return {'status':'duplicate'}
    db.refresh(item)
    return {'status':'created','id':item.id}


def measurement_window(db, signal_id):
    from sqlalchemy import select
    since = datetime.now(timezone.utc)-timedelta(minutes=15)
    # sqlite and postgresql both support >= aware timestamps through SQLAlchemy
    return list(db.scalars(select(m.Measurement).where(m.Measurement.signal_id==signal_id,m.Measurement.observed_at>=since).order_by(m.Measurement.observed_at)))

@app.get('/',response_class=HTMLResponse)
def home(db: Session=Depends(get_db)):
    rows = db.scalars(select(m.Signal).order_by(m.Signal.id)).all()
    lis = ''.join(f'<li>{r.code}: {r.name}</li>' for r in rows)
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>УСУДТ</title><style>body{{font-family:Arial,sans-serif;max-width:900px;margin:42px auto;line-height:1.55;color:#222}}a{{color:#154e76}}.box{{border:1px solid #ddd;padding:18px;border-radius:6px}}</style></head><body><h1>УСУДТ</h1><p>Мониторинг транспортных потоков на пяти перекрёстках ул. Северной.</p><div class="box"><h2>Светофорные объекты</h2><ul>{lis}</ul><p><a href="/docs">Открыть интерфейс API (Swagger)</a></p><p><a href="/api/report">Сводные показатели</a></p></div><p>Выбор программы требует подтверждения инженера. Команды контроллерам отсюда не направляются.</p></body></html>'''

@app.get('/health')
def health():return {'status':'ok'}

@app.get('/api/signals')
def signals(db:Session=Depends(get_db)):
    return [{'code':x.code,'name':x.name} for x in db.scalars(select(m.Signal)).all()]

@app.post('/api/measurements')
def post_measurement(data:s.MeasurementIn,db:Session=Depends(get_db)):
    return add_measurement(db,data)

@app.post('/api/measurements/csv')
async def import_csv(file:UploadFile=File(...),db:Session=Depends(get_db)):
    if not file.filename.lower().endswith('.csv'):raise HTTPException(400,'Требуется CSV-файл')
    try: rows=list(csv.DictReader(io.StringIO((await file.read()).decode('utf-8-sig'))))
    except Exception as ex: raise HTTPException(400,f'Ошибка чтения CSV: {ex}')
    summary={'created':0,'duplicate':0,'errors':[]}
    for idx,row in enumerate(rows, start=2):
        try:
            value=s.MeasurementIn.model_validate(row)
            answer=add_measurement(db,value)
            summary[answer['status']]+=1
        except Exception as ex:summary['errors'].append({'line':idx,'detail':str(ex)[:240]})
    return summary

@app.get('/api/forecast/{signal_code}')
def forecast(signal_code:str,db:Session=Depends(get_db)):
    signal=get_signal(db,signal_code)
    window=measurement_window(db,signal.id)
    ok,reason=completeness_and_freshness(window)
    if not ok:return {'signal':signal_code,'available':False,'reason':reason,'last_measurement':max((v.observed_at.isoformat() for v in window),default=None)}
    calc=predict_intensity(window)
    for horizon in (5,10,15):
        db.add(m.Forecast(signal_id=signal.id,horizon_min=horizon,intensity_per_hour=calc['intensity_per_hour'],method=calc['method']))
    db.commit()
    return {'signal':signal_code,'available':True,'horizons_min':[5,10,15],**calc,'note':'Одинаковая базовая оценка на каждом горизонте; в дальнейшем проверяется по фактическим измерениям'}

@app.post('/api/programs')
def create_program(data:s.ProgramIn,db:Session=Depends(get_db)):
    signal=get_signal(db,data.signal_code)
    p=m.Program(signal_id=signal.id,code=data.code,name=data.name,approved=data.approved,current=data.current)
    db.add(p)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Программа с этим кодом уже есть')
    db.refresh(p)
    return {'id':p.id,'code':p.code}

@app.post('/api/estimates')
def create_estimate(data:s.EstimateIn,db:Session=Depends(get_db)):
    p=db.get(m.Program,data.program_id)
    if not p:raise HTTPException(404,'Программа не найдена')
    e=m.ModelEstimate(**data.model_dump())
    db.add(e)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Оценка для программы и сценария уже существует')
    return {'id':e.id}

@app.get('/api/programs/compare/{signal_code}')
def compare_programs(signal_code:str,car_weight:float=0.7,scenario:str='base',db:Session=Depends(get_db)):
    signal=get_signal(db,signal_code)
    ok,reason=completeness_and_freshness(measurement_window(db,signal.id))
    if not ok:return {'available':False,'reason':reason}
    programs=list(db.scalars(select(m.Program).where(m.Program.signal_id==signal.id,m.Program.approved==True).order_by(m.Program.current.desc(),m.Program.id).limit(3)))
    if not programs:return {'available':False,'reason':'Нет утверждённых программ'}
    variants=[]
    for p in programs:
        e=db.scalar(select(m.ModelEstimate).where(m.ModelEstimate.program_id==p.id,m.ModelEstimate.scenario==scenario))
        if e is None:return {'available':False,'reason':f'Нет согласованной оценки задержек для {p.code}'}
        try:total,public=weighted_delay(e.cars_delay,e.buses_delay,e.trolley_delay,e.tram_delay,e.buses_count,e.trolley_count,e.tram_count,car_weight)
        except ValueError as ex:return {'available':False,'reason':str(ex)}
        variants.append({'program_id':p.id,'program':p.code,'current':p.current,'score':total,'public_transport_delay':public,'cars_delay':e.cars_delay})
    return {'available':True,'signal':signal_code,'variants':sorted(variants,key=lambda v:v['score']),'note':'Сравнение на основе загруженной транспортной модели, а не непосредственного управления светофорами'}

@app.post('/api/decisions')
def create_decision(data:s.DecisionIn,db:Session=Depends(get_db)):
    signal=get_signal(db,data.signal_code)
    program=db.get(m.Program,data.program_id)
    if not program or program.signal_id!=signal.id or not program.approved:raise HTTPException(400,'Программа не утверждена для выбранного СО')
    obj=m.Decision(signal_id=signal.id,program_id=program.id,engineer=data.engineer,reason=data.reason,status='draft')
    db.add(obj);db.commit();db.refresh(obj)
    return {'id':obj.id,'status':obj.status}

@app.post('/api/decisions/{decision_id}/confirm')
def confirm_decision(decision_id:int,data:s.ConfirmIn,db:Session=Depends(get_db)):
    d=db.get(m.Decision,decision_id)
    if not d:raise HTTPException(404,'Решение не найдено')
    if data.engineer!=d.engineer:raise HTTPException(403,'Подтвердить может только автор решения')
    if d.status=='confirmed':return {'id':d.id,'status':'confirmed','duplicate':True}
    if d.status!='draft':raise HTTPException(409,'Текущий статус не позволяет подтверждение')
    signal=db.get(m.Signal,d.signal_id)
    ok,reason=completeness_and_freshness(measurement_window(db,d.signal_id))
    if not ok:raise HTTPException(409,reason)
    d.status='confirmed';d.confirmed_at=datetime.now(timezone.utc);db.commit()
    return {'id':d.id,'status':'confirmed','asu_dd_package':{'signal_code':signal.code,'program_id':d.program_id,'decision_id':d.id},'note':'Пакет подготовлен. Фактический ввод выполняет инженер через АСУДД.'}

@app.post('/api/incidents')
def post_incident(data:s.IncidentIn,db:Session=Depends(get_db)):
    signal=get_signal(db,data.signal_code)
    obj=m.Incident(signal_id=signal.id,category=data.category,description=data.description)
    db.add(obj);db.commit();db.refresh(obj)
    return {'id':obj.id,'status':obj.status}

@app.post('/api/appeals')
def post_appeal(data:s.AppealIn,db:Session=Depends(get_db)):
    signal=get_signal(db,data.signal_code)
    if data.period_end<data.period_start:raise HTTPException(422,'Конец периода раньше начала')
    a=m.Appeal(signal_id=signal.id,registry_code=data.registry_code,summary=data.summary,period_start=data.period_start,period_end=data.period_end)
    db.add(a)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Обращение с этим кодом уже зарегистрировано')
    return {'id':a.id,'status':a.status}

@app.get('/api/report')
def report(db:Session=Depends(get_db)):
    out=[]
    for sig in db.scalars(select(m.Signal).order_by(m.Signal.id)):
        out.append({'signal':sig.code,'name':sig.name,'measurements':db.scalar(select(func.count(m.Measurement.id)).where(m.Measurement.signal_id==sig.id)),'decisions':db.scalar(select(func.count(m.Decision.id)).where(m.Decision.signal_id==sig.id)),'incidents':db.scalar(select(func.count(m.Incident.id)).where(m.Incident.signal_id==sig.id)),'appeals':db.scalar(select(func.count(m.Appeal.id)).where(m.Appeal.signal_id==sig.id))})
    return {'objects':out,'note':'Оперативная сводка по сохранённым данным; сравнительная оценка до/после требует сопоставимых периодов'}

@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine)
    from .seed import seed_reference
    with next(get_db()) as db:seed_reference(db)
