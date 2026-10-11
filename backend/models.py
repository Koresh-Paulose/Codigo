from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from db import Base

class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, default="demo")
    title = Column(String, nullable=False)
    file_type = Column(String)
    file_path = Column(String)
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    chunks = relationship("Chunk", cascade="all, delete-orphan", back_populates="material",
                          order_by="Chunk.position")

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    position = Column(Integer)
    text = Column(Text, nullable=False)
    material = relationship("Material", back_populates="chunks")

class StudySession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, default="demo")
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    status = Column(String, default="active")          # active | finished
    flaw_claim = Column(Text, nullable=True)           # the planted wrong statement
    flaw_truth = Column(Text, nullable=True)           # what is actually correct
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

class Concept(Base):
    __tablename__ = "concepts"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    name = Column(String, nullable=False)
    summary = Column(Text, nullable=False)             # ground truth from the material
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=True)

class Turn(Base):
    __tablename__ = "turns"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)              # "student" (AI) | "user" (teacher)
    content = Column(Text, nullable=False)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=True)
    hint_level = Column(Integer, default=0)            # 0-4, written by hint_by_hint
    is_exam = Column(Boolean, default=False)
    reply_to = Column(Integer, nullable=True)          # exam answer -> question turn id
    created_at = Column(DateTime, default=datetime.utcnow)

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), unique=True, nullable=False)
    coverage = Column(Integer)
    accuracy = Column(Integer)
    clarity = Column(Integer)
    flaw = Column(Integer, nullable=True)              # 100 / 0, or NULL if no flaw planted
    independence = Column(Integer)
    total = Column(Integer)
    details = Column(Text)                             # JSON: feedback, errors, missed concepts
    created_at = Column(DateTime, default=datetime.utcnow)