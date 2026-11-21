import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class GigStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class Gig(Base, TimestampMixin):
    __tablename__ = "gigs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(100))
    subcategory: Mapped[str] = mapped_column(String(100))
    title_template: Mapped[str] = mapped_column(Text)
    description_template: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    package_basic_price: Mapped[int] = mapped_column(Integer)
    package_basic_days: Mapped[int] = mapped_column(Integer)
    package_basic_revisions: Mapped[int] = mapped_column(Integer)
    package_basic_features: Mapped[list] = mapped_column(JSON, default=list)
    package_standard_price: Mapped[int] = mapped_column(Integer)
    package_standard_days: Mapped[int] = mapped_column(Integer)
    package_standard_revisions: Mapped[int] = mapped_column(Integer)
    package_standard_features: Mapped[list] = mapped_column(JSON, default=list)
    package_premium_price: Mapped[int] = mapped_column(Integer)
    package_premium_days: Mapped[int] = mapped_column(Integer)
    package_premium_revisions: Mapped[int] = mapped_column(Integer)
    package_premium_features: Mapped[list] = mapped_column(JSON, default=list)
    extras_json: Mapped[list] = mapped_column(JSON, default=list)
    faq_json: Mapped[list] = mapped_column(JSON, default=list)
    requirements_json: Mapped[list] = mapped_column(JSON, default=list)
    image_urls: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(String(200), default="")
    ab_variants_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[GigStatus] = mapped_column(
        Enum(GigStatus), default=GigStatus.DRAFT
    )
    gig_id: Mapped[str] = mapped_column(String(100), nullable=True)
    gig_url: Mapped[str] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="gig")
