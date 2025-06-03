from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
import uuid
from database.lifetime import get_session, Event, EventContent
router = APIRouter()
from schema.activity import ActivityInputData, ActivityCreateRequest, GeneratedActivity, ActivityCreateResponse, ManualCreateRequest, ManualCreateResponse, ManualCreateRequirements, ActivityCardRequest, ActivityCardResponse, ActivityDetailRequest, ActivityDetailResponse, ActivityDetailRequirements, ActivityUpdateRequest, ActivityUpdateResponse, ActivityUpdateRequirements, ActivityFeedbackRequest, ActivityFeedbackResponse, FeedbackListResponse, FeedbackItem, ActivityHistoryItem, ActivityHistoryRequest, ActivityHistoryResponse
from schema.database import EventRating
from typing import List
from fastapi import Query

import random

@router.post("/api/activities/create", response_model=ActivityCreateResponse)
async def create_activity(request: Request, body: ActivityCreateRequest):
    # 1. 过滤和处理输入
    input_data = body.input_data

    # 2. 生成活动内容（此处为模拟，实际可接入AI/模板生成）
    # 生成活动ID和时间
    activity_id = f"a{uuid.uuid4().hex[:6]}"
    now = datetime.now(timezone(timedelta(hours=8)))  # 东八区
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    # 简单生成标题和描述
    title = f"{input_data.location}{input_data.theme}之旅"
    description = f"本次活动结合{input_data.location}的自然景观，为摄影爱好者提供捕捉秋日光影的机会。"
    recommended_equipment = ["单反相机", "三脚架"]

    # 3. 写入数据库
    session = get_session(request)
    try:
        # 主表
        event = Event(
            activity_id=activity_id,
            owner_id=body.user_id,
            participants_id=[body.user_id],
            status=input_data.status or "决定中",
            created_at=now,
            updated_at=now,
            rating=None,
            rating_id=[]
        )
        session.add(event)
        # 内容表
        event_content = EventContent(
            activity_id=activity_id,
            title=title,
            description=description,
            start_time=start_time,
            duration=None,  # 可根据 input_data.duration 解析
            theme=input_data.theme,
            location=input_data.location,
            budget=int(''.join(filter(str.isdigit, input_data.budget))),
            group_size=1,
            recommended_equipment=recommended_equipment,
            activity_tags=[input_data.theme]
        )
        session.add(event_content)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"活动创建失败: {str(e)}")

    # 4. 返回响应
    return ActivityCreateResponse(
        activity_id=activity_id,
        generated_activity=GeneratedActivity(
            title=title,
            description=description,
            start_time=start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
            recommended_equipment=recommended_equipment
        ),
        status="created",
        created_at=now.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    )


@router.post("/api/activities/manual-create", response_model=ManualCreateResponse)
async def manual_create_activity(request: Request, body: ManualCreateRequest):
    import uuid
    from datetime import datetime
    from dateutil import parser

    activity_id = f"a{uuid.uuid4()}"
    now = datetime.now()
    start_time = parser.parse(body.start_time)


   #title = AI.genete_title(body.title, body.description, body.theme, body.location)


    session = get_session(request)
    try:
        # 主表
        event = Event(
            activity_id=activity_id,
            owner_id=body.user_id,
            participants_id=[body.user_id],
            status="决定中",
            created_at=now,
            updated_at=now,
            rating=None,
            rating_id=[]
        )
        session.add(event)
        # 内容表
        event_content = EventContent(
            activity_id=activity_id,
            title=body.title,
            description=body.description,
            start_time=start_time,
            duration=None,
            theme=body.theme,
            location=body.location,
            budget=body.budget,
            group_size=body.requirements.group_size,
            recommended_equipment=[],
            activity_tags=body.requirements.activity_tags
        )
        session.add(event_content)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"活动创建失败: {str(e)}")

    return ManualCreateResponse(
        activity_id=activity_id,
        status="created",
        created_at=now.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    )


@router.post("/api/activities/{activity_id}/generate-card", response_model=ActivityCardResponse)
async def generate_activity_card(
    activity_id: str,
    body: ActivityCardRequest,
    request: Request
):
    session = get_session(request)
    event_content = session.query(EventContent).filter_by(activity_id=activity_id).first()
    if not event_content:
        raise HTTPException(status_code=404, detail="活动不存在")
    return ActivityCardResponse(
        activity_id=activity_id,
        title=event_content.title,
        location=event_content.location,
        start_time=event_content.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    )

@router.get("/api/activities/{activity_id}/details", response_model=ActivityDetailResponse)
async def get_activity_detail(
    activity_id: str,
    user_id: str = Query(...),
    token: str = Query(...),
    request: Request = None
):  
    print(f"Fetching details for activity_id: {activity_id}, user_id: {user_id}, token: {token}")
    session = get_session(request)
    event = session.query(Event).filter_by(activity_id=activity_id).first()
    event_content = session.query(EventContent).filter_by(activity_id=activity_id).first()
    if not event or not event_content:
        raise HTTPException(status_code=404, detail="活动不存在")

    # 组装 requirements
    requirements = ActivityDetailRequirements(
        group_size=str(event_content.group_size) if hasattr(event_content, "group_size") else "",
        activity_tags=event_content.activity_tags if hasattr(event_content, "activity_tags") else [],
        recommended_equipment=event_content.recommended_equipment if hasattr(event_content, "recommended_equipment") else []
    )

    return ActivityDetailResponse(
        activity_id=activity_id,
        title=event_content.title,
        description=event_content.description,
        theme=event_content.theme,
        location=event_content.location,
        budget=f"{event_content.budget}元",
        start_time=event_content.start_time.strftime("%Y-%m-%dT%H:%M:%SZ") if event_content.start_time else "",
        duration=str(event_content.duration) if event_content.duration else "",
        status=event.status,
        requirements=requirements,
        participants=event.participants_id if hasattr(event, "participants_id") else [],
        created_at=event.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if event.created_at else "",
        last_updated=event.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if event.updated_at else ""
    )

