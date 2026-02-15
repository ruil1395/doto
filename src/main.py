#!/usr/bin/env python3
import asyncio
import logging
import sys
import os

# Настройка путей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования сразу
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

try:
    from config import BOT_TOKEN, logger as config_logger
    from bot import create_application
except Exception as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)


async def main():
    logger.info("=" * 50)
    logger.info("Dota 2 Counter Bot starting...")
    logger.info("=" * 50)
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)
    
    try:
        application = create_application()
        await application.initialize()
        await application.start()
        
        logger.info("Bot is running!")
        
        # Bothost.ru требует keep-alive через polling
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        
        # Бесконечный цикл
        while True:
            await asyncio.sleep(60)
            
    except Exception as e:
        logger.error(f"Runtime error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.critical(f"Fatal: {e}", exc_info=True)
        sys.exit(1)
