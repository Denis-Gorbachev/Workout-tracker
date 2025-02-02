from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import update, delete
import uvicorn, datetime, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.future import select
import os
import asyncio
from Database import *
from Models import *
from Schemas import *

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_pwd(pwd):
    return pwd_context.hash(pwd)

async def get_user(db = Depends(get_session), token = Depends(oauth2_scheme)):
    credetials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = data.get("sub")
        if user is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credetials_exception
    user = (await db.scalars(select(User).where(User.username == user))).first()
    if user is None:
        raise credetials_exception
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
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or not verify_pwd(pwd, user.pwd_hash):
        return False
    return user

app = FastAPI()

@app.post("/signup")
async def signup(user: UserCreate, db: AsyncSession = Depends(get_session)):
    hashed_pwd = hash_pwd(user.password)
    user = User(username = user.username, pwd_hash = hashed_pwd)
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
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/create_workout")
async def create_workout(workout: WorkoutCreate, db: async_session = Depends(get_session), cur_user: UserCreate = Depends(get_user)):
    res = await db.execute(select(Workout).where(Workout.exercise_id == workout.exercise_id, Workout.user_id == cur_user.id))
    if res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workout already exists"
        )
    workout = Workout(
        user_id = cur_user.id,
        exercise_id = workout.exercise_id,
        sets = workout.sets,
        repetitions = workout.repetitions,
        weights = workout.weights
    )
    db.add(workout)
    await db.commit()
    return {"message":"Workout created successfully"}

@app.post("/update_workout")
async def update_workout(update_workout: WorkoutCreate, db: async_session = Depends(get_session), cur_user: UserCreate = Depends(get_user)):
    update_data = update_workout.dict(exclude_unset=True)
    update_stmt = update(Workout).where(Workout.exercise_id == updated_workout.exercise_id, Workout.user_id == cur_user.id).values(update_data)
    await db.execute(update_stmt)
    await db.commit()
    return {"message":"Workout updated successfully"}

@app.delete("/delete_workout")
async def delete_workout(delete_workout: WorkoutDelete, db: async_session = Depends(get_session), cur_user: UserCreate = Depends(get_user)):
    delete_stmt = delete(Workout).where(Workout.exercise_id == delete_workout.exercise_id, Workout.user_id == cur_user.id)
    await db.execute(delete_stmt)
    await db.commit()
    return {"message":"Workout deleted successfully"}

@app.get("/list_workouts")
async def list_workouts(db: async_session = Depends(get_session), cur_user: UserCreate = Depends(get_user)):
    result = await db.execute(select(Workout).where(Workout.user_id == cur_user.id))
    workouts = result.scalars().all()
    json_data = []
    if workouts:
        for workout in workouts:
            json_data.append({
                "exercise_id": workout.exercise_id,
                "sets":workout.sets,
                "repetitions":workout.repetitions,
                "weights":workout.weights
            })
    return json_data

@app.on_event("startup")
async def startup_event():
    await init_models()

if __name__=="__main__":
    uvicorn.run("Registration:app", reload=True)
