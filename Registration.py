from fastapi import FastAPI, HTTPException, Depends
import uvicorn
import datetime
import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.future import select

from Database import *
from Schemas import *

SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class UserCreate(BaseModel):
    username: str
    password: str

def hash_pwd(pwd):
    return pwd_context.hash(pwd)

async def get_user(db, username):
    user = (await db.scalars(select(Users).where(Users.username == username))).first()
    return user

def verify_pwd(pwd, hashed_pwd):
    return pwd_context.verify(pwd, hashed_pwd)

def create_access_token(data: dict):
    jwt_data = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_data.update({"exp":expire})
    encoded_jwt = jwt.encode(jwt_data, SECRET_KEY, ALGORITHM)
    return encoded_jwt

async def authenticate_user(db, username, pwd):
    stmt = select(Users).where(Users.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or not verify_pwd(pwd, user.pwd_hash):
        return False
    return user

app = FastAPI()

@app.post("/signup")
async def signup(user: UserCreate, db: AsyncSession = Depends(get_session)):
    hashed_pwd = hash_pwd(user.password)
    user = Users(username = user.username, pwd_hash = hashed_pwd)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    access_token = create_access_token({"sub":user.username})
    return {"access_token":access_token}

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: async_session = Depends(get_session)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub":form_data.username})
    return access_token

@app.on_event("startup")
async def startup_event():
    await init_models()

if __name__=="__main__":
    uvicorn.run("Registration:app", reload=True)