from sqlalchemy import select
from .models import Signal, Source

SIGNALS=[('S01','Северная / Красная'),('S02','Северная / Рашпилевская'),('S03','Северная / Головатого'),('S04','Северная / Садовая'),('S05','Северная / Фрунзе')]
SOURCES=[('I01','Детекторы АСУДД'),('I02','Видеоаналитика ИТС'),('I03','Метеоданные'),('I04','ДТП'),('I05','Реестр обращений'),('I06','Журнал неисправностей'),('I07','Общественный транспорт'),('I08','Задания'),('IR1','Паспорта и каталог программ'),('IR2','Транспортная модель')]

def seed_reference(db):
    for code,name in SIGNALS:
        if not db.scalar(select(Signal).where(Signal.code==code)):db.add(Signal(code=code,name=name))
    for code,name in SOURCES:
        if not db.scalar(select(Source).where(Source.code==code)):db.add(Source(code=code,name=name))
    db.commit()
