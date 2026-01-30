import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Imports da aplicação
from app.database import engine, get_db, Base
from app.models import User, UserBook
from app.auth import get_current_user_from_cookie, create_access_token, verify_password, get_password_hash
from app.routers import books, recommendations


BASE_DIR = Path(__file__).resolve().parent

# Caminhos absolutos dinâmicos
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Criar tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BookBrain Modern")

# Configurar arquivos estáticos (com verificação de segurança)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
else:
    print(f"⚠️ AVISO: Pasta 'static' não encontrada em: {STATIC_DIR}")

# Configurar templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Incluir routers
app.include_router(books.router, prefix="/books", tags=["books"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Página inicial - redireciona para login ou dashboard"""
    user = await get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Processar login"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not verify_password(password, user.password_hash):
        # Certifique-se que o arquivo partials/login_error.html existe
        return templates.TemplateResponse(
            "partials/login_error.html",
            {"request": request, "error": "Usuário ou senha inválidos"},
            headers={"HX-Retarget": "#login-error", "HX-Reswap": "innerHTML"}
        )
    
    token = create_access_token({"sub": user.username})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Página de registro"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Processar registro"""
    # Verificar se usuário já existe
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse(
            "partials/register_error.html",
            {"request": request, "error": "Nome de usuário já existe"},
            headers={"HX-Retarget": "#register-error", "HX-Reswap": "innerHTML"}
        )
    
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse(
            "partials/register_error.html",
            {"request": request, "error": "Email já cadastrado"},
            headers={"HX-Retarget": "#register-error", "HX-Reswap": "innerHTML"}
        )
    
    # Criar novo usuário
    new_user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password)
    )
    db.add(new_user)
    db.commit()
    
    # Fazer login automático
    token = create_access_token({"sub": username})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard principal"""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Estatísticas
    total_books = db.query(UserBook).filter(UserBook.user_id == user.id).count()
    reading = db.query(UserBook).filter(
        UserBook.user_id == user.id,
        UserBook.status == "reading"
    ).count()
    finished = db.query(UserBook).filter(
        UserBook.user_id == user.id,
        UserBook.status == "finished"
    ).count()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "total_books": total_books,
        "reading": reading,
        "finished": finished
    })


@app.post("/logout")
async def logout():
    """Logout"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)