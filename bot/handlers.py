from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database import BuildSaver
from bot.selector import ComponentSelector
from bot.config import YANDEX_MAPS_API_KEY
from bot.config import YANDEX_Static_API_KEY
import requests

# Состояния
BUDGET, GOAL, WAITING_FOR_CITY = range(3)

class BotHandlers:
    def __init__(self):
        self.db = BuildSaver()
        self.selector = ComponentSelector()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()

        keyboard = [
            [InlineKeyboardButton("Создать новую сборку", callback_data='new_build')],
            [InlineKeyboardButton("Мои сборки", callback_data='my_builds')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)
        elif update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

    async def handle_new_build(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text="Введите ваш бюджет на ПК (в рублях):")
        return BUDGET

    async def show_my_builds(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id

        builds = self.db.get_builds_by_user_id(user_id)

        if not builds:
            keyboard = [[InlineKeyboardButton("В главное меню", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="У вас пока нет сохранённых сборок.")
            return

        keyboard = []
        for build in builds:
            keyboard.append([InlineKeyboardButton(f"Сборка от {build['created_at']} - {build['total_price']}руб.", callback_data=f"build_{build['id']}")])

        keyboard.append([InlineKeyboardButton("В главное меню", callback_data='main_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Ваши сборки:", reply_markup=reply_markup)

    async def show_build_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        build_id = int(query.data.split('_')[1])
        build = self.db.get_build_by_id(build_id)

        if not build:
            keyboard = [[InlineKeyboardButton("В главное меню", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="Сборка не найдена.")
            return

        response = self.format_build_from_db(build)

        keyboard = [[InlineKeyboardButton("В главное меню", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=response, reply_markup=reply_markup)

    async def handle_budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            budget = int(update.message.text)
            context.user_data['budget'] = budget
            keyboard = [
                [InlineKeyboardButton("Игры", callback_data='games')],
                [InlineKeyboardButton("Офис", callback_data='office')],
                [InlineKeyboardButton("Монтаж", callback_data='editing')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Для каких целей будет использоваться ПК?", reply_markup=reply_markup)
            
            return GOAL
        except ValueError:
            keyboard = [
                [InlineKeyboardButton("В главное меню", callback_data='main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Пожалуйста, введите число.")
            return BUDGET

    async def ask_goal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        goal = query.data
        print(GOAL)
        context.user_data['goal'] = goal

        budget = context.user_data['budget']

        build = self.selector.select(budget, goal)

        response, reply_markup = self.format_build(build)

        await query.edit_message_text(text=response, reply_markup=reply_markup)

        self.db.save_build(query.from_user.id, build)

        return ConversationHandler.END
    
    async def find_stores(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(text="Введите город, в котором хотите найти магазины DNS (например, Москва):")

        return WAITING_FOR_CITY

    async def handle_city_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        city = update.message.text.strip()

        if not city:
            await update.message.reply_text("Пожалуйста, введите название города.")
            return WAITING_FOR_CITY

        geocode_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": YANDEX_MAPS_API_KEY,
            "geocode": city,
            "format": "json",
            "results": 1
        }

        try:
            response = requests.get(geocode_url, params=params)
            data = response.json()

            if data["response"]["GeoObjectCollection"]["metaDataProperty"]["GeocoderResponseMetaData"]["found"] == 0:
                await update.message.reply_text("Город не найден. Попробуйте ещё раз.")
                return WAITING_FOR_CITY

            pos_str = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
            lon, lat = map(float, pos_str.split(" "))

        except Exception as e:
            await update.message.reply_text(f"Ошибка при получении координат: {e}")
            return WAITING_FOR_CITY

        yandex_maps_link = f"https://yandex.ru/maps/?ll={lon}%2C{lat}&z=12&l=map"

        await update.message.reply_text(f"Вот ссылка на Яндекс.Карты для города {city}:\n{yandex_maps_link}")

        await self.start(update, context)
        return ConversationHandler.END
    
    async def handle_main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await self.start(update, context)

    def get_build_by_budget_and_goal(self, budget, goal):
        build = self.selector.select(budget, goal)
        return {
            "cpu": build['cpu']['name'] if build['cpu'] else "Не выбран",
            "gpu": build['gpu']['name'] if build['gpu'] else "Не выбран",
            "motherboard": build['motherboard']['name'] if build['motherboard'] else "Не выбрана",
            "ram": build['ram']['name'] if build['ram'] else "Не выбрана",
            "ssd": build['ssd']['name'] if build['ssd'] else "Не выбран",
            "psu": build['psu']['name'] if build['psu'] else "Не выбран",
            "case": build['pc_case']['name'] if build['pc_case'] else "Не выбран",
            "cooler": build['cooler']['name'] if build['cooler'] else "Не выбран",
            "total_price": build['total_price']
        }

    def format_build(self, build):
        response = f"""
        CPU: {build['cpu']}\n
        GPU: {build['gpu']}\n
        MB: {build['motherboard']}\n
        RAM: {build['ram']}\n
        SSD: {build['ssd']}\n
        PSU: {build['psu']}\n
        Case: {build['pc_case']}\n
        Cooler: {build['cooler']}\n
        Общая цена: {build['total_price']} руб.
        """.strip()

        keyboard = [
            [InlineKeyboardButton("Найти магазины", callback_data='find_stores')],
            [InlineKeyboardButton("В главное меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        return response, reply_markup
    
    def format_build_from_db(self, build):
        return f"""
        CPU: {build['cpu']}\n
        GPU: {build['gpu']}\n
        MB: {build['motherboard']}\n
        RAM: {build['ram']}\n
        SSD: {build['ssd']}\n
        PSU: {build['psu']}\n
        Case: {build['pc_case']}\n
        Cooler: {build['cooler']}\n
        Общая цена: {build['total_price']} руб.
        """.strip()

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Диалог отменён.")
        return ConversationHandler.END