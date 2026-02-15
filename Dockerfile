FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements отдельно для кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Создаём папки
RUN mkdir -p logs cache

# Переменная для Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Запуск бота
CMD ["python", "-m", "src.main"]
