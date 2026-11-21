from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # "fiverr_main"
    cookies_json: Mapped[str] = mapped_column(Text)  # encrypted
    local_storage_json: Mapped[str] = mapped_column(Text, default="{}")
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
