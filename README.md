# Dota 2 Counter Bot v2.0

Telegram бот с ML-предсказаниями матчей, контрпиками и статистикой из OpenDota API.

## Установка

```bash
# Клонирование
mkdir dota2_bot && cd dota2_bot

# Создание структуры
mkdir -p src/{api,ml,handlers,services,models,data,utils} cache logs

# Установка зависимостей
pip install -r requirements.txt

# Настройка
cp .env.example .env
# Отредактируй .env, добавь BOT_TOKEN

# Запуск
python -m src.main
