import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base,get_db
from app.main import app
from app.seed import seed_reference

@pytest.fixture
def client():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine,expire_on_commit=False)
    with Session() as db:seed_reference(db)
    def override():
        with Session() as db:yield db
    app.dependency_overrides[get_db]=override
    with TestClient(app) as test_client:yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
