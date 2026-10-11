from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import Base, engine
import models

from features.materials.router import router as materials_router
from features.assessment.router import router as assessment_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Protégé")

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],
    allow_methods=["*"], 
    allow_headers=["*"]
)

app.include_router(materials_router)
app.include_router(assessment_router)
