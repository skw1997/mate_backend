from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
from database.lifetime import get_session, Event
router = APIRouter()
from schema.activity_admin import PendingActivitiesResponse, PendingActivityItem, AdminActivityUpdateRequest, AdminActivityUpdateResponse
from schema.database import Event, AdminActivityAction
from fastapi import Query


from schema.activity_admin import PendingActivitiesResponse, PendingActivityItem

@router.get("/api/admin/activities/pending", response_model=PendingActivitiesResponse)
async def get_pending_activities(
    request: Request,
    user_id: str = Query(...),
    token: str = Query(...)
):
    session = get_session(request)
    # 查询所有待审核活动
    pending_events = session.query(Event).filter_by(status="pending").all()
    pending_activities = []
    for event in pending_events:
        pending_activities.append(
            PendingActivityItem(
                activity_id=event.activity_id,
                owner_id=event.owner_id,
                submitted_at=event.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if event.created_at else "",
                status=event.status
            )
        )
    return PendingActivitiesResponse(pending_activities=pending_activities)



@router.post("/api/admin/activities/update", response_model=AdminActivityUpdateResponse)
async def admin_update_activity(
    body: AdminActivityUpdateRequest,
    request: Request
):
    session = get_session(request)
    event = session.query(Event).filter_by(activity_id=body.activity_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="活动不存在")


    now = datetime.utcnow()
    try:
        # 只更新event中的status
        event.status = body.status
        event.updated_at = now

        # 新增一条AdminActivityAction记录
        admin_action = AdminActivityAction(
            activity_id=body.activity_id,
            reviewer_id=body.reviewer_id,
            decision=body.status,
            comment=body.comment,
            operated_at=now
        )
        session.add(admin_action)

        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")

    return AdminActivityUpdateResponse(
        activity_id=body.activity_id,
        new_status=body.status,
        reviewed_at=now.strftime("%Y-%m-%dT%H:%M:%SZ")
    )