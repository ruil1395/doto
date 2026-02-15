from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from src.config import BOT_TOKEN, logger
from src.handlers.commands import CommandHandlers
from src.handlers.heroes import HeroHandlers
from src.handlers.stats import StatsHandlers
from src.handlers.predict import PredictionHandlers
from src.handlers.callbacks import CallbackHandlers
from src.handlers.errors import ErrorHandlers


def create_application() -> Application:
    logger.info("Creating bot with ML prediction support...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    predict_handlers = PredictionHandlers()
    
    # Команды
    application.add_handler(CommandHandler("start", CommandHandlers.start))
    application.add_handler(CommandHandler("help", CommandHandlers.help_command))
    application.add_handler(CommandHandler("list", CommandHandlers.list_heroes))
    application.add_handler(CommandHandler("about", CommandHandlers.about))
    
    # Герои
    application.add_handler(CommandHandler("hero", HeroHandlers.hero_command))
    application.add_handler(CommandHandler("counter", HeroHandlers.counter_command))
    application.add_handler(CommandHandler("build", HeroHandlers.build_command))
    application.add_handler(CommandHandler("search", HeroHandlers.search_command))
    
    # Статистика
    application.add_handler(CommandHandler("stats", StatsHandlers.stats_command))
    application.add_handler(CommandHandler("meta", StatsHandlers.meta_command))
    application.add_handler(CommandHandler("counters", StatsHandlers.counters_stats_command))
    
    # Предсказания
    application.add_handler(CommandHandler("predict", predict_handlers.predict_quick))
    
    # Callback
    application.add_handler(CallbackQueryHandler(CallbackHandlers.handle_callback))
    
    # Текст
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, HeroHandlers.handle_text))
    
    # Ошибки
    application.add_error_handler(ErrorHandlers.error_handler)
    
    logger.info("Bot created successfully")
    return application
