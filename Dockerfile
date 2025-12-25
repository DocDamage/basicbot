FROM python:3.10-slim

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev
COPY chatbot/ ./chatbot/
COPY docs/ ./docs/
EXPOSE 8501
CMD ["poetry", "run", "streamlit", "run", "chatbot/rag_chatbot_app.py", "--server.headless", "true", "--server.port", "8501"]
