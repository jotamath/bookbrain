# Recomendo 3.12 para melhor compatibilidade com bibliotecas de Data Science (numpy/scikit)
FROM python:3.12-slim

# Instala o uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Define /app como o diretório onde tudo vai acontecer
WORKDIR /app

# Copia arquivos de dependência
COPY pyproject.toml uv.lock ./

# Instala dependências
RUN uv sync --frozen --no-install-project

COPY . .

# O Render ignora o EXPOSE, mas deixamos para documentação
EXPOSE 8000

# --- CORREÇÃO CRÍTICA PARA O RENDER ---
# O Render fornece a porta na variável de ambiente $PORT.
# Usamos "sh -c" para ler essa variável. Se não existir (localmente), usa 8000.
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]