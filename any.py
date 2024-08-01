import telebot
from telebot import types
import mysql.connector
from mysql.connector import pooling
from threading import Lock
import os
from dotenv import load_dotenv

# Variables
load_dotenv('my.env')
user_lock = Lock()
channel_id = '@elphii'

# Setup bot token
bot = telebot.TeleBot(os.getenv('TOKEN'))

#######################
###### Setup DB ######
#######################
# Create a connection pool
db_pool = pooling.MySQLConnectionPool(
    pool_name='my_pool',
    pool_size=30,
    pool_reset_session=True,
    host=os.getenv('host'),
    database=os.getenv('db'),
    user=os.getenv('user'),
    password=os.getenv('pass')
)

# Delete previous table
connection = db_pool.get_connection()
cursor = connection.cursor()
cursor.execute("DROP TABLE IF EXISTS anyuser")
connection.commit()

# Creat new bot table
connection = db_pool.get_connection()
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS anyuser (id INT AUTO_INCREMENT PRIMARY KEY, chat_id BIGINT UNIQUE NOT NULL, gender VARCHAR(255), state VARCHAR(255), partner_id BIGINT)")
connection.commit()

# DB control
# Add user
def add_user(chat_id, gender):
    connection = db_pool.get_connection()
    try:
        cursor = connection.cursor()
        query = f"INSERT INTO anyuser (chat_id, gender, state) VALUES ({chat_id}, '{gender}', 'off')"
        cursor.execute(query)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# Get user
def get_user(chat_id):
    connection = db_pool.get_connection()
    try:
        cursor = connection.cursor()
        query = f"SELECT gender FROM anyuser WHERE chat_id = {chat_id}"
        cursor.execute(query)
        user = cursor.fetchone()
        return user[0] if user else None
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# Update gender
def update_gender(chat_id, gender):
    connection = db_pool.get_connection()
    try:
        cursor = connection.cursor()
        query = f"UPDATE anyuser SET gender = '{gender}' WHERE chat_id = {chat_id}"
        cursor.execute(query)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# Find
# Update state
def update_state(chat_id, state):
    connection = db_pool.get_connection()
    try:
        cursor = connection.cursor()
        query = f"UPDATE anyuser SET state = '{state}' WHERE chat_id = {chat_id}"
        cursor.execute(query)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# Check state
def check_state(chat_id):
    connection = db_pool.get_connection()
    try:
        cursor = connection.cursor()
        query = f"SELECT state FROM anyuser WHERE chat_id = {chat_id}"
        cursor.execute(query)
        user = cursor.fetchone()
        return user[0] if user else None
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# find
def find(chat_id, gen):
    connection = db_pool.get_connection()
    try:
        cursor = connection.cursor()
        query = f"SELECT chat_id FROM anyuser WHERE state = 'waiting' AND gender != '{gen}' AND chat_id != {chat_id} ORDER BY RAND() LIMIT 1"
        cursor.execute(query)
        user = cursor.fetchone()
        return user[0] if user else None
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# Update partner
def update_partner(chat_id, partner_id):
    connection = db_pool.get_connection()
    try:
        cursor = connection.cursor()
        query = f"UPDATE anyuser SET partner_id = {partner_id} WHERE chat_id = {chat_id}"
        cursor.execute(query)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# Remove partner
def remove_partner(chat_id):
    connection = db_pool.get_connection()
    try:
        cursor = connection.cursor()
        query = f"UPDATE anyuser SET partner_id = NULL WHERE chat_id = {chat_id}"
        cursor.execute(query)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# Get partner
def get_partner(chat_id):
    connection = db_pool.get_connection()
    try:
        cursor = connection.cursor()
        query = f"SELECT partner_id FROM anyuser WHERE chat_id = {chat_id}"
        cursor.execute(query)
        user = cursor.fetchone()
        return user[0] if user else None
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# Check user joined func
def user_joined(chat_id):
    try:
        member = bot.get_chat_member(channel_id, chat_id)
        return member.status not in ["left", "kicked"]
    except:
        return False

# Check user joined keyboard
def check_user_joined_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('عضویت در کانال', url='https://t.me/elphii'.format(channel_id)),
    types.InlineKeyboardButton('عضو شدم', callback_data='check_join'))
    return markup

# Gender keyboard
def gender_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🙋‍♂️پسرم', callback_data='gender_boy'))
    markup.add(types.InlineKeyboardButton('🙋‍♀️دخترم', callback_data='gender_girl'))
    return markup

# Search keyboard
def search_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('جستجو👧👦', callback_data='search'))
    return markup

# Leave keyboard
def leave_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('پایان چت'))
    return keyboard

