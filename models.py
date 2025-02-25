from sqlalchemy import Boolean, Column,Integer,String,DateTime,ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class Attendees(Base):
    __tablename__ = "attendees"

    attendee_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20), nullable=False)
    event_id = Column(Integer, ForeignKey("events.event_id"))
    check_in_status = Column(Boolean, default=False) 
    event = relationship("Events", back_populates="attendees")

class Events(Base):
    __tablename__ = 'events'

    event_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=False)
    max_attendees = Column(Integer, nullable=False)
    status = Column(String(500), nullable=False)
    attendees = relationship("Attendees", back_populates="event") 