from fastapi import FastAPI,HTTPException,Depends,status,BackgroundTasks,UploadFile,File
from pydantic import BaseModel
from datetime import datetime,timezone
from typing import Annotated,Optional
import models
import csv
from io import StringIO
from database import engine,SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()

models.Base.metadata.create_all(bind=engine)



class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: str
    max_attendees: int
    status: Optional[str] = "scheduled"


class EventUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: str
    max_attendees: int
    status: Optional[str] = None

class AttendeesBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str


class Checkin(BaseModel):
    check_in_status : bool



def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()





@app.post('/events',status_code=status.HTTP_201_CREATED)
async def create_event(event:EventBase, db: Session = Depends(get_db)):
    db_event = models.Events(**event.model_dump())
    db.add(db_event)
    db.commit()
    return {'message':'Event created Successfully'}



def update_event_status(db: Session):
    current_time = datetime.now(timezone.utc)
    events_to_update = db.query(models.Events).filter(
        models.Events.end_time < current_time,
        models.Events.status != "completed"
    ).all()

    for event in events_to_update:
        event.status = "completed"

    db.commit()

@app.get('/events', status_code=status.HTTP_200_OK)
async def get_events(status: Optional[str] = None, location: Optional[str] = None, start_time: Optional[datetime] = None,
                     db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    
    background_tasks.add_task(update_event_status, db)
    
    query = db.query(models.Events)

    if status:
        query = query.filter(models.Events.status == status)
    if location:
        query = query.filter(models.Events.location == location)
    if start_time:
        query = query.filter(models.Events.start_time >= start_time)

    return query.all()

@app.put('/events', status_code=status.HTTP_200_OK)
async def update_events(event_id : int,event_update : EventUpdate, db:Session = Depends(get_db)):
    event_check = db.query(models.Events).filter(models.Events.event_id == event_id).first()
    if not event_check:
        raise HTTPException(status_code=400, detail='Event not found')
    
    for key,value in event_update.model_dump(exclude_unset=True).items():
        setattr(event_check, key,value)

    db.commit()
    return {"Message": "Event Updated Successfully"}





@app.delete('/events', status_code=status.HTTP_200_OK)
async def delete_events(event_id : int, db:Session = Depends(get_db)):
    event = db.query(models.Events).filter(models.Events.event_id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail='Event not Found')
    
    db.delete(event)
    db.commit()
    return {'Message' :'Event Successfully Deleted'}



@app.post('/attendees', status_code=status.HTTP_201_CREATED)
async def create_attendees(event_id: int, attendees:AttendeesBase, db:Session = Depends(get_db)):
    event = db.query(models.Events).filter(models.Events.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail = 'Event Not found')
    
    max_events = db.query(models.Attendees).filter(models.Attendees.event_id==event_id).count()
    if max_events >= event.max_attendees:
        raise HTTPException(status_code=400, detail='Event is full')
    
    db_attendee = models.Attendees(**attendees.model_dump(),event_id = event_id)
    db.add(db_attendee)
    db.commit()
    return {'message' : 'Registration is successfully done'}


@app.get('/attendees', status_code=status.HTTP_200_OK)
async def get_attendees(event_id : int, db:Session=Depends(get_db)):
    get_attendees = db.query(models.Attendees).filter(models.Attendees.event_id == event_id).all()
    return get_attendees



@app.post('/register', status_code=status.HTTP_200_OK)
async def check_in(attendee_id :int, check_in : Checkin, db : Session = Depends(get_db)):
    attendee = db.query(models.Attendees).filter(models.Attendees.attendee_id==attendee_id).first()
    if not attendee:
        raise HTTPException(status_code=404, detail='Data not found')

    attendee.check_in_status = check_in.check_in_status
    db.commit()
    return {'Message' : 'Check in done Successfully'}    
    



@app.post('/bulk-check-in', status_code=status.HTTP_200_OK)
async def bulk_check_in(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    decoded_content = content.decode("utf-8")
    csv_reader = csv.reader(StringIO(decoded_content))
    
    attendee_ids = []
    for row in csv_reader:
        try:
            attendee_id = int(row[0]) 
            attendee_ids.append(attendee_id)
        except ValueError:
            continue  

    attendees = db.query(models.Attendees).filter(models.Attendees.attendee_id.in_(attendee_ids)).all()
    
    if not attendees:
        raise HTTPException(status_code=404, detail="No valid attendees found in the file")

    for attendee in attendees:
        attendee.check_in_status = True

    db.commit()
    return {"message": f"Check-in successful for {len(attendees)} attendees"}



