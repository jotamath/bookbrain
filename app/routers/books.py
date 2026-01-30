from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import UserBook, User
from ..auth import require_auth
from ..book_apis import UnifiedBookAPI
from ..templating import templates

router = APIRouter()

GOOGLE_BOOKS_API_KEY = settings.GOOGLE_BOOKS_API_KEY

@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, db: Session = Depends(get_db)):
    # Página de busca
    user = await require_auth(request, db)
    return templates.TemplateResponse("search.html", {
        "request": request,
        "user": user
    })


@router.get("/search-results", response_class=HTMLResponse)
async def search_books(
    request: Request,
    q: str,
    source: str = "all",  # all, google, openlibrary
    db: Session = Depends(get_db)
):
    """Buscar livros (retorna HTML)"""
    user = await require_auth(request, db)
    
    if not q or len(q.strip()) < 2:
        return templates.TemplateResponse("partials/search_results.html", {
            "request": request,
            "books": [],
            "error": "Digite pelo menos 2 caracteres"
        })
    
    try:
        # Definir fontes de busca
        sources = []
        if source == "all":
            sources = ['google', 'openlibrary']
        elif source == "google":
            sources = ['google']
        elif source == "openlibrary":
            sources = ['openlibrary']
        else:
            sources = ['google', 'openlibrary']
        
        # Buscar usando API unificada
        books = UnifiedBookAPI.search_books(
            query=q,
            sources=sources,
            limit_per_source=15,
            google_api_key=GOOGLE_BOOKS_API_KEY
        )
        
        # Verificar quais livros já estão na biblioteca
        for book in books:
            existing = db.query(UserBook).filter(
                UserBook.user_id == user.id,
                UserBook.book_id == book['id']
            ).first()
            book['in_library'] = existing is not None
        
        return templates.TemplateResponse("partials/search_results.html", {
            "request": request,
            "books": books,
            "query": q,
            "source": source
        })
        
    except Exception as e:
        print(f"Erro na busca: {e}")
        return templates.TemplateResponse("partials/search_results.html", {
            "request": request,
            "books": [],
            "error": "Erro ao buscar livros. Tente novamente."
        })


@router.get("/library", response_class=HTMLResponse)
async def library_page(request: Request, db: Session = Depends(get_db)):
    """Página da biblioteca"""
    user = await require_auth(request, db)
    
    # Obter filtro de status
    status_filter = request.query_params.get('status', 'all')
    
    query = db.query(UserBook).filter(UserBook.user_id == user.id)
    
    if status_filter != 'all':
        query = query.filter(UserBook.status == status_filter)
    
    books = query.order_by(UserBook.added_at.desc()).all()
    
    return templates.TemplateResponse("library.html", {
        "request": request,
        "user": user,
        "books": books,
        "status_filter": status_filter
    })


@router.get("/library-content", response_class=HTMLResponse)
async def library_content(
    request: Request,
    status: str = "all",
    db: Session = Depends(get_db)
):
    """Conteúdo da biblioteca (HTMX)"""
    user = await require_auth(request, db)
    
    query = db.query(UserBook).filter(UserBook.user_id == user.id)
    
    if status != 'all':
        query = query.filter(UserBook.status == status)
    
    books = query.order_by(UserBook.added_at.desc()).all()
    
    return templates.TemplateResponse("partials/library_content.html", {
        "request": request,
        "books": books
    })


@router.post("/add")
async def add_book(
    request: Request,
    book_id: str = Form(...),
    title: str = Form(...),
    authors: str = Form(""),
    description: str = Form(""),
    categories: str = Form(""),
    thumbnail: str = Form(""),
    rating: float = Form(0.0),
    db: Session = Depends(get_db)
):
    """Adicionar livro à biblioteca"""
    user = await require_auth(request, db)
    
    # Verificar se já existe
    existing = db.query(UserBook).filter(
        UserBook.user_id == user.id,
        UserBook.book_id == book_id
    ).first()
    
    if existing:
        return HTMLResponse(
            content='<div class="text-red-600 text-sm">✗ Livro já está na biblioteca</div>',
            headers={"HX-Reswap": "innerHTML", "HX-Retarget": f"#status-{book_id}"}
        )
    
    # Adicionar livro
    new_book = UserBook(
        user_id=user.id,
        book_id=book_id,
        title=title,
        authors=authors,
        description=description,
        categories=categories,
        thumbnail=thumbnail,
        google_rating=rating,
        status='want_to_read'
    )
    
    db.add(new_book)
    db.commit()
    
    return HTMLResponse(
        content='<div class="text-green-600 text-sm">✓ Adicionado à biblioteca!</div>',
        headers={"HX-Reswap": "innerHTML", "HX-Retarget": f"#status-{book_id}"}
    )


@router.post("/{book_id}/update-status")
async def update_status(
    request: Request,
    book_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    """Atualizar status do livro"""
    user = await require_auth(request, db)
    
    book = db.query(UserBook).filter(
        UserBook.id == book_id,
        UserBook.user_id == user.id
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    
    book.status = status
    db.commit()
    
    # Retornar o card atualizado
    return templates.TemplateResponse("partials/book_card.html", {
        "request": request,
        "book": book
    })


@router.post("/{book_id}/rate")
async def rate_book(
    request: Request,
    book_id: int,
    rating: int = Form(...),
    db: Session = Depends(get_db)
):
    """Avaliar livro"""
    user = await require_auth(request, db)
    
    book = db.query(UserBook).filter(
        UserBook.id == book_id,
        UserBook.user_id == user.id
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    
    book.user_rating = rating
    db.commit()
    
    # Retornar estrelas atualizadas
    return templates.TemplateResponse("partials/rating_stars.html", {
        "request": request,
        "book": book
    })


@router.delete("/{book_id}")
async def delete_book(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db)
):
    """Remover livro da biblioteca"""
    user = await require_auth(request, db)
    
    book = db.query(UserBook).filter(
        UserBook.id == book_id,
        UserBook.user_id == user.id
    ).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    
    db.delete(book)
    db.commit()
    
    return HTMLResponse(content="", status_code=200)
