# 📚 BookBrain

Um sistema moderno de gerenciamento de biblioteca pessoal e recomendação de livros, construído com foco em performance e simplicidade no frontend usando **HTMX** e **TailwindCSS**, com um backend robusto em **FastAPI**.
### Sistema de Recomendação
<img width="600" height="400" alt="Captura de tela 2026-01-29 230831" src="https://github.com/user-attachments/assets/fc12f199-bb18-49a9-baa9-d89d9b2a309d" />
### Biblioteca
<img width="600" height="400" alt="Captura de tela 2026-01-29 224849" src="https://github.com/user-attachments/assets/1c8658b4-d494-4e0e-a12a-0d0965e88a82" />


## 🚀 Sobre o Projeto

O **BookBrain** resolve o problema de organizar leituras e descobrir novos títulos sem a complexidade de frameworks SPA pesados (como React/Vue). A aplicação utiliza **Server-Side Rendering (SSR)** com Jinja2 e **HTMX** para interatividade dinâmica (SPA-feel), garantindo um carregamento extremamente rápido.

O diferencial é o motor de recomendação interno que utiliza **TF-IDF e Cosine Similarity** (via Scikit-learn) para sugerir livros baseados no histórico de leitura e avaliações do usuário, sem depender exclusivamente de APIs externas para a lógica de sugestão.

## 🛠️ Tech Stack

**Backend & Dados:**

* **Python 3.12+** gerenciado com **uv** (sucessor ultra-rápido do pip/poetry).
* **FastAPI**: Framework web assíncrono.
* **SQLAlchemy 2.0**: ORM moderno para interação com o banco.
* **PostgreSQL**: Banco de dados relacional.
* **Scikit-learn**: Processamento de dados para o sistema de recomendação.
* **Argon2**: Hashing seguro de senhas.

**Frontend:**

* **HTMX**: Requisições AJAX declarativas diretamente no HTML.
* **TailwindCSS**: Estilização utility-first.
* **Jinja2**: Templates HTML.

## ✨ Funcionalidades

* [x] **Autenticação Segura**: Login e Registro com cookies HTTP-only e JWT.
* [x] **Gestão de Biblioteca**: Adicionar livros, atualizar status (Lendo, Quero Ler, Finalizado) e dar notas.
* [x] **Busca Unificada**: Integração simultânea com **Google Books API** e **OpenLibrary**.
* [x] **Recomendações Inteligentes**: Algoritmo próprio que analisa descrições, autores e categorias dos seus livros favoritos.
* [x] **UI Responsiva**: Interface limpa e adaptável a mobile.

## ⚡ Como Rodar Localmente

Este projeto utiliza o **uv** para gerenciamento de dependências.

### 1. Clone o repositório

```bash
git clone https://github.com/jotamath/bookbrain.git
cd bookbrain

```

### 2. Configuração do Ambiente

Crie um arquivo `.env` na raiz do projeto com base no exemplo abaixo:

```ini
# .env
DATABASE_URL=postgresql://user:password@localhost/bookbrain_db
SECRET_KEY=sua_chave_secreta_gerada_com_openssl
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
GOOGLE_BOOKS_API_KEY=sua_chave_api_google

```

### 3. Instale as dependências

```bash
# Instala o uv (se não tiver)
pip install uv

# Sincroniza o ambiente virtual e instala dependências
uv sync

```

### 4. Execute a aplicação

```bash
# Roda o servidor com hot-reload
uv run uvicorn main:app --reload

```

Acesse em: `http://localhost:8000`

## 📂 Estrutura do Projeto

```text
bookbrain/
├── app/
│   ├── routers/      # Rotas da API (Books, Auth, Recommendations)
│   ├── templates/    # Arquivos HTML (Jinja2)
│   ├── auth.py       # Lógica de JWT e Segurança
│   ├── database.py   # Configuração do DB
│   ├── models.py     # Tabelas SQLAlchemy
│   └── recommendation.py # Lógica de IA/ML
├── static/           # CSS, Imagens e JS auxiliares
├── main.py           # Entry point
├── pyproject.toml    # Dependências
└── uv.lock           # Lockfile do uv

```

## 🤝 Contato

**João Matheus** Engenheiro de Software & Entusiasta de Data Science.
