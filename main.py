from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import logging
from database import db

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WebCinema")

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Сессии (простое хранилище)
sessions = {}

# Вспомогательные функции
def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        return sessions[session_id]
    return None

# ========== СТРАНИЦЫ ==========

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/schedule", response_class=HTMLResponse)
async def schedule(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Панель администратора"""
    user = get_current_user(request)
    if not user or user['role'] != 'admin':
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("admin/panel.html", {"request": request})

@app.get("/admin/movies", response_class=HTMLResponse)
async def admin_movies(request: Request):
    """Управление фильмами"""
    user = get_current_user(request)
    if not user or user['role'] != 'admin':
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("admin/movies.html", {"request": request})

@app.get("/admin/sessions", response_class=HTMLResponse)
async def admin_sessions(request: Request):
    """Управление сеансами"""
    user = get_current_user(request)
    if not user or user['role'] != 'admin':
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("admin/sessions.html", {"request": request})

@app.get("/admin/tariffs", response_class=HTMLResponse)
async def admin_tariffs(request: Request):
    """Управление ценами"""
    user = get_current_user(request)
    if not user or user['role'] != 'admin':
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("admin/tariffs.html", {"request": request})

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    """Управление пользователями"""
    user = get_current_user(request)
    if not user or user['role'] != 'admin':
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("admin/users.html", {"request": request})

@app.get("/cashier", response_class=HTMLResponse)
async def cashier_panel(request: Request):
    """Панель кассира"""
    user = get_current_user(request)
    if not user or user['role'] not in ['admin', 'cashier']:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("cashier/panel.html", {"request": request})

@app.get("/cashier/sales", response_class=HTMLResponse)
async def cashier_sales(request: Request):
    """Продажа билетов"""
    user = get_current_user(request)
    if not user or user['role'] not in ['admin', 'cashier']:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("cashier/sales.html", {"request": request})

@app.get("/cashier/hall/{session_id}", response_class=HTMLResponse)
async def cashier_hall(request: Request, session_id: int):
    """Схема зала"""
    user = get_current_user(request)
    if not user or user['role'] not in ['admin', 'cashier']:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("cashier/hall.html", {
        "request": request,
        "session_id": session_id
    })

@app.get("/cashier/checkout", response_class=HTMLResponse)
async def cashier_checkout(request: Request):
    """Оформление продажи"""
    user = get_current_user(request)
    if not user or user['role'] not in ['admin', 'cashier']:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("cashier/checkout.html", {"request": request})

@app.get("/cashier/returns", response_class=HTMLResponse)
async def cashier_returns(request: Request):
    """Возврат билетов"""
    user = get_current_user(request)
    if not user or user['role'] not in ['admin', 'cashier']:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("cashier/returns.html", {"request": request})

# ========== API ==========

@app.get("/api/movies")
async def get_movies():
    """Получение списка фильмов"""
    try:
        movies = db.get_movies()
        logger.info(f"GET /api/movies: {len(movies)} фильмов")
        return JSONResponse(content=movies)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return JSONResponse(content=[], status_code=500)

@app.post("/api/movies/update/{movie_id}")
async def update_movie(request: Request, movie_id: int):
    """Обновление фильма"""
    try:
        data = await request.json()
        query = """
            UPDATE movies 
            SET title = %s, duration = %s, genre = %s, age_rating = %s
            WHERE id = %s
        """
        result = db.execute_query(query, (
            data['title'], data['duration'],
            data['genre'], data['age_rating'],
            movie_id
        ))
        return {"success": result > 0}
    except Exception as e:
        logger.error(f"Ошибка обновления фильма: {e}")
        return {"success": False}

@app.get("/api/all_movies")
async def get_all_movies():
    """Получение всех фильмов (для страницы Все фильмы)"""
    try:
        movies = db.get_movies()
        return JSONResponse(content=movies)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return JSONResponse(content=[])

@app.get("/api/sessions")
async def get_sessions():
    """Получение списка сеансов"""
    try:
        sessions = db.get_sessions()
        logger.info(f"GET /api/sessions: {len(sessions)} сеансов")
        return JSONResponse(content=sessions)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return JSONResponse(content=[], status_code=500)

@app.get("/api/session/{session_id}")
async def get_session(session_id: int):
    """Получение информации о сеансе"""
    try:
        session = db.get_session_by_id(session_id)
        return JSONResponse(content=session)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return JSONResponse(content=None, status_code=500)

@app.get("/api/seats/{hall_id}")
async def get_seats(hall_id: int):
    """Получение схемы зала"""
    try:
        seats = db.get_seats(hall_id)
        return JSONResponse(content=seats)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return JSONResponse(content=[], status_code=500)

@app.get("/api/tariffs")
async def get_tariffs():
    """Получение списка тарифов"""
    try:
        tariffs = db.get_tariffs()
        return JSONResponse(content=tariffs)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return JSONResponse(content=[], status_code=500)

@app.get("/api/tickets/{session_id}")
async def get_tickets(session_id: int):
    """Получение проданных билетов"""
    try:
        tickets = db.get_sold_tickets(session_id)
        return JSONResponse(content=tickets)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return JSONResponse(content=[], status_code=500)

@app.post("/api/login")
async def login(request: Request):
    """Авторизация"""
    try:
        data = await request.json()
        user = db.authenticate(data['username'], data['password'])
        if user:
            import uuid
            session_id = str(uuid.uuid4())
            sessions[session_id] = dict(user)
            response = JSONResponse({"success": True, "user": user})
            response.set_cookie(key="session_id", value=session_id)
            return response
        return JSONResponse({"success": False, "error": "Неверный логин или пароль"})
    except Exception as e:
        logger.error(f"Ошибка авторизации: {e}")
        return JSONResponse({"success": False, "error": str(e)})

@app.get("/api/logout")
async def logout(request: Request):
    """Выход"""
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        del sessions[session_id]
    response = RedirectResponse(url="/")
    response.delete_cookie("session_id")
    return response

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )