from fastapi import FastAPI
from loguru import logger
from sqlalchemy.exc import OperationalError
from sqlmodel import Field, Session, SQLModel, create_engine
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import Column, JSON, DateTime, Float, Integer, String, select
import sys
from pathlib import Path

class Event(SQLModel, table=True):
    __tablename__ = "event"
    
    activity_id: str = Field(primary_key=True)
    owner_id: str
    participants_id: List[str] = Field(sa_column=Column(JSON))
    status: str
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    rating: Optional[float] = Field(sa_column=Column(Float))
    rating_id: List[str] = Field(sa_column=Column(JSON))

class EventContent(SQLModel, table=True):
    __tablename__ = "event_content"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: str = Field(foreign_key="event.activity_id")
    title: str
    description: str
    start_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    duration: Optional[float] = Field(sa_column=Column(Float))
    theme: str
    location: str
    budget: int
    group_size: int
    recommended_equipment: List[str] = Field(sa_column=Column(JSON))
    activity_tags: List[str] = Field(sa_column=Column(JSON))

class EventRating(SQLModel, table=True):
    __tablename__ = "event_rating"
    
    rating_id: str = Field(primary_key=True)
    status: str
    submitted_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    activity_id: str = Field(foreign_key="event.activity_id")
    rater_id: str
    comment: str

class PartnerRating(SQLModel, table=True):
    __tablename__ = "partner_rating"
    
    rating_id: str = Field(primary_key=True)
    status: str
    submitted_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    user_id: str
    tags: List[str] = Field(sa_column=Column(JSON))
    comment: str

class EventReview(SQLModel, table=True):
    __tablename__ = "event_review"
    
    review_id: str = Field(primary_key=True)
    status: str
    submitted_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    activity_id: str = Field(foreign_key="event.activity_id")
    reviewer_id: str
    comment: str


# 数据库生命周期管理
def init_database(app: FastAPI) -> None:
    """初始化数据库连接池并创建表结构"""
    # 获取并标准化路径
    database_path = "C:\Machine Files\event_management.db"
    db_path = Path(database_path).absolute()
    database_path = str(db_path)
    db_dir = db_path.parent
    
    # 1. 验证目录
    try:
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database directory: {db_dir}")
        
        # 测试目录可写性
        test_file = db_dir / "db_permission_test.tmp"
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        logger.critical(f"Directory error: {e}")
        logger.critical(f"请手动创建目录并设置权限: {db_dir}")
        sys.exit(1)
    
    # 2. 创建数据库引擎
    sqlite_url = f"sqlite:///{db_path}"
    
    # Windows 需要额外的连接参数
    connect_args = {}
    if sys.platform.startswith("win"):
        connect_args["check_same_thread"] = False
    
    engine = create_engine(
        sqlite_url,
        echo=False,
        connect_args=connect_args
    )
    
    # 3. 尝试创建数据库
    try:
        SQLModel.metadata.create_all(engine)
        logger.success(f"Database initialized at {db_path}")
    except OperationalError as e:
        logger.critical(f"无法打开数据库文件: {db_path}")
        logger.critical(f"错误详情: {e}")
        
        # 尝试创建空数据库文件
        try:
            logger.warning("尝试创建空数据库文件...")
            db_path.touch()
            SQLModel.metadata.create_all(engine)
            logger.warning("已创建新的空数据库文件")
        except Exception as e2:
            logger.critical(f"创建数据库文件失败: {e2}")
            logger.critical("请检查磁盘空间和文件权限")
            sys.exit(1)
    
    # 存储引擎引用
    app.state.engine = engine

async def shutdown_database(app: FastAPI) -> None:
    """
    关闭数据库连接
    
    :param app: FastAPI应用实例
    """
    engine = app.state.engine
    
    # 显式关闭连接池
    if engine:
        engine.dispose()
        logger.info("Database connection pool closed")
    
    # 清理应用状态
    app.state.engine = None

from fastapi import Request

def get_session(request: Request) -> Session:
    """
    获取数据库会话（用于依赖注入）
    
    :param request: FastAPI请求对象
    :return: SQLModel会话实例
    """
    engine = request.app.state.engine
    if not engine:
        raise RuntimeError("Database engine not initialized")
    
    return Session(engine)

