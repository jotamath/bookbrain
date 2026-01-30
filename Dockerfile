# Usa uma imagem leve do Python
FROM python:3.13-slim

# Instala o uv (gerenciador de pacotes que você está usando)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de configuração primeiro (para cachear a instalação)
COPY pyproject.toml uv.lock ./

# Instala as dependências sem instalar o projeto em si (modo frozen para garantir versões exatas)
RUN uv sync --frozen --no-install-project

# Copia o resto do código
COPY . .

# Expõe a porta 8000
EXPOSE 8000

# Comando para rodar a aplicação em produção
# Usamos 'uv run' para garantir que ele use o ambiente virtual criado pelo uv
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]