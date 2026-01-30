"""
Integração com Open Library API
https://openlibrary.org/developers/api
"""
import requests
from typing import List, Dict, Optional


class OpenLibraryAPI:
    """Cliente para Open Library API"""
    
    BASE_URL = "https://openlibrary.org"
    SEARCH_URL = f"{BASE_URL}/search.json"
    COVERS_URL = "https://covers.openlibrary.org/b"
    
    @staticmethod
    def search_books(query: str, limit: int = 20) -> List[Dict]:
        """
        Buscar livros na Open Library
        
        Args:
            query: Termo de busca
            limit: Número máximo de resultados
            
        Returns:
            Lista de livros formatados
        """
        try:
            response = requests.get(
                OpenLibraryAPI.SEARCH_URL,
                params={
                    'q': query,
                    'limit': limit,
                    'fields': 'key,title,author_name,first_publish_year,'
                             'isbn,subject,ratings_average,cover_i',
                    'language': 'por,eng'
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            books = []
            for doc in data.get('docs', []):
                book = OpenLibraryAPI._format_book(doc)
                if book:
                    books.append(book)
            
            return books
            
        except Exception as e:
            print(f"Erro ao buscar na Open Library: {e}")
            return []
    
    @staticmethod
    def _format_book(doc: Dict) -> Optional[Dict]:
        """Formatar livro do Open Library para formato padrão"""
        try:
            # ID único
            key = doc.get('key', '')
            book_id = key.replace('/works/', 'ol_')
            
            # Informações básicas
            title = doc.get('title', 'Sem título')
            authors = doc.get('author_name', [])
            year = doc.get('first_publish_year', '')
            
            # Descrição (Open Library não retorna na busca, então usamos subjects)
            subjects = doc.get('subject', [])[:5]
            description = f"Publicado em {year}. " if year else ""
            if subjects:
                description += f"Temas: {', '.join(subjects)}."
            
            # Categorias
            categories = doc.get('subject', [])[:3]
            
            # Rating
            rating = doc.get('ratings_average', 0)
            if rating:
                rating = round(rating, 1)
            
            # Thumbnail
            cover_id = doc.get('cover_i')
            thumbnail = ""
            if cover_id:
                thumbnail = f"{OpenLibraryAPI.COVERS_URL}/id/{cover_id}-M.jpg"
            
            return {
                'id': book_id,
                'title': title,
                'authors': authors,
                'description': description,
                'categories': categories,
                'rating': rating,
                'thumbnail': thumbnail,
                'source': 'openlibrary'
            }
            
        except Exception as e:
            print(f"Erro ao formatar livro: {e}")
            return None
    
    @staticmethod
    def get_book_details(work_id: str) -> Optional[Dict]:
        """
        Obter detalhes completos de um livro
        
        Args:
            work_id: ID do work (ex: /works/OL45804W)
            
        Returns:
            Detalhes do livro
        """
        try:
            # Se o ID vier com ol_ prefix, extrair o ID real
            if work_id.startswith('ol_'):
                work_id = '/works/' + work_id.replace('ol_', '')
            
            response = requests.get(
                f"{OpenLibraryAPI.BASE_URL}{work_id}.json",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Obter descrição completa
            description = ""
            if 'description' in data:
                desc = data['description']
                if isinstance(desc, dict):
                    description = desc.get('value', '')
                else:
                    description = str(desc)
            
            return {
                'description': description,
                'subjects': data.get('subjects', []),
                'covers': data.get('covers', [])
            }
            
        except Exception as e:
            print(f"Erro ao obter detalhes: {e}")
            return None


class GoogleBooksAPI:
    """Cliente para Google Books API (já existente, refatorado)"""
    
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"
    
    @staticmethod
    def search_books(query: str, api_key: str = "", limit: int = 20) -> List[Dict]:
        """
        Buscar livros no Google Books
        
        Args:
            query: Termo de busca
            api_key: API Key do Google (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de livros formatados
        """
        try:
            params = {
                'q': query,
                'maxResults': limit,
                'langRestrict': 'pt',
                'printType': 'books'
            }
            
            if api_key:
                params['key'] = api_key
            
            response = requests.get(
                GoogleBooksAPI.BASE_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            books = []
            for item in data.get('items', []):
                book = GoogleBooksAPI._format_book(item)
                if book:
                    books.append(book)
            
            return books
            
        except Exception as e:
            print(f"Erro ao buscar no Google Books: {e}")
            return []
    
    @staticmethod
    def _format_book(item: Dict) -> Optional[Dict]:
        """Formatar livro do Google Books para formato padrão"""
        try:
            vol = item.get('volumeInfo', {})
            
            return {
                'id': 'gb_' + item.get('id', ''),
                'title': vol.get('title', 'Sem título'),
                'authors': vol.get('authors', []),
                'description': vol.get('description', ''),
                'categories': vol.get('categories', []),
                'rating': vol.get('averageRating', 0),
                'thumbnail': vol.get('imageLinks', {}).get('thumbnail', ''),
                'source': 'google'
            }
            
        except Exception as e:
            print(f"Erro ao formatar livro: {e}")
            return None


class UnifiedBookAPI:
    """API unificada que busca em múltiplas fontes"""
    
    @staticmethod
    def search_books(
        query: str,
        sources: List[str] = ['google', 'openlibrary'],
        limit_per_source: int = 10,
        google_api_key: str = ""
    ) -> List[Dict]:
        """
        Buscar livros em múltiplas fontes
        
        Args:
            query: Termo de busca
            sources: Lista de fontes ('google', 'openlibrary')
            limit_per_source: Limite por fonte
            google_api_key: API Key do Google Books
            
        Returns:
            Lista unificada de livros (sem duplicatas)
        """
        all_books = []
        
        # Buscar no Google Books
        if 'google' in sources:
            google_books = GoogleBooksAPI.search_books(
                query, 
                api_key=google_api_key,
                limit=limit_per_source
            )
            all_books.extend(google_books)
        
        # Buscar na Open Library
        if 'openlibrary' in sources:
            ol_books = OpenLibraryAPI.search_books(
                query,
                limit=limit_per_source
            )
            all_books.extend(ol_books)
        
        # Remover duplicatas por título similar
        unique_books = UnifiedBookAPI._remove_duplicates(all_books)
        
        return unique_books
    
    @staticmethod
    def _remove_duplicates(books: List[Dict]) -> List[Dict]:
        """Remove duplicatas baseado em similaridade de título"""
        seen_titles = set()
        unique = []
        
        for book in books:
            # Normalizar título para comparação
            title_normalized = book['title'].lower().strip()
            
            if title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique.append(book)
        
        return unique
