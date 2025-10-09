# create_admin.py
from app.database import SessionLocal
from app.models import User
from app.core.security import hash_password

db = SessionLocal()
if(db.query(User).count() == 0):
    name = input("Enter admin name: ")
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    hashed_password = hash_password(password)
    admin = User(name=name,email=email, password=hashed_password, is_active=True, role=1)
    db.add(admin)
    db.commit()
    print("Admin user created!")
else:
    print("Admin user already exists.")