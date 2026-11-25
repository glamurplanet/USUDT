from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Signal(Base):
    __tablename__ = 'signals'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(150))

class Source(Base):
    __tablename__ = 'sources'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100))

class Measurement(Base):
    __tablename__ = 'measurements'
    __table_args__ = (UniqueConstraint('source_id','external_id',name='uq_source_message'), CheckConstraint('vehicle_count >= 0'), CheckConstraint('period_seconds > 0'), CheckConstraint('occupancy >= 0 AND occupancy <= 100'))
    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey('signals.id'))
    source_id: Mapped[int] = mapped_column(ForeignKey('sources.id'))
    external_id: Mapped[str] = mapped_column(String(100))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    vehicle_count: Mapped[int] = mapped_column(Integer)
    period_seconds: Mapped[int] = mapped_column(Integer, default=60)
    occupancy: Mapped[float] = mapped_column(Float, default=0)
    speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)

class Program(Base):
    __tablename__ = 'programs'
    __table_args__ = (UniqueConstraint('signal_id','code',name='uq_program_signal'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey('signals.id'))
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120))
    approved: Mapped[bool] = mapped_column(Boolean, default=True)
    current: Mapped[bool] = mapped_column(Boolean, default=False)

class ModelEstimate(Base):
    __tablename__ = 'model_estimates'
    __table_args__ = (UniqueConstraint('program_id','scenario',name='uq_estimate_program_scenario'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey('programs.id'))
    scenario: Mapped[str] = mapped_column(String(60), default='base')
    cars_delay: Mapped[float] = mapped_column(Float)
    buses_delay: Mapped[float] = mapped_column(Float)
    trolley_delay: Mapped[float] = mapped_column(Float)
    tram_delay: Mapped[float] = mapped_column(Float)
    buses_count: Mapped[int] = mapped_column(Integer, default=0)
    trolley_count: Mapped[int] = mapped_column(Integer, default=0)
    tram_count: Mapped[int] = mapped_column(Integer, default=0)

class Forecast(Base):
    __tablename__ = 'forecasts'
    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey('signals.id'))
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    horizon_min: Mapped[int] = mapped_column(Integer)
    intensity_per_hour: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(50))

class Decision(Base):
    __tablename__ = 'decisions'
    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey('signals.id'))
    program_id: Mapped[int] = mapped_column(ForeignKey('programs.id'))
    engineer: Mapped[str] = mapped_column(String(120))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='draft')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Incident(Base):
    __tablename__ = 'incidents'
    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey('signals.id'))
    category: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='new')
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Appeal(Base):
    __tablename__ = 'appeals'
    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey('signals.id'))
    registry_code: Mapped[str] = mapped_column(String(60), unique=True)
    summary: Mapped[str] = mapped_column(Text)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default='new')
