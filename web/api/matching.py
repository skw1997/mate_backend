from fastapi import APIRouter, Body, HTTPException, Request
from datetime import datetime
import uuid
from sqlalchemy.orm.attributes import flag_modified
from database.lifetime import get_session
router = APIRouter()
from schema.matching import *
from schema.database import ActivityMatch, MatchFeedbackRecord
from fastapi import Query


@router.post("/api/match/activities/{activity_id}/match-candidates", response_model=MatchCandidatesResponse)
async def match_candidates(
    activity_id: str,
    body: MatchCandidatesRequest,
    request: Request
):
    session = get_session(request)

    # 这里应有实际的匹配逻辑，下面为演示用的假数据
    matched_candidates = [
        MatchedCandidate(user_id="u67890", similarity_score=0.92),
        MatchedCandidate(user_id="u54321", similarity_score=0.87)
    ]
    user_pending = [c.user_id for c in matched_candidates]
    user_accepted = []
    user_rejected = []
    now = datetime.utcnow()
    match_id = str(uuid.uuid4())

    # 保存到数据库
    match = ActivityMatch(
        match_id=match_id,
        activity_id=activity_id,
        status="matching",
        matched_candidates=user_pending,
        pending=user_pending,
        accepted=user_accepted,
        rejected=user_rejected,
        updated_at=now
    )
    session.add(match)
    session.commit()

    return MatchCandidatesResponse(
        activity_id=activity_id,
        match_id=match_id,
        matched_candidates=matched_candidates,
        user_pending=user_pending,
        user_accepted=user_accepted,
        user_rejected=user_rejected,
        matched_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        status="matching_completed"
    )

@router.get("/api/match/activities/{activity_id}/records", response_model=MatchRecordQueryResponse)
async def get_match_record(
    activity_id: str,
    user_id: str = Query(...),
    token: str = Query(...),
    request: Request = None
):
    session = get_session(request)
    match = session.query(ActivityMatch).filter(activity_id == activity_id).order_by(ActivityMatch.updated_at.desc()).first()
    if not match:
        raise HTTPException(status_code=404, detail="未找到匹配记录")

    # 假设你有保存 similarity_score，若没有可用默认值
    matched_candidates = [
        MatchedCandidate(user_id=uid, similarity_score=0.0) for uid in match.matched_candidates
    ]

    return MatchRecordQueryResponse(
        activity_id=activity_id,
        match_record_id=match.match_id,
        matched_candidates=matched_candidates,
        user_pending=match.pending,
        user_accepted=match.accepted,
        user_rejected=match.rejected,
        matched_at=match.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        status=match.status
    )


@router.post("/api/match/activities/{activity_id}/feedback", response_model=MatchFeedbackResponse)
async def submit_match_feedback(
    activity_id: str,
    body: MatchFeedbackRequest,
    request: Request
):
    session = get_session(request)
    from schema.database import MatchFeedbackRecord
    from datetime import datetime

    # 保存反馈到数据库
    feedback_record = MatchFeedbackRecord(
        rater_id=body.user_id,
        match_id=body.match_id,
        rating=body.rating,
        updated_at=datetime.utcnow()
    )
    session.add(feedback_record)
    session.commit()

    return MatchFeedbackResponse(
        activity_id=activity_id,
        message="OK"
    )


@router.get("/api/match/status", response_model=MatchStatusResponse)
async def get_match_status(
    activity_id: str = Query(...),
    user_id: str = Query(...),
    token: str = Query(...),
    request: Request = None
):
    session = get_session(request)
    match = session.query(ActivityMatch).filter(activity_id=activity_id).order_by(ActivityMatch.updated_at.desc()).first()
    if not match:
        raise HTTPException(status_code=404, detail="未找到匹配记录")

    # 这里假设 status 字段即为 matching_status
    matching_status = match.status
    current_candidates_count = len(match.matched_candidates) if match.matched_candidates else 0

    return MatchStatusResponse(
        activity_id=activity_id,
        user_id=user_id,
        matching_status=matching_status,
        current_candidates_count=current_candidates_count
    )



@router.post("/api/match/update", response_model=MatchUpdateResponse)
async def update_match_status(
    body: MatchUpdateRequest = Body(...),
    request: Request = None
):
    session = get_session(request)
    print(body.activity_id)
    match = session.query(ActivityMatch).filter(ActivityMatch.activity_id == body.activity_id).order_by(ActivityMatch.updated_at.desc()).first()

    if not match:
        raise HTTPException(status_code=404, detail="未找到匹配记录")
    # 更新状态
    if body.action not in ["cancelled", "paused"]:
        raise HTTPException(status_code=400, detail="无效的操作类型")
    match.status = body.action
    match.updated_at = datetime.utcnow()
    session.add(match)
    session.commit()
    return MatchUpdateResponse(
        activity_id=body.activity_id,
        status=body.action,
        timestamp=match.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    )


@router.post("/api/match/notifications/action", response_model=MatchNotificationActionResponse)
async def match_notification_action(
    body: MatchNotificationActionRequest = Body(...),
    request: Request = None
):
    session = get_session(request)
    match = session.query(ActivityMatch).filter_by(match_id=body.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="未找到匹配记录")

    if body.response == "accept":
        if body.user_id in match.pending:
            match.pending.remove(body.user_id)
        if body.user_id not in match.accepted:
            match.accepted.append(body.user_id)
        match.pending = list(match.pending)
        match.accepted = list(match.accepted)
        flag_modified(match, "pending")
        flag_modified(match, "accepted")
    elif body.response == "reject":
        if body.user_id in match.pending:
            match.pending.remove(body.user_id)
        if body.user_id not in match.rejected:
            match.rejected.append(body.user_id)
        match.pending = list(match.pending)
        match.rejected = list(match.rejected)
        flag_modified(match, "pending")
        flag_modified(match, "rejected")
    else:
        raise HTTPException(status_code=400, detail="无效的响应类型")
    match.updated_at = datetime.utcnow()
    session.commit()

    return MatchNotificationActionResponse(
        match_id=body.match_id,
        message="OK"
    )

