from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List
import random
from .models import UserBook

def generate_recommendations(
    user_books: List[UserBook],
    candidate_books: List[dict],
    limit: int = 12
) -> List[dict]:
    """
    Gera recomendações refinadas com penalização de livros odiados.
    """
    
    # 1. MELHORIA: Definição mais estrita de "Favoritos"
    # Só usamos para match positivo se a nota for boa ou se não tiver nota mas foi lido.
    favorites = [
        b for b in user_books
        if (b.user_rating and b.user_rating >= 3.5) or (b.status == "finished" and not b.user_rating)
    ]

    # 2. NOVO: Identificar livros "Odiados" para penalização
    hated_books = [
        b for b in user_books
        if b.user_rating and b.user_rating <= 2.5
    ]

    if not favorites or not candidate_books:
        return []

    # Preparar descrições (Favoritos e Odiados)
    fav_descriptions = [b.description or b.title or "" for b in favorites]
    hated_descriptions = [b.description or b.title or "" for b in hated_books]
    
    cand_descriptions = [
        b.get('description', '') or b.get('title', '')
        for b in candidate_books
    ]

    # Limpeza básica
    def clean_text(texts):
        return [t if t.strip() else "no description" for t in texts]

    fav_descriptions = clean_text(fav_descriptions)
    hated_descriptions = clean_text(hated_descriptions)
    cand_descriptions = clean_text(cand_descriptions)

    # TF-IDF Setup
    vectorizer = TfidfVectorizer(
        max_features=1500, # Aumentei um pouco para captar mais nuances
        stop_words='english', # Idealmente, use stop_words em português se os livros forem BR
        ngram_range=(1, 2)
    )

    try:
        # Treinar com tudo para ter o vocabulário completo
        all_corpus = fav_descriptions + hated_descriptions + cand_descriptions
        vectorizer.fit(all_corpus)
        
        cand_vectors = vectorizer.transform(cand_descriptions)
        fav_vectors = vectorizer.transform(fav_descriptions)
        
        # Calcular similaridade com favoritos (Bônus)
        # Retorna matriz [n_candidatos, n_favoritos]
        sim_favorites = cosine_similarity(cand_vectors, fav_vectors)
        # Pegamos a média dos 3 melhores matches para não depender de um único livro
        # (Se tiver menos de 3 favoritos, pega a média de tudo)
        if sim_favorites.shape[1] >= 3:
            # Ordena cada linha e pega os 3 últimos (maiores valores), depois a média
            semantic_scores = np.sort(sim_favorites, axis=1)[:, -3:].mean(axis=1)
        else:
            semantic_scores = sim_favorites.mean(axis=1)

        # Calcular similaridade com odiados (Penalidade)
        penalty_scores = np.zeros(len(candidate_books))
        if hated_vectors := vectorizer.transform(hated_descriptions) if hated_books else None:
            if hated_vectors.shape[0] > 0:
                sim_hated = cosine_similarity(cand_vectors, hated_vectors)
                penalty_scores = sim_hated.max(axis=1)

    except Exception as e:
        print(f"Erro no TF-IDF: {e}")
        semantic_scores = np.zeros(len(candidate_books))
        penalty_scores = np.zeros(len(candidate_books))

    # Scoring Final
    recommendations = []
    
    for i, book in enumerate(candidate_books):
        score = 0.0
        reasons = []
        
        # 1. Similaridade Semântica (45%)
        sem_score = float(semantic_scores[i])
        score += sem_score * 0.45
        
        # 2. Penalidade por similaridade com livro ruim (-25%)
        pen_score = float(penalty_scores[i])
        if pen_score > 0.4: # Só penaliza se for realmente muito parecido
            score -= pen_score * 0.25
            # Não adicionamos "motivo" para penalidade, apenas baixamos o score
        
        # 3. Category Match (30%)
        # Aqui usamos set intersection para ser mais rápido
        book_cats = set([c.strip().lower() for c in book.get('categories', [])])
        
        # Coletar categorias dos favoritos
        fav_cats = set()
        for f in favorites:
            if f.categories:
                fav_cats.update([c.strip().lower() for c in f.categories.split(',')])
        
        if book_cats & fav_cats:
            score += 0.3
            cat_name = list(book_cats & fav_cats)[0].title()
            reasons.append(f"Gênero: {cat_name}")

        # 4. Author Match (15%)
        book_authors = set([a.strip().lower() for a in book.get('authors', [])])
        fav_authors = set()
        for f in favorites:
            if f.authors:
                fav_authors.update([a.strip().lower() for a in f.authors.split(',')])
                
        if book_authors & fav_authors:
            score += 0.15
            auth_name = list(book_authors & fav_authors)[0].title()
            reasons.append(f"Autor: {auth_name}")

        # 5. Rating Global Bonus (10%)
        google_rating = book.get('rating', 0) or 0
        if google_rating >= 4.5:
            score += 0.1
            reasons.append("Aclamado pela crítica")
        elif google_rating >= 4.0:
            score += 0.05

        # Adicionar à lista se score for relevante
        if score > 0.25:
            recommendations.append({
                'book': book,
                'score': round(score, 3), # 3 casas para desempate
                'reason': ' • '.join(reasons[:2]) if reasons else 'Baseado no seu perfil'
            })

    # Ordenar
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations[:limit]


def get_user_favorite_categories(user_books: List[UserBook]) -> List[str]:
    """
    Retorna categorias favoritas ponderadas pela nota.
    Ex: Um livro nota 5 vale 3 pontos de categoria. Um livro nota 3 vale 1 ponto.
    """
    category_scores = {}
    
    for book in user_books:
        if not book.categories: continue
        
        # Definir peso base
        weight = 1
        if book.user_rating:
            if book.user_rating == 5: weight = 3
            elif book.user_rating == 4: weight = 2
            elif book.user_rating <= 2: weight = -1 # Penaliza categorias de livros ruins
        elif book.status == 'finished':
            weight = 1.5 # Lido sem nota vale mais que não lido
            
        categories = [c.strip() for c in book.categories.split(',')]
        for cat in categories:
            if cat:
                category_scores[cat] = category_scores.get(cat, 0) + weight

    # Remove categorias com pontuação negativa ou zero
    valid_cats = {k: v for k, v in category_scores.items() if v > 0}
    
    sorted_cats = sorted(valid_cats.items(), key=lambda x: x[1], reverse=True)
    
    # MELHORIA: Retornar top 5, mas garantir que não é sempre estático se houver empate
    # Retorna chaves
    return [c[0] for c in sorted_cats[:6]]


def get_user_favorite_authors(user_books: List[UserBook]) -> List[str]:
    """Mesma lógica ponderada para autores"""
    author_scores = {}
    
    for book in user_books:
        if not book.authors: continue
        
        weight = 1
        if book.user_rating:
            if book.user_rating >= 4: weight = 3
            elif book.user_rating <= 2: weight = 0 # Ignora autores ruins
        
        authors = [a.strip() for a in book.authors.split(',')]
        for author in authors:
            if author:
                author_scores[author] = author_scores.get(author, 0) + weight

    sorted_authors = sorted(author_scores.items(), key=lambda x: x[1], reverse=True)
    return [a[0] for a in sorted_authors[:4]]