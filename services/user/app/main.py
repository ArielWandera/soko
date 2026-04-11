from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.database import Base, engine
from app.routers import follows,internal,profile,reviews,settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Soko User Service",
    description="User profiles, stats, reviews and follows",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/users",
)

app.include_router(follows)
app.include_router(internal)
app.include_router(profile)
app.include_router(settings)
app.include_router(reviews)