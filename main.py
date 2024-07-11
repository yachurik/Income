from telebot import TeleBot, types
from config import TOKEN, DATABASE
from logic import DB_Manager

bot = TeleBot(TOKEN)
manager = DB_Manager(DATABASE)

hideBoard = types.ReplyKeyboardRemove()
cancel_button = "Отмена 🚫"

def cancel(message):
    bot.send_message(message.chat.id, "Чтобы посмотреть команды, используй - /info", reply_markup=hideBoard)

def no_projects(message):
    bot.send_message(message.chat.id, 'У тебя пока нет расходов и заработка!')

def gen_inline_markup(rows):
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(types.InlineKeyboardButton(row, callback_data=row))
    return markup

def gen_markup(rows):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(types.KeyboardButton(row))
    markup.add(types.KeyboardButton(cancel_button))
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "Привет! Я бот-менеджер расходов.\nЯ помогу тебе отслеживать свои расходы и доходы.\nДля списка доступных команд используй /info")
    info(message)

@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id,
    """
    Вот команды которые могут тебе помочь:

    /new_income - добавление нового дохода
    /new_expense - добавление нового расхода
    /records - отображение всех записей
    /delete - удаление записи
    /update_income - обновление дохода
    /update_expense - обновление расхода
    """)

@bot.message_handler(commands=['records'])
def get_records(message):
    user_id = message.from_user.id
    records = manager.get_records(user_id)
    if records:
        text = "\n".join([f"Record ID: {record[0]}, Amount: {record[2]}, Category: {record[3]}, Description: {record[4]}, Date: {record[5]}" for record in records])
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "У вас нет записей.")

@bot.message_handler(commands=['new_income'])
def new_income(message):
    bot.send_message(message.chat.id, "Введите сумму дохода:")
    bot.register_next_step_handler(message, income_amount)

def income_amount(message):
    amount = message.text
    user_id = message.from_user.id
    data = [user_id, amount]
    bot.send_message(message.chat.id, "Введите описание дохода:")
    bot.register_next_step_handler(message, income_description, data=data)

def income_description(message, data):
    description = message.text
    data.append(description)
    from datetime import datetime
    data.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    success = manager.insert_income([tuple(data)])
    if success:
        bot.send_message(message.chat.id, "Доход сохранен")
    else:
        bot.send_message(message.chat.id, "Не удалось сохранить доход")

@bot.message_handler(commands=['new_expense'])
def new_expense(message):
    bot.send_message(message.chat.id, "Введите сумму расхода:")
    bot.register_next_step_handler(message, expense_amount)

def expense_amount(message):
    amount = message.text
    user_id = message.from_user.id
    data = [user_id, amount]
    categories = manager.get_expense_categories()
    category_names = [category[0] for category in categories]
    bot.send_message(message.chat.id, "Введите категорию расхода:", reply_markup=gen_markup(category_names))
    bot.register_next_step_handler(message, expense_description, data=data, category_names=category_names)

def expense_description(message, data, category_names):
    category = message.text
    if category == cancel_button:
        cancel(message)
        return
    if category not in category_names:
        bot.send_message(message.chat.id, "Ты выбрал категорию не из списка, попробуй еще раз!", reply_markup=gen_markup(category_names))
        bot.register_next_step_handler(message, expense_description, data=data, category_names=category_names)
        return
    data.append(category)
    bot.send_message(message.chat.id, "Введите описание расхода:")
    bot.register_next_step_handler(message, save_expense, data=data)

def save_expense(message, data):
    description = message.text
    data.append(description)
    from datetime import datetime
    data.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    success = manager.insert_expense([tuple(data)])
    if success:
        bot.send_message(message.chat.id, "Расход успешно добавлен.")
    else:
        bot.send_message(message.chat.id, "Не удалось добавить расход.")

@bot.message_handler(commands=['delete'])
def delete_record(message):
    bot.send_message(message.chat.id, "Введите ID записи, которую хотите удалить:")
    bot.register_next_step_handler(message, confirm_delete)

