import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy import MetaData, func, DateTime
from datetime import datetime
from app.core.config import settings

POSTGRES_SCHEMA = "wp"

class Base(DeclarativeBase):
    metadata = MetaData(schema=POSTGRES_SCHEMA)
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, sort_order=-100)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        sort_order=90
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        sort_order=100
    )