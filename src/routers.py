from fastapi import Depends, HTTPException, Query, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from typing import List
import math

from src.database import get_db
from src.models import Building, Organization, Activity

router = APIRouter(prefix="/api/v1")


@router.get("/buildings/{building_id}/organizations", response_model=List[dict])
def get_organizations_by_building(building_id: int, db: AsyncSession = Depends(get_db)):
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    organizations = db.query(Organization).filter(Organization.building_id == building_id).all()
    return [org.to_dict() for org in organizations]


@router.get("/activities/{activity_id}/organizations", response_model=List[dict])
def get_organizations_by_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    organizations = db.query(Organization).join(Organization.activities).filter(Activity.id == activity_id).all()
    return [org.to_dict() for org in organizations]


@router.get("/organizations/nearby", response_model=List[dict])
def get_organizations_nearby(
        lat: float = Query(..., description="Широта центральной точки"),
        lon: float = Query(..., description="Долгота центральной точки"),
        radius_km: float = Query(1.0, description="Радиус в километрах"),
        db: AsyncSession = Depends(get_db)
):
    def calculate_distance(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    all_buildings = db.query(Building).all()
    nearby_buildings = []

    for building in all_buildings:
        distance = calculate_distance(lat, lon, building.latitude, building.longitude)
        if distance <= radius_km:
            nearby_buildings.routerend(building.id)

    if not nearby_buildings:
        return []

    organizations = db.query(Organization).filter(Organization.building_id.in_(nearby_buildings)).all()
    return [org.to_dict() for org in organizations]


@router.get("/organizations/in-rectangle", response_model=List[dict])
def get_organizations_in_rectangle(
        lat_min: float = Query(..., description="Минимальная широта"),
        lat_max: float = Query(..., description="Максимальная широта"),
        lon_min: float = Query(..., description="Минимальная долгота"),
        lon_max: float = Query(..., description="Максимальная долгота"),
        db: AsyncSession = Depends(get_db)
):
    buildings = db.query(Building).filter(
        and_(
            Building.latitude >= lat_min,
            Building.latitude <= lat_max,
            Building.longitude >= lon_min,
            Building.longitude <= lon_max
        )
    ).all()

    building_ids = [building.id for building in buildings]
    organizations = db.query(Organization).filter(Organization.building_id.in_(building_ids)).all()
    return [org.to_dict() for org in organizations]


@router.get("/buildings", response_model=List[dict])
def get_all_buildings(db: AsyncSession = Depends(get_db)):
    buildings = db.query(Building).all()
    return [building.to_dict() for building in buildings]


@router.get("/organizations/{organization_id}", response_model=dict)
def get_organization_by_id(organization_id: int, db: AsyncSession = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization.to_dict()


@router.get("/organizations/search/by-activity", response_model=List[dict])
def search_organizations_by_activity(
        activity_name: str = Query(..., description="Название вида деятельности"),
        db: AsyncSession = Depends(get_db)
):
    root_activity = db.query(Activity).filter(
        Activity.name.ilike(f"%{activity_name}%"),
        Activity.level == 1
    ).first()

    if not root_activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    def get_child_activities(parent_id, current_level=1):
        if current_level > 3:
            return []

        children = db.query(Activity).filter(Activity.parent_id == parent_id).all()
        result = [child.id for child in children]

        for child in children:
            result.extend(get_child_activities(child.id, current_level + 1))

        return result

    all_activity_ids = [root_activity.id] + get_child_activities(root_activity.id)

    organizations = db.query(Organization).join(Organization.activities).filter(
        Activity.id.in_(all_activity_ids)
    ).all()

    return [org.to_dict() for org in organizations]


@router.get("/organizations/search/by-name", response_model=List[dict])
def search_organizations_by_name(
        name: str = Query(..., description="Название организации"),
        db: AsyncSession = Depends(get_db)
):
    organizations = db.query(Organization).filter(Organization.name.ilike(f"%{name}%")).all()
    return [org.to_dict() for org in organizations]


@router.get("/activities", response_model=List[dict])
def get_all_activities(
        max_level: int = Query(3, description="Максимальный уровень вложенности"),
        db: AsyncSession = Depends(get_db)
):
    activities = db.query(Activity).filter(Activity.level <= max_level).all()
    return [activity.to_dict() for activity in activities]
