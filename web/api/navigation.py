from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
import uuid
from database.lifetime import get_session, Event, EventContent
router = APIRouter()
from schema.navigation import LocationItem, UserLocationRequest, UserLocationResponse
from schema.database import ActivityLocation
from typing import List
from fastapi import Query
from dateutil import parser
import random
import requests
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "navigation.json")

def get_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/api/navigation/locations/nearby")
async def get_nearby_locations(
    lat: float = Query(..., description="用户纬度"),
    lng: float = Query(..., description="用户经度"),
    radius: int = Query(2000, description="搜索半径（米）"),
    category: str = Query(None, description="地点类别"),
    request: Request = None
):  
    config_json = get_config()
    url = "https://restapi.amap.com/v3/geocode/regeo"
    key = config_json.get("map_api_key", "your_api_key_here")
    params = {
        "location": f"{lng},{lat}",
        "key": key,
        "radius": radius,
        "poitype": category if category else None,
        "extensions": "all"
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data["regeocode"]["pois"]


@router.get("/api/navigation/locations/search")
async def get_nearby_locations(
    lat: float = Query(..., description="用户纬度"),
    lng: float = Query(..., description="用户经度"),
    radius: int = Query(2000, description="搜索半径（米）"),
    keywords: str = Query(None, description="关键词"),
    request: Request = None
):  
    config_json = get_config()
    url = "https://restapi.amap.com/v3/place/around"
    key = config_json.get("map_api_key", "your_api_key_here")
    params = {
        "location": f"{lng},{lat}",
        "key": key,
        "radius": radius,
        "keywords": keywords if keywords else None,
        "extensions": "all"
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data["regeocode"]["pois"]


@router.get("GET /api/navigation/locations/recommend")
async def get_nearby_locations(
    lat: float = Query(..., description="用户纬度"),
    lng: float = Query(..., description="用户经度"),
    radius: int = Query(2000, description="搜索半径（米）"),
    types: str = Query(None, description="种类（如餐饮、购物等）"),
    request: Request = None
):  
    config_json = get_config()
    url = "https://restapi.amap.com/v3/place/around"
    key = config_json.get("map_api_key", "your_api_key_here")
    params = {
        "location": f"{lng},{lat}",
        "key": key,
        "radius": radius,
        "types": types if types else None,
        "extensions": "all"
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data["regeocode"]["pois"]

@router.post("/api/navigation/location/user", response_model=UserLocationResponse)
async def update_user_location(
    body: UserLocationRequest,
    request: Request = None
):
    session = get_session(request)
    activity_id = body.user_id  # 实际应传递 activity_id

    record = session.get(ActivityLocation, activity_id)
    now = datetime.utcnow()
    user_found = False

    if record:
        # 查找 user_id 是否已存在
        for item in record.participants_location:
            if item["user_id"] == body.user_id:
                item["lat"] = body.location["lat"]
                item["lng"] = body.location["lng"]
                user_found = True
                break
        # 如果未找到，检查 Event 表
        if not user_found:
            event = session.get(Event, activity_id)
            if event and body.user_id in event.participants_id:
                record.participants_location.append({
                    "user_id": body.user_id,
                    "lat": body.location["lat"],
                    "lng": body.location["lng"]
                })
                user_found = True
        record.updated_at = now
    else:
        # 新建记录
        record = ActivityLocation(
            activity_id=activity_id,
            participants_location=[{
                "user_id": body.user_id,
                "lat": body.location["lat"],
                "lng": body.location["lng"]
            }],
            updated_at=now
        )
        session.add(record)
        user_found = True

    session.commit()

    return UserLocationResponse(
        user_id=body.user_id,
        status="location_updated" if user_found else "user_not_found",
        updated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ")
    )