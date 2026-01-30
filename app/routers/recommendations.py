from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from ..database import get_db
from ..models import UserBook
from ..auth import require_auth
from ..recommendation import (
    generate_recommendations,
    get_user_favorite_categories,
    get_user_favorite_authors
)
from ..book_apis import UnifiedBookAPI
from ..templating import templates

from ..config import settings

router = APIRouter()


GOOGLE_BOOKS_API_KEY = settings.GOOGLE_BOOKS_API_KEY


@router.get("/", response_class=HTMLResponse)
async def recommendations_page(request: Request, db: Session = Depends(get_db)):
    """Página de recomendações"""
    user = await require_auth(request, db)
    
    # Obter livros do usuário
    user_books = db.query(UserBook).filter(UserBook.user_id == user.id).all()
    
    if len(user_books) < 2:
        return templates.TemplateResponse("recommendations.html", {
            "request": request,
            "user": user,
            "recommendations": [],
            "message": "Adicione e avalie pelo menos 2 livros para receber recomendações!"
        })
    
    # Gerar recomendações
    recommendations = await get_recommendations(user_books, db)
    
    return templates.TemplateResponse("recommendations.html", {
        "request": request,
        "user": user,
        "recommendations": recommendations,
        "message": None
    })


@router.get("/content", response_class=HTMLResponse)
async def recommendations_content(request: Request, db: Session = Depends(get_db)):
    """Conteúdo de recomendações (HTMX)"""
    user = await require_auth(request, db)
    
    user_books = db.query(UserBook).filter(UserBook.user_id == user.id).all()
    
    if len(user_books) < 2:
        return templates.TemplateResponse("partials/recommendations_empty.html", {
            "request": request
        })
    
    recommendations = await get_recommendations(user_books, db)
    
    return templates.TemplateResponse("partials/recommendations_content.html", {
        "request": request,
        "recommendations": recommendations
    })


async def get_recommendations(user_books, db: Session):
    """Gera recomendações baseadas nos livros do usuário"""
    
    # Obter categorias e autores favoritos
    favorite_categories = get_user_favorite_categories(user_books)
    favorite_authors = get_user_favorite_authors(user_books)
    
    # Buscar candidatos usando API unificada
    candidate_books = []
    
    # Buscar por categorias favoritas (ambas APIs)
    for category in favorite_categories[:3]:
        try:
            books = UnifiedBookAPI.search_books(
                query=f'subject:{category}',
                sources=['google', 'openlibrary'],
                limit_per_source=8,
                google_api_key=GOOGLE_BOOKS_API_KEY
            )
            
            for book in books:
                # Verificar se já não está na biblioteca
                book_id = book['id']
                exists = any(b.book_id == book_id for b in user_books)
                
                if not exists:
                    candidate_books.append(book)
                    
        except Exception as e:
            print(f"Erro ao buscar categoria {category}: {e}")
            continue
    
    # Buscar por autores favoritos (ambas APIs)
    for author in favorite_authors[:2]:
        try:
            books = UnifiedBookAPI.search_books(
                query=f'author:{author}',
                sources=['google', 'openlibrary'],
                limit_per_source=5,
                google_api_key=GOOGLE_BOOKS_API_KEY
            )
            
            for book in books:
                book_id = book['id']
                exists = any(b.book_id == book_id for b in user_books)
                
                if not exists:
                    candidate_books.append(book)
                    
        except Exception as e:
            print(f"Erro ao buscar autor {author}: {e}")
            continue
    
    # Remover duplicatas
    seen_ids = set()
    unique_candidates = []
    for book in candidate_books:
        if book['id'] not in seen_ids:
            seen_ids.add(book['id'])
            unique_candidates.append(book)
    
    # Gerar recomendações com TF-IDF
    if unique_candidates:
        recommendations = generate_recommendations(
            user_books,
            unique_candidates,
            limit=12
        )
        return recommendations
    
    return []
