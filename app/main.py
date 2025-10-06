from fastapi import FastAPI, Depends,UploadFile,File,Request
from app.helper import upload_file
from app.database import get_db
from sqlalchemy import text
from app.database import engine
from app.models import Base
from sqlalchemy.orm import Session
from app.routers import users,vm_master,vm_status,api
from fastapi.staticfiles import StaticFiles
from app.core.auth import get_current_user   
app = FastAPI()

Base.metadata.create_all(bind = engine)
app.mount("/logs", StaticFiles(directory="uploads/logs"), name="logs")

app.include_router(users.auth)
app.include_router(users.user)
app.include_router(vm_master.router)
app.include_router(vm_status.router)
app.include_router(api.router)

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
    

@app.post("/upload", dependencies = [Depends(get_current_user)])
async def uploadFile(request:Request,file: UploadFile = File(...)):
    return await upload_file(request,file)

