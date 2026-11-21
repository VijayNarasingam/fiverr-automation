import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class OrderStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    DISPUTED = "disputed"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fiverr_order_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )
    gig_id: Mapped[int] = mapped_column(ForeignKey("gigs.id"))
    buyer_username: Mapped[str] = mapped_column(String(100))
    amount: Mapped[int] = mapped_column(Integer)  # in cents
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.NEW
    )
    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    requirements: Mapped[dict] = mapped_column(JSON, default=dict)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_url: Mapped[str] = mapped_column(Text, nullable=True)

    gig: Mapped["Gig"] = relationship(back_populates="orders")
    messages: Mapped[list["Message"]] = relationship(back_populates="order")
