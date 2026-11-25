from .database import Base,engine,SessionLocal
from . import models
from .seed import seed_reference

def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:seed_reference(db)
    print('База данных создана, справочники загружены')

if __name__=='__main__':main()
