import random
import telebot
import requests
from telebot import types
import bot2_db

TOKEN = '78449'
bot = telebot.TeleBot(TOKEN)

user_answers = {}


def get_random_word(user_id):
    words = bot2_db.get_words_from_db(user_id)
    if not words:
        return None, None, None

    target = random.choice(words)
    other_options = random.sample([w[0] for w in words if w[0] != target[0]], 3)

    return target[0], target[1], other_options


def send_random_word(message):
    user_id = message.from_user.id
    target_word, russian_word, other_words = get_random_word(user_id)

    if not target_word:
        bot.send_message(message.chat.id, "Ваш словарь пуст. Добавьте новые слова!")
        return

    user_answers[user_id] = target_word

    markup = types.ReplyKeyboardMarkup(row_width=2)
    buttons = [types.KeyboardButton(word) for word in [target_word] + other_words]
    random.shuffle(buttons)

    markup.add(*buttons)

    add_word_btn = types.KeyboardButton('Добавить слово')
    delete_word_btn = types.KeyboardButton('Удалить слово')
    next_btn = types.KeyboardButton('Дальше')
    markup.add(add_word_btn, delete_word_btn, next_btn)

    bot.send_message(message.chat.id, f'Угадай перевод слова: {russian_word}', reply_markup=markup)

def get_usage_example(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        for meaning in data[0]["meanings"]:
            for definition in meaning["definitions"]:
                if "example" in definition:
                    return definition["example"]

    else:
        print(f"Ошибка: {response.status_code}")
        return None

@bot.message_handler(commands=['start', 'cards'])
def start_bot(message):
    user_id = message.from_user.id
    if not bot2_db.user_exists(user_id):
        bot2_db.add_user(user_id)
        bot.send_message(message.chat.id, f"Привет, <b>{message.from_user.first_name}</b>.\n"
                                           "Давай попрактикуемся в английском языке!\n"
                                           "\n"
                                           "У тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения.\n"
                                           "Для этого воспользуйся инструментами:\n"
                                           "<i>Добавить слово ➕</i>,\n"
                                           "<i>Удалить слово 🔙</i>.\n"
                                           "\n"
                                           "Отправь мне /help, если нужна помощь.\n"
                                           "Удачи! 😊",
                                           parse_mode="HTML",
                                        )
        default_words = bot2_db.insert_default_words()
        for eng, rus in default_words:
            bot2_db.add_word_to_db(user_id, eng, rus)

    user_words = bot2_db.get_words_from_db(user_id)
    words_list = "\n".join([f"{eng} - {rus}" for eng, rus in user_words])

    bot.send_message(message.chat.id, f"Добро пожаловать, <b>{message.from_user.first_name}</b>!\n"
                                      f"Вот все твои слова:\n{words_list}", parse_mode="HTML",)

    send_random_word(message)


@bot.message_handler(commands=["help"])
def help_bot(message):
    bot.send_message(
        message.chat.id,
        "<b>Используй команды</b> 💬:\n"
        "/start и /cards - начать обучение\n"
        "\n"
        "<b>Используй кнопки:</b>\n"
        "<i>Добавить слово➕\n</i>"
        "<i>Удалить слово🔙\n</i>"
        "<i>Дальше ⏭\n</i>"
        "\n"
        "Эти функции помогут тебе создать свою собственную базу данных для обучения!\n"
        "Удачи! 😊",
        parse_mode="HTML",
    )

@bot.message_handler(func=lambda message: message.text == 'Дальше')
def next_word(message):
    send_random_word(message)


@bot.message_handler(func=lambda message: message.text == "Добавить слово")
def add_word(message):

    bot.send_message(message.chat.id, "Введите английское слово для добавления: ")
    bot.register_next_step_handler(message, save_english_word)


def save_english_word(message):
    if message.text == 'Дальше':
        next_word(message)
        return
    elif message.text == 'Удалить слово':
        delete_word(message)
        return
    english_word = message.text
    bot.send_message(message.chat.id, 'Введите перевод этого слова: ')
    bot.register_next_step_handler(message, lambda msg: save_translation(msg, english_word))


def save_translation(message, english_word):
    user_id = message.from_user.id
    translation = message.text
    bot2_db.add_word_to_db(user_id, english_word, translation)
    bot.send_message(message.chat.id,
                     f"Слово '{english_word}' с переводом '{translation}' добавлено в Ваш словарик!")
    send_random_word(message)


@bot.message_handler(func=lambda message: message.text == 'Удалить слово')
def delete_word(message):
    user_id = message.from_user.id
    user_words = bot2_db.get_words_from_db(user_id)
    if not user_words:
        bot.send_message(message.chat.id, 'У вас нет слов для удаления.')
        return
    words_list = "\n".join([f"{eng} - {rus}" for eng, rus in user_words])
    bot.send_message(message.chat.id, f"Ваши слова:\n{words_list}\n\nВведите английское слово для удаления:")
    bot.register_next_step_handler(message, confirm_delete_word)


def confirm_delete_word(message):
    user_id = message.from_user.id
    english_word = message.text

    if message.text == 'Дальше':
        next_word(message)
        return
    elif message.text == 'Добавить слово':
        add_word(message)
        return
    elif message.text == 'Удалить слово':
        delete_word(message)
        return

    user_words = bot2_db.get_words_from_db(user_id)
    if english_word not in [word[0] for word in user_words]:
        bot.send_message(message.chat.id, f"Слово '{english_word}' не найдено в Вашем словаре.")
        return

    bot2_db.remove_word_from_db(user_id, english_word)
    bot.send_message(message.chat.id, f"Слово '{english_word}' удалено из Вашего словарика!")

@bot.message_handler(func=lambda message: True)
def check_answer(message):
    user_id = message.from_user.id
    target_word = user_answers.get(user_id)

    if message.text == 'Дальше':
        send_random_word(message)
    elif message.text.strip().lower() == target_word.strip().lower():
        bot.send_message(message.chat.id, 'Правильно! 🎉')
        example = get_usage_example(target_word)
        bot.send_message(message.chat.id, f"<b>Пример</b> 📖:<i>{example}</i>", parse_mode="HTML")
        send_random_word(message)
    elif message.text in ['Добавить слово', 'Удалить слово']:
        return  
    else:
        bot.send_message(message.chat.id, 'Ошибка ❌ Попробуйте ещё раз.')


if __name__ == '__main__':
    print('Bot is running!')
    bot.infinity_polling(skip_pending=True)