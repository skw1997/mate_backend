from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
import uuid
from database.lifetime import get_session, Event, EventContent
router = APIRouter()
from schema.navigation import LocationItem
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
    url = "https://restapi.amap.com/v3/place/text"
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