# 在 __main__ 部分添加测试代码
if __name__ == "__main__":
    from sqlmodel import select  # 关键修复
    import asyncio 
    from fastapi import FastAPI, Request
    from datetime import datetime, UTC, timedelta 
    import uuid
    
    app = FastAPI()
    init_database(app)  # 初始化数据库
    async def main():
        # 创建模拟请求对象获取会话
        request = Request(scope={"type": "http", "app": app})
        session = get_session(request)

        # 测试1：插入完整活动数据流
        try:
            # 创建主活动记录
            activity_id = str(uuid.uuid4())
            event = Event(
                activity_id=activity_id,
                owner_id="user_001",
                participants_id=["user_002", "user_003"],
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(event)
            
            # 创建活动内容
            event_content = EventContent(
                activity_id=activity_id,
                title="周末登山活动",
                description="攀登西山观日出",
                start_time=datetime.utcnow() + timedelta(days=3),
                duration=4.5,
                theme="户外运动",
                location="西山森林公园",
                budget=500,
                group_size=15,
                recommended_equipment=["登山杖", "防晒霜"],
                activity_tags=["登山", "户外", "健身"]
            )
            session.add(event_content)
            
            # 创建活动评分
            rating_id = str(uuid.uuid4())
            event_rating = EventRating(
                rating_id=rating_id,
                status="submitted",
                submitted_at=datetime.utcnow(),
                activity_id=activity_id,
                rater_id="user_002",
                comment="组织有序，体验很棒！"
            )
            session.add(event_rating)
            
            # 更新主活动的评分信息
            event.rating = 4.8
            event.rating_id = [rating_id]
            
            session.commit()
            logger.success("测试1：活动数据流插入成功")
        except Exception as e:
            session.rollback()
            logger.error(f"测试1失败: {str(e)}")

        # 测试2：查询验证插入的数据
        try:
            # 验证主活动记录
            db_event = session.get(Event, activity_id)
            assert db_event is not None, "主活动记录未找到"
            logger.info(f"查询到活动: {db_event.activity_id} 状态: {db_event.status}")
            
            # 验证关联内容
            content = session.exec(
                select(EventContent).where(EventContent.activity_id == activity_id)
            ).first()
            assert content.title == "周末登山活动", "活动标题不匹配"
            logger.info(f"活动内容: {content.title} 地点: {content.location}")
            
            # 验证评分
            rating = session.get(EventRating, rating_id)
            assert rating.comment == "组织有序，体验很棒！", "评分内容不匹配"
            logger.info(f"活动评分: {rating.comment}")
            
            logger.success("测试2：数据查询验证通过")
        except Exception as e:
            logger.error(f"测试2失败: {str(e)}")

        # 测试3：插入伙伴评分
        try:
            partner_rating = PartnerRating(
                rating_id=str(uuid.uuid4()),
                status="approved",
                submitted_at=datetime.utcnow(),
                user_id="user_005",
                tags=["守时", "友好"],
                comment="非常可靠的登山伙伴"
            )
            session.add(partner_rating)
            session.commit()
            logger.success("测试3：伙伴评分插入成功")
        except Exception as e:
            session.rollback()
            logger.error(f"测试3失败: {str(e)}")

        # 测试4：JSON字段查询
        try:
            # 查询包含特定装备的活动
            results = session.exec(
                select(EventContent).where(
                    EventContent.recommended_equipment.contains(["登山杖"])
                )
            ).all()
            
            logger.info(f"找到 {len(results)} 个需要登山杖的活动")
            for r in results:
                logger.info(f"活动: {r.title} 装备: {r.recommended_equipment}")
            
            logger.success("测试4：JSON字段查询通过")
        except Exception as e:
            logger.error(f"测试4失败: {str(e)}")

        # 测试5：关联表更新操作
        try:
            # 更新活动状态
            db_event.status = "completed"
            db_event.updated_at = datetime.utcnow()
            
            # 添加活动回顾
            review = EventReview(
                review_id=str(uuid.uuid4()),
                status="published",
                submitted_at=datetime.utcnow(),
                activity_id=activity_id,
                reviewer_id="user_001",
                comment="本次活动圆满成功，感谢大家参与！"
            )
            session.add(review)
            session.commit()
            logger.success("测试5：关联表更新操作成功")
        except Exception as e:
            session.rollback()
            logger.error(f"测试5失败: {str(e)}")

        # 关闭数据库连接
        await shutdown_database(app)
    asyncio.run(main())
    logger.info("数据库生命周期管理模块已加载")