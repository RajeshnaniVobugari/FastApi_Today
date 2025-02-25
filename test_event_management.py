import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base

import models
import time
from main import app,get_db,engine
from apscheduler.schedulers.background import BackgroundScheduler
from main import update_event_status 

TEST_DB_URL = "mssql+pyodbc://@RAJESH\\SQLEXPRESS/Trance?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"

test_engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_registration_limit(setup_db):
    db = TestingSessionLocal()
    
    event = models.Events(
        name="Tech Conference",
        description="A test event",
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
        end_time=datetime.now(timezone.utc) + timedelta(days=2),
        location="New York",
        max_attendees=2,
        status="scheduled"
    )
    db.add(event)
    db.commit()
    event_id = event.event_id

    attendee1 = {"first_name": "John", "last_name": "Doe", "email": "john@example.com", "phone_number": "1234567890"}
    attendee2 = {"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com", "phone_number": "9876543210"}

    response1 = client.post(f"/attendees?event_id={event_id}", json=attendee1)
    response2 = client.post(f"/attendees?event_id={event_id}", json=attendee2)
    
    assert response1.status_code == 201
    assert response2.status_code == 201

    attendee3 = {"first_name": "Mike", "last_name": "Brown", "email": "mike@example.com", "phone_number": "5555555555"}
    response3 = client.post(f"/attendees?event_id={event_id}", json=attendee3)

    assert response3.status_code == 400
    assert response3.json()["detail"] == "Event is full"

def test_check_in(setup_db):
    db = TestingSessionLocal()

    event = models.Events(
        name="AI Summit",
        description="An AI-focused event",
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
        end_time=datetime.now(timezone.utc) + timedelta(days=2),
        location="San Francisco",
        max_attendees=5,
        status="scheduled"
    )
    db.add(event)
    db.commit()
    event_id = event.event_id

    attendee_data = {"first_name": "Alice", "last_name": "Wonderland", "email": "alice@example.com", "phone_number": "1112223333"}
    response = client.post(f"/attendees?event_id={event_id}", json=attendee_data)
    assert response.status_code == 201

    attendee = db.query(models.Attendees).filter(models.Attendees.email == "alice@example.com").first()
    assert attendee is not None

    check_in_data = {"check_in_status": True}
    check_in_response = client.post(f"/register?attendee_id={attendee.attendee_id}", json=check_in_data)
    
    assert check_in_response.status_code == 200
    assert check_in_response.json()["Message"] == "Check in done Successfully"

