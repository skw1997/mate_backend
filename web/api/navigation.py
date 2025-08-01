from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
import uuid
from database.lifetime import get_session, Event, EventContent
from fastapi.responses import Response
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter()
from schema.navigation import (
    LocationItem,
    UserLocationRequest,
    UserLocationResponse,
    UserLocationStopRequest,
    UserLocationStopResponse,
)
from schema.database import ActivityLocation
from typing import List
from fastapi import Query
from dateutil import parser
import random
import requests
import json
import os

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "navigation.json"
)


def get_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/api/navigation/locations/nearby")
async def get_nearby_locations(
    lat: float = Query(..., description="用户纬度"),
    lng: float = Query(..., description="用户经度"),
    radius: int = Query(2000, description="搜索半径（米）"),
    category: str = Query(None, description="地点类别"),
    request: Request = None,
):
    config_json = get_config()
    url = "https://restapi.amap.com/v3/geocode/regeo"
    key = config_json.get("map_api_key", "your_api_key_here")
    params = {
        "location": f"{lng},{lat}",
        "key": key,
        "radius": radius,
        "poitype": category if category else None,
        "extensions": "all",
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
    request: Request = None,
):
    config_json = get_config()
    url = "https://restapi.amap.com/v3/place/around"
    key = config_json.get("map_api_key", "your_api_key_here")
    params = {
        "location": f"{lng},{lat}",
        "key": key,
        "radius": radius,
        "keywords": keywords if keywords else None,
        "extensions": "all",
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
    request: Request = None,
):
    config_json = get_config()
    url = "https://restapi.amap.com/v3/place/around"
    key = config_json.get("map_api_key", "your_api_key_here")
    params = {
        "location": f"{lng},{lat}",
        "key": key,
        "radius": radius,
        "types": types if types else None,
        "extensions": "all",
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data["regeocode"]["pois"]


@router.post("/api/navigation/location/user", response_model=UserLocationResponse)
async def update_user_location(body: UserLocationRequest, request: Request = None):
    session = get_session(request)
    activity_id = body.activity_id
    user_id = body.user_id

    record = session.get(ActivityLocation, activity_id)
    event = session.get(Event, activity_id)
    now = datetime.utcnow()
    user_found = False
    if event:
        if record:
            # 查找 user_id 是否已存在
            for item in record.participants_location:
                if item["user_id"] == user_id:
                    item["lat"] = body.location["lat"]
                    item["lng"] = body.location["lng"]
                    user_found = True
                    break
            # 如果未找到，检查 Event 表
            if not user_found:
                if user_id in event.participants_id:
                    record.participants_location.append(
                        {
                            "user_id": user_id,
                            "lat": body.location["lat"],
                            "lng": body.location["lng"],
                        }
                    )
                    user_found = True
            record.updated_at = now
            flag_modified(record, "participants_location")  # 强制标记为已修改
        else:
            # 新建记录
            record = ActivityLocation(
                activity_id=activity_id,
                participants_location=[
                    {
                        "user_id": user_id,
                        "lat": body.location["lat"],
                        "lng": body.location["lng"],
                    }
                ],
                updated_at=now,
            )
            session.add(record)
        session.commit()
    else:
        raise HTTPException(
            status_code=404, detail=f"Activity with ID {activity_id} not found"
        )
    return UserLocationResponse(
        user_id=user_id,
        activity_id=activity_id,
        status="location_updated" if user_found else "user_not_found",
        updated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


@router.post(
    "/api/navigation/location/user/stop", response_model=UserLocationStopResponse
)
async def stop_user_location_sharing(
    body: UserLocationStopRequest, request: Request = None
):
    session = get_session(request)
    record = session.get(ActivityLocation, body.activity_id)
    now = datetime.utcnow()
    if record:
        before = len(record.participants_location)
        record.participants_location = [
            item
            for item in record.participants_location
            if item["user_id"] != body.user_id
        ]
        if len(record.participants_location) < before:
            record.updated_at = now
            session.commit()
    return UserLocationStopResponse(
        user_id=body.user_id,
        activity_id=body.activity_id,
        stopped_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


@router.get("/api/navigation/location/activity")
async def get_activity_location_map(
    activity_id: str,
    user_id: str = None,
    token: str = None,
    request: Request = None,
):
    session = get_session(request)
    record = session.get(ActivityLocation, activity_id)
    if not record or not record.participants_location:
        raise HTTPException(status_code=404, detail="No location data found")

    def get_url(key):
        return "http://47.99.53.24:8000/i/3cc893a5-cc05-42a5-8bf5-da47b45b637e.png"

    config_json = get_config()
    key = config_json.get("map_api_key", "your_api_key_here")
    markers = "|".join(
        f'-1,{get_url(item["user_id"])},0:{item["lat"]},{item["lng"]}'
        for item in record.participants_location
    )
    marker_param = f"markers={markers}"

    user_location = None
    for item in record.participants_location:
        if item["user_id"] == user_id:
            user_location = item
            break
    if not user_location:
        raise HTTPException(status_code=404, detail="User location not found")

    url = (
        f"https://restapi.amap.com/v3/staticmap?"
        f"location={user_location['lat']},{user_location['lng']}"
        f"&size=750*750"
        f"&{marker_param}"
        f"&key={key}"
    )
    print("Request URL:", url)
    amap_response = requests.get(url)
    content_type = amap_response.headers.get("Content-Type", "")
    if (
        content_type.lower() != "image/png"
        and content_type.lower() != "image/png;charset=utf-8"
    ):
        # 返回高德错误信息
        try:
            error_json = amap_response.json()
        except Exception:
            error_json = {"detail": "高德地图API请求失败", "content_type": content_type}
        raise HTTPException(status_code=502, detail=error_json)
    if amap_response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch map image")

    return Response(
        content=amap_response.content,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="{activity_id}.png"'},
    )
