from fastapi import FastAPI
from loguru import logger
from sqlalchemy.exc import OperationalError
from sqlmodel import Field, Session, SQLModel, create_engine
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import Column, JSON, DateTime, Float, Integer, String, select
import sys
from pathlib import Path
from schema.database import ActivityMatch, MatchRecord, MatchFeedbackRecord 

# 数据库生命周期管理
def init_database(app: FastAPI) -> None:
    """初始化数据库连接池并创建表结构"""
    # 获取并标准化路径
    database_path = r"C:\Machine Files\matching_management.db"
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

if __name__ == "__main__":
    from sqlmodel import select  # 关键修复
    import asyncio 
    from fastapi import FastAPI, Request
    from datetime import datetime, UTC, timedelta 
    import uuid
    from schema.database import ActivityMatch, MatchRecord, MatchFeedbackRecord

    app = FastAPI()
    init_database(app)  # 初始化数据库
    async def main():
        # 创建模拟请求对象获取会话
        request = Request(scope={"type": "http", "app": app})
        session = get_session(request)

        # ...原有测试...

        # 测试6：插入和查询 ActivityMatch/MatchRecord/MatchFeedbackRecord
        try:
            match_id = str(uuid.uuid4())
            activity_id = str(uuid.uuid4())
            now = datetime.utcnow()

            # 插入 ActivityMatch
            match = ActivityMatch(
                match_id=match_id,
                activity_id=activity_id,
                status="pending",
                matched_candidates=["user_01", "user_02"],
                pending=["user_01"],
                accepted=[],
                rejected=[],
                updated_at=now
            )
            session.add(match)
            session.commit()

            # 插入 MatchRecord
            record = MatchRecord(
                match_id=match_id,
                action="created",
                updated_at=now
            )
            session.add(record)
            session.commit()

            # 插入 MatchFeedbackRecord
            fb = MatchFeedbackRecord(
                rater_id="user_01",
                match_id=match_id,
                rating=4.5,
                updated_at=now
            )
            session.add(fb)
            session.commit()

            # 查询验证
            db_match = session.get(ActivityMatch, match_id)
            assert db_match is not None, "ActivityMatch 未找到"
            logger.info(f"ActivityMatch: {db_match.match_id}, 状态: {db_match.status}")

            db_record = session.exec(select(MatchRecord).where(MatchRecord.match_id == match_id)).first()
            assert db_record is not None, "MatchRecord 未找到"
            logger.info(f"MatchRecord: {db_record.action}")

            db_fb = session.exec(select(MatchFeedbackRecord).where(MatchFeedbackRecord.match_id == match_id)).first()
            assert db_fb is not None, "MatchFeedbackRecord 未找到"
            logger.info(f"MatchFeedbackRecord: {db_fb.rating}")

            logger.success("测试6：匹配相关表插入和查询成功")
        except Exception as e:
            session.rollback()
            logger.error(f"测试6失败: {str(e)}")

        # 关闭数据库连接
        await shutdown_database(app)
    asyncio.run(main())
    logger.info("数据库生命周期管理模块已加载")