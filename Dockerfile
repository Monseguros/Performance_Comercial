FROM python:3.11-slim-bookworm

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Instalação de dependências
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv $VIRTUAL_ENV

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD exec streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0