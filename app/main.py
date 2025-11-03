from fastapi import FastAPI, Depends,UploadFile,File,Request
from app.helper import upload_file
from app.database import get_db
from sqlalchemy import text
from app.database import engine
from app.models import Base
from sqlalchemy.orm import Session
from app.routers import users,vm_master,vm_status,monitor,logs
from fastapi.staticfiles import StaticFiles
from app.core.auth import get_current_user   
from fastapi.middleware.cors import CORSMiddleware
from app.helper.path import LOGS_DIR

Base.metadata.create_all(bind=engine)
app = FastAPI()
 
origins = ["*","10.0.5.22","http://localhost","http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory=LOGS_DIR), name="log_files")

app.include_router(users.auth)
app.include_router(users.user)
app.include_router(vm_master.router)
app.include_router(vm_status.router)
app.include_router(monitor.router)
app.include_router(logs.router)

@app.get("/")
def root():
    return {"message" : "Hello from FastAPI !!"}

@app.get("/testdb")
def test_database_connection(db :Session  =  Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"message":" database connection is successful !"}
    except Exception as e:
        return {"error" : "occured error "+ e}


