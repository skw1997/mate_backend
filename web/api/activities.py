from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
import uuid
from database.lifetime import get_session, Event, EventContent
router = APIRouter()
from schema.activity import ActivityInputData, ActivityCreateRequest, GeneratedActivity, ActivityCreateResponse


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