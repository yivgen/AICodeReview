FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip3 install poetry==1.8.4


WORKDIR /app
COPY . /app

RUN adduser app && chown -R app /app
USER app

RUN poetry install --only main

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]