def confirm_delete(message):
    record_id = message.text
    if not record_id.isdigit():
        bot.send_message(message.chat.id, "ID записи должен быть числом. Попробуй еще раз.")
        bot.register_next_step_handler(message, confirm_delete)
        return
    success = manager.delete_record(record_id)
    if success:
        bot.send_message(message.chat.id, f"Запись с ID {record_id} успешно удалена.")
    else:
        bot.send_message(message.chat.id, f"Не удалось найти запись с ID {record_id}.")

@bot.message_handler(commands=['update_income'])
def update_income(message):
    bot.send_message(message.chat.id, "Введите ID дохода, который хотите обновить:")
    bot.register_next_step_handler(message, update_income_amount)

def update_income_amount(message):
    income_id = message.text
    if not income_id.isdigit():
        bot.send_message(message.chat.id, "ID дохода должен быть числом. Попробуй еще раз.")
        bot.register_next_step_handler(message, update_income_amount)
        return
    bot.send_message(message.chat.id, "Введите новую сумму дохода:")
    bot.register_next_step_handler(message, update_income_description, income_id=income_id)

def update_income_description(message, income_id):
    amount = message.text
    user_id = message.from_user.id
    data = [user_id, amount]
    bot.send_message(message.chat.id, "Введите новое описание дохода:")
    bot.register_next_step_handler(message, perform_income_update, data=data, income_id=income_id)

def perform_income_update(message, data, income_id):
    description = message.text
    data.append(description)
    success = manager.update_income(data, income_id)
    if success:
        bot.send_message(message.chat.id, f"Доход с ID {income_id} успешно обновлен.")
    else:
        bot.send_message(message.chat.id, f"Не удалось обновить доход с ID {income_id}.")

@bot.message_handler(commands=['update_expense'])
def update_expense(message):
    bot.send_message(message.chat.id, "Введите ID расхода, который хотите обновить:")
    bot.register_next_step_handler(message, update_expense_amount)

def update_expense_amount(message):
    expense_id = message.text
    if not expense_id.isdigit():
        bot.send_message(message.chat.id, "ID расхода должен быть числом. Попробуй еще раз.")
        bot.register_next_step_handler(message, update_expense_amount)
        return
    bot.send_message(message.chat.id, "Введите новую сумму расхода:")
    bot.register_next_step_handler(message, update_expense_category, expense_id=expense_id)

def update_expense_category(message, expense_id):
    amount = message.text
    user_id = message.from_user.id
    data = [user_id, amount]
    categories = manager.get_expense_categories()
    category_names = [category[0] for category in categories]
    bot.send_message(message.chat.id, "Введите новую категорию расхода:", reply_markup=gen_markup(category_names))
    bot.register_next_step_handler(message, update_expense_description, data=data, expense_id=expense_id, category_names=category_names)

def update_expense_description(message, data, expense_id, category_names):
    category = message.text
    if category == cancel_button:
        cancel(message)
        return
    if category not in category_names:
        bot.send_message(message.chat.id, "Ты выбрал категорию не из списка, попробуй еще раз!", reply_markup=gen_markup(category_names))
        bot.register_next_step_handler(message, update_expense_description, data=data, expense_id=expense_id, category_names=category_names)
        return
    data.append(category)
    bot.send_message(message.chat.id, "Введите новое описание расхода:")
    bot.register_next_step_handler(message, perform_expense_update, data=data, expense_id=expense_id)

def perform_expense_update(message, data, expense_id):
    description = message.text
    data.append(description)
    success = manager.update_expense(data, expense_id)
    if success:
        bot.send_message(message.chat.id, f"Расход с ID {expense_id} успешно обновлен.")
    else:
        bot.send_message(message.chat.id, f"Не удалось обновить расход с ID {expense_id}.")

if __name__ == '__main__':
    bot.infinity_polling()
