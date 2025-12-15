from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from bot.handlers import BotHandlers
from bot.config import TOKEN

BUDGET, GOAL, WAITING_FOR_CITY = range(3)

def main():
    handlers = BotHandlers()
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handlers.handle_new_build, pattern='^new_build$')],
        states={
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_budget)],
            GOAL: [CallbackQueryHandler(handlers.ask_goal, pattern='^(games|office|editing|other)$')],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)]
    )

    city_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handlers.find_stores, pattern='^find_stores$')],
        states={
            WAITING_FOR_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_city_input)]
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)]
    )

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CallbackQueryHandler(handlers.show_my_builds, pattern='^my_builds$'))
    app.add_handler(CallbackQueryHandler(handlers.show_build_details, pattern='^build_\\d+$'))
    app.add_handler(CallbackQueryHandler(handlers.handle_main_menu_callback, pattern='^main_menu$'))

    app.add_handler(conv_handler)
    app.add_handler(city_conv_handler)

    app.run_polling()

if __name__ == '__main__':
    main()