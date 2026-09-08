import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import crosscheck, dashboard, demo, documents, equipment, issues, projects, report
from app.core.config import CORS_ORIGINS
from app.db.database import Base, engine, run_light_migrations
from app.db import models  # noqa: F401  (ensures models are registered before create_all)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

Base.metadata.create_all(bind=engine)
run_light_migrations()

app = FastAPI(
    title="Engineering CrossCheck Agent API",
    description="Decision-support API for cross-checking engineering design documents. "
                 "Not a design-approval system — final engineering judgment remains with the reviewing engineer.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(demo.router)
app.include_router(projects.router)
app.include_router(dashboard.router)
app.include_router(equipment.router)
app.include_router(issues.router)
app.include_router(documents.router)
app.include_router(crosscheck.router)
app.include_router(report.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
