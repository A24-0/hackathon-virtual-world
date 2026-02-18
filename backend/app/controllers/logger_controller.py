from fastapi import APIRouter, Query
from datetime import datetime, timedelta

from app.models.log import Log, LogLevel, LogCategory
from app.schemas.schemas import LogResponse, LogListResponse, LogStats

router = APIRouter(prefix="/logs", tags=["Logger"])


def to_resp(l: Log) -> LogResponse:
    return LogResponse(
        id=str(l.id), level=l.level, category=l.category,
        message=l.message, agent_id=l.agent_id,
        agent_name=l.agent_name, details=l.details, timestamp=l.timestamp,
    )


@router.get("/", response_model=LogListResponse)
async def get_logs(level: LogLevel | None = None, category: LogCategory | None = None,
                   agent_id: str | None = None, skip: int = 0, limit: int = 50):
    q = {}
    if level: q["level"] = level.value
    if category: q["category"] = category.value
    if agent_id: q["agent_id"] = agent_id

    logs = await Log.find(q).sort("-timestamp").skip(skip).limit(limit).to_list()
    total = await Log.find(q).count()
    return LogListResponse(logs=[to_resp(l) for l in logs], total=total)


@router.get("/errors", response_model=LogListResponse)
async def errors(skip: int = 0, limit: int = 50):
    q = {"level": {"$in": [LogLevel.ERROR.value, LogLevel.CRITICAL.value]}}
    logs = await Log.find(q).sort("-timestamp").skip(skip).limit(limit).to_list()
    total = await Log.find(q).count()
    return LogListResponse(logs=[to_resp(l) for l in logs], total=total)


@router.get("/agent/{agent_id}", response_model=LogListResponse)
async def agent_logs(agent_id: str, skip: int = 0, limit: int = 50):
    logs = await Log.find({"agent_id": agent_id}).sort("-timestamp").skip(skip).limit(limit).to_list()
    total = await Log.find({"agent_id": agent_id}).count()
    return LogListResponse(logs=[to_resp(l) for l in logs], total=total)


@router.get("/stats", response_model=LogStats)
async def stats():
    total = await Log.count()

    by_level = {}
    for lvl in LogLevel:
        c = await Log.find({"level": lvl.value}).count()
        if c: by_level[lvl.value] = c

    by_cat = {}
    for cat in LogCategory:
        c = await Log.find({"category": cat.value}).count()
        if c: by_cat[cat.value] = c

    last_err = None
    errs = await Log.find({"level": {"$in": ["error", "critical"]}}).sort("-timestamp").limit(1).to_list()
    if errs:
        last_err = to_resp(errs[0])

    return LogStats(total_logs=total, by_level=by_level, by_category=by_cat, last_error=last_err)


@router.delete("/clear")
async def clear_old(days: int = Query(7, ge=1)):
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await Log.find({"timestamp": {"$lt": cutoff}}).delete()
    return {"deleted": result.deleted_count if result else 0}


@router.delete("/clear-all")
async def clear_all():
    result = await Log.find({}).delete()
    return {"deleted": result.deleted_count if result else 0}
