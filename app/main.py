from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.monitoring import monitoring_engine
from app.routes.alerts import router as alerts_router
from app.routes.handover import router as handover_router
from app.routes.monitoring import router as monitoring_router
from app.routes.patients import router as patients_router
from app.routes.vitals import router as vitals_router
from app.storage import ensure_data_files


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_data_files()
    await monitoring_engine.start()
    yield
    await monitoring_engine.stop()


app = FastAPI(
    title="Ward AI MVP",
    version="0.3.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(patients_router)
app.include_router(vitals_router)
app.include_router(alerts_router)
app.include_router(monitoring_router)
app.include_router(handover_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Ward AI MVP API is running"}