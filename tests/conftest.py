import sqlite3
import pytest
from fastapi.testclient import TestClient
from src.config import Settings
from src.data.generate import generate
from src.pipeline.run import run
from src.api.app import create_app

@pytest.fixture(scope="session")
def built(tmp_path_factory):
    settings = Settings(root=tmp_path_factory.mktemp("packright"), database_url="sqlite:///data/processed/packright.db")
    generate(settings, scale=.08)
    summary = run(settings)
    return settings, summary

@pytest.fixture
def conn(built):
    connection = sqlite3.connect(built[0].db_path)
    connection.row_factory = sqlite3.Row
    yield connection
    connection.close()

@pytest.fixture
def client(built):
    with TestClient(create_app(built[0])) as c:
        yield c
