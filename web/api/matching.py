from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
import uuid
from database.lifetime import get_session, Event
router = APIRouter()
from schema.matching import MatchCandidatesRequest, MatchCandidatesResponse, MatchedCandidate, MatchRecordQueryRequest, MatchRecordQueryResponse, MatchFeedbackRequest, MatchFeedbackResponse
from schema.database import Event, ActivityMatch
from fastapi import Query


from schema.matching import PendingActivitiesResponse, PendingActivityItem


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
    user_accepted = [c.user_id for c in matched_candidates]
    user_rejected = [c.user_id for c in matched_candidates]
    now = datetime.utcnow()
    match_id = str(uuid.uuid4())

    # 保存到数据库
    match = ActivityMatch(
        match_id=match_id,
        activity_id=activity_id,
        status="matching_completed",
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
    match = session.query(ActivityMatch).filter_by(activity_id=activity_id).order_by(ActivityMatch.updated_at.desc()).first()
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