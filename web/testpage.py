# main.py
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database.lifetime import init_database, shutdown_database
from web.api import activities
app = FastAPI()
templates = Jinja2Templates(directory="web/templates")

# 全局变量初始化（在 startup 事件中赋值）
app.state.welcome_message = None

# 注册 startup 事件[1,11](@ref)
@app.on_event("startup")
async def init_app():
    """应用启动时初始化全局数据"""
    app.state.welcome_message = "欢迎访问 FastAPI 网页！"
    init_database(app)  # 初始化数据库连接
    print("✅ 数据库连接已初始化")

    print("✅ 应用启动完成，全局变量已初始化")

# 网页路由
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """渲染首页模板并传递全局变量"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "message": app.state.welcome_message,  # 使用 startup 初始化的数据
            "now": lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 添加 now 函数
        }
    )

app.include_router(activities.router)