@router.put("/api/activities/{activity_id}/update", response_model=ActivityUpdateResponse)
async def update_activity(
    activity_id: str,
    body: ActivityUpdateRequest,
    request: Request
):
    session = get_session(request)
    event = session.query(Event).filter_by(activity_id=activity_id).first()
    event_content = session.query(EventContent).filter_by(activity_id=activity_id).first()
    if not event or not event_content:
        raise HTTPException(status_code=404, detail="活动不存在")

    try:
        # 更新主表
        if body.activity_title:
            event_content.title = body.activity_title
        if body.description:
            event_content.description = body.description
        if body.theme:
            event_content.theme = body.theme
        if body.location:
            event_content.location = body.location
        if body.budget is not None:
            event_content.budget = body.budget
        if body.start_time:
            from dateutil import parser
            event_content.start_time = parser.parse(body.start_time)
        if body.duration is not None:
            event_content.duration = body.duration
        if body.requirements:
            if body.requirements.group_size is not None:
                event_content.group_size = body.requirements.group_size
            if body.requirements.activity_tags is not None:
                event_content.activity_tags = body.requirements.activity_tags

        # 更新时间
        now = datetime.now()
        event.updated_at = now

        session.commit()
        feedback = "success"
    except Exception as e:
        session.rollback()
        feedback = "fail"

    return ActivityUpdateResponse(
        activity_id=activity_id,
        feedback=feedback,
        updated_at=event.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%f%z") if event.updated_at else ""
    )

@router.post("/api/activities/{activity_id}/feedback", response_model=ActivityFeedbackResponse)
async def submit_activity_feedback(
    activity_id: str,
    body: ActivityFeedbackRequest,
    request: Request
):
    from datetime import datetime
    import random

    session = get_session(request)
    event = session.query(Event).filter_by(activity_id=activity_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="活动不存在")

    existing_rating = session.query(EventRating).filter_by(activity_id=activity_id, rater_id=body.user_id).first()
    if existing_rating:
        raise HTTPException(status_code=400, detail="同一个用户不能对同一个活动重复评论")

    # 生成唯一 rating_id
    rating_id = f"f{random.getrandbits(16):04x}"

    now = datetime.now()
    # 写入 EventRating

    event_rating = EventRating(
        rating_id=rating_id,
        status="submitted",
        submitted_at=now,
        activity_id=activity_id,
        rating=body.rating,
        rater_id=body.user_id,
        comment=body.comment
    )
    session.add(event_rating)

    # 更新活动评分（可选：简单平均或覆盖）
    all_ratings = session.query(EventRating).filter_by(activity_id=activity_id).all()
    if all_ratings:
        avg_rating = sum(r.rating for r in all_ratings if hasattr(r, "rating") and r.rating is not None) / len(all_ratings)
        event.rating = avg_rating
    else:
        event.rating = body.rating
    session.commit()

    return ActivityFeedbackResponse(
        activity_id=activity_id,
        rating_id=rating_id,
        status="submitted",
        submitted_at=now.strftime("%Y-%m-%dT%H:%M:%SZ")
    )


@router.get("/api/activities/{activity_id}/feedback_list", response_model=FeedbackListResponse)
async def get_activity_feedback_list(
    activity_id: str,
    user_id: str = Query(...),
    token: str = Query(...),
    request: Request = None
):
    session = get_session(request)
    feedbacks = session.query(EventRating).filter_by(activity_id=activity_id).all()
    feedback_items = [
        FeedbackItem(
            feedback_id=f.rating_id,
            rating=f.rating,
            comment=f.comment,
            submitted_at=f.submitted_at.strftime("%Y-%m-%dT%H:%M:%SZ") if f.submitted_at else ""
        )
        for f in feedbacks
    ]
    return FeedbackListResponse(
        activity_id=activity_id,
        feedbacks=feedback_items
    )


@router.get("/api/activities/history", response_model=ActivityHistoryResponse)
async def get_user_activity_history(
    user_id: str = Query(...),
    token: str = Query(...),
    request: Request = None
):
    session = get_session(request)

    # 查询用户创建的活动
    created_events = session.query(Event).filter_by(owner_id=user_id).all()
    created_history = [
        ActivityHistoryItem(
            activity_id=e.activity_id,
            status="created",
            timestamp=e.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if e.created_at else ""
        )
        for e in created_events
    ]

    # 查询用户参与的活动（不包括自己创建的）
    joined_events = session.query(Event).filter(Event.participants_id.contains([user_id]), Event.owner_id != user_id).all()
    joined_history = [
        ActivityHistoryItem(
            activity_id=e.activity_id,
            status="joined",
            timestamp=e.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if e.created_at else ""
        )
        for e in joined_events
    ]

    return ActivityHistoryResponse(
        user_id=user_id,
        history=created_history + joined_history
    )