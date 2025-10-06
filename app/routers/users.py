from app.database import get_db
from app.schemas import UserCreate,UserResponse, Token
from app.crud import insert_user,get_user_by_email
from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from app.core import verify_password
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from app.core import hash_password, refresh_token, create_token, decode_token
from app.core.auth import get_current_user


auth  = APIRouter(prefix="/auth", tags=["Auth"])
user  = APIRouter(prefix="/users", tags=["Users Module"], dependencies=[Depends(get_current_user)])

@user.post("/create", response_model= UserResponse)
def create_user(userdata:UserCreate, db:Session = Depends(get_db)):
    is_exist = get_user_by_email(db, userdata.email)
    if is_exist:
        raise HTTPException(status_code=409, detail="Email already registerd")
    data = userdata.model_dump(exclude={"password"})
    data['password'] = hash_password(userdata.password)
    user = insert_user(db,data)
    db.commit()
    db.refresh(user)
    return user

 

@auth.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 spec expects 'username' + 'password' form fields.
    We treat 'username' as the user's email.
    """
    user = get_user_by_email(db, form.username)
    if not user or not verify_password(form.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password.")

    # If you store scopes/roles somewhere (e.g., user.scopes), include them here:
    scopes = getattr(user, "scopes", []) or []

    access = create_token(subject=str(user.id), name=user.name, scopes=scopes)
    refresh = refresh_token(subject=str(user.id))
    return Token(access_token=access, refresh_token=refresh)

@user.get("/me", response_model=UserResponse)
def read_me(current_user = Depends(get_current_user)):

    return current_user

@auth.post("/refresh", response_model=Token)
def refresh(access_refresh_token: str, db: Session = Depends(get_db)):
    try:
        claims = decode_token(access_refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if claims.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Not a refresh token.")

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Token subject missing.")
    new_access = create_token(subject=str(user_id), name=claims.get("name", ""), scopes=claims.get("scopes", []))
    new_refresh = refresh_token(subject=str(user_id))
    return Token(access_token=new_access, refresh_token=new_refresh)