# Define the start command handler
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    with user_lock:
      if user_joined(chat_id):
         user = get_user(chat_id)
         if user:
            bot.send_message(chat_id, "جنس مخالفتو جستجو کن😍", reply_markup=search_keyboard())
         else:
            bot.send_message(message.chat.id, "جنسیتت رو انتخاب کن🥰", reply_markup=gender_keyboard())
      else:
         bot.send_message(chat_id, 'لطفا در کانال ما عضو بشید تا از قابلیت های این بات استفاده کنید❤️', reply_markup=check_user_joined_keyboard())

# Select gender
@bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
def gender_callback(call):
    chat_id = call.from_user.id
    message_id = call.message.message_id
    data = call.data.split('_')[1]  # Extract the target identifier
    with user_lock:
        if user_joined(chat_id):
            if data == 'boy':
                bot.answer_callback_query(call.id)
                gender = "پسر"
                add_user(chat_id, gender)
                bot.edit_message_text("جنس مخالفتو جستجو کن😍", chat_id, message_id, reply_markup=search_keyboard())
            elif data == 'girl':
                bot.answer_callback_query(call.id)
                gender = "دختر"
                add_user(chat_id, gender)
                bot.edit_message_text("جنس مخالفتو جستجو کن😍", chat_id, message_id, reply_markup=search_keyboard())
            else:
                bot.answer_callback_query(call.id, 'انتخاب شما نامعتبر است، لطفا از گزینه ها برای انتخابتان استفاده کنید!')
        else:
                bot.send_message(chat_id, 'لطفا در کانال ما عضو بشید تا از قابلیت های این بات استفاده کنید❤️', reply_markup=check_user_joined_keyboard())

# Find
@bot.callback_query_handler(func=lambda call: call.data == 'search')
def search_callback(call):
    chat_id = call.from_user.id
    with user_lock:
        if user_joined(chat_id):
           gen = get_user(chat_id)
           if check_state(chat_id) == 'off':
              update_state(chat_id, "waiting")
              partner_id = find(chat_id, gen)
              if partner_id:
                 update_partner(chat_id, partner_id)
                 update_partner(partner_id, chat_id)
                 bot.send_message(chat_id, "وصل شدی😎", reply_markup=leave_keyboard())
                 bot.send_message(partner_id, "وصل شدی😎", reply_markup=leave_keyboard())
                 update_state(chat_id, "chatting")
                 update_state(partner_id, "chatting")
              else:
                 update_state(chat_id, "waiting")
                 bot.send_message(chat_id, "در انتظار اتصال...")
           elif check_state(chat_id) == 'chatting':
               bot.send_message(chat_id, "شما در چت هستید! چت قبلی را ببندید و بعد جستجو کنید💛", reply_markup=leave_keyboard())
           elif check_state(chat_id) == 'waiting':
               update_state(chat_id, "off")
               bot.send_message(chat_id, "جستجو قبلی شما کنسل شد!", reply_markup=search_keyboard())
        else:
                bot.send_message(chat_id, 'لطفا در کانال ما عضو بشید تا از قابلیت های این بات استفاده کنید❤️', reply_markup=check_user_joined_keyboard())

# Chat
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'animation'])
def forward_message(message):
    chat_id = message.chat.id
    with user_lock:
        partner_id = get_partner(chat_id)
        if partner_id:
            if message.text == 'پایان چت':
                bot.send_message(chat_id, "چت شما پایان یافت!", reply_markup=search_keyboard())
                bot.send_message(partner_id, "چت شما پایان یافت!", reply_markup=search_keyboard())
                update_state(chat_id, "off")
                update_state(partner_id, "off")
                remove_partner(chat_id)
                remove_partner(partner_id)
            else:
                if message.content_type == 'text':
                   bot.send_message(partner_id, message.text, disable_notification=True)
                elif message.content_type == 'photo':
                   bot.send_photo(partner_id, message.photo[-1].file_id)
                elif message.content_type == 'video':
                   bot.send_video(partner_id, message.video.file_id)
                elif message.content_type == 'document':
                   bot.send_document(partner_id, message.document.file_id)
                elif message.content_type == 'audio':
                   bot.send_audio(partner_id, message.audio.file_id)
                elif message.content_type == 'voice':
                   bot.send_voice(partner_id, message.voice.file_id)
                elif message.content_type == 'sticker':
                   bot.send_sticker(partner_id, message.sticker.file_id)
                elif message.content_type == 'animation':
                   bot.send_animation(partner_id, message.animation.file_id)
                else:
                   bot.send_message(chat_id, "این پیام مجاز نیست!")
        else:
            bot.send_message(chat_id, "شما به کسی متصل نیستید!", reply_markup=search_keyboard())

# Start the bot
bot.polling(none_stop=True)