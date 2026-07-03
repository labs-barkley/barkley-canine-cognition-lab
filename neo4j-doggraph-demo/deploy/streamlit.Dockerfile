# Barkley DogGraph — Streamlit app image.
# Build context is the neo4j-doggraph-demo/ folder (see docker-compose.yml).
FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal; matplotlib/networkx wheels are self-contained.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code (app.py, graph_query*.py, screenshots/, .cypher files, etc.)
COPY . .

# Barkley v9 dark theme for Streamlit.
RUN mkdir -p /app/.streamlit
COPY deploy/config.toml /app/.streamlit/config.toml

EXPOSE 8501
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
