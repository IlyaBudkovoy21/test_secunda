from sqlalchemy import ForeignKey, String, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from typing import List, Optional
from sqlalchemy import Table, Column, Integer


class Base(DeclarativeBase):
    pass


organization_activity = Table(
    'organization_activity',
    Base.metadata,
    Column('organization_id', Integer, ForeignKey('organizations.id')),
    Column('activity_id', Integer, ForeignKey('activities.id'))
)


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    organizations: Mapped[List["Organization"]] = relationship("Organization", back_populates="building")

    def __repr__(self):
        return f"<Building {self.address}>"


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('activities.id'), nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # Уровень вложенности (1-3)

    parent: Mapped[Optional["Activity"]] = relationship(
        "Activity",
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[List["Activity"]] = relationship(
        "Activity",
        back_populates="parent"
    )

    organizations: Mapped[List["Organization"]] = relationship(
        "Organization",
        secondary=organization_activity,
        back_populates="activities"
    )

    def __repr__(self):
        return f"<Activity {self.name} (level {self.level})>"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone_numbers: Mapped[List[str]] = mapped_column(ARRAY(String(50)), nullable=False)  # Массив телефонных номеров
    building_id: Mapped[int] = mapped_column(Integer, ForeignKey('buildings.id'), nullable=False)

    building: Mapped["Building"] = relationship("Building", back_populates="organizations")
    activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        secondary=organization_activity,
        back_populates="organizations"
    )

    def __repr__(self):
        return f"<Organization {self.name}>"
