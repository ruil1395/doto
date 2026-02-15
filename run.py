#!/usr/bin/env python3
import sys
import os

# Добавляем текущую папку в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Запускаем как модуль
from src.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
