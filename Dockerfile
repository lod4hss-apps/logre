FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

RUN apt-get update && \
    apt-get install --no-install-recommends -y git curl gettext-base && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN rm -f src/lib/shacl-maker.js && \
    curl -sL https://raw.githubusercontent.com/gaetanmuck/shacl-maker/refs/heads/main/src/index.js | \
    sed -n '\|// To not include|q;p' > src/lib/shacl-maker.js

RUN chmod +x scripts/*.sh

EXPOSE 8501

CMD ["streamlit", "run", "src/server.py"]
