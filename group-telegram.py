import os
import mysql.connector
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

# إعداد القروبات
BAHRAIN_GROUP_LINK = "@Rashed_bahrain"
OTHER_GROUP_LINK = "@Rashed_GCC"

# الأسئلة
QUESTIONS = [
    ("شنو جنسيتك؟", ["بحريني", "سعودي", "إماراتي", "كويتي", "قطري", "عُماني", "دول أخرى"]),
    ("كم عمرك؟", ["10-15 سنة", "16-20 سنة", "21-35 سنة", "36-46 سنة", "47+"]),
    ("شنو جنسك؟", ["ذكر", "أنثى"]),
    ("هل أنت مقيم في البحرين؟", ["نعم", "لا"])
]

# إعداد الاتصال بقاعدة بيانات MySQL
def connect_to_database():
    connection = mysql.connector.connect(
        host=os.getenv("mysql.railway.internal"),
        user=os.getenv("root"),
        password=os.getenv("dvetBSQBIlISKihNMrmDNPUMUPTvVMGQ"),
        database=os.getenv("railway"),
        port=os.getenv("3306")
    )
    return connection

# إنشاء الجدول إذا لم يكن موجودًا
def initialize_database():
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            add_date TIMESTAMP,
            username VARCHAR(255),
            nationality VARCHAR(50),
            age VARCHAR(50),
            gender VARCHAR(10),
            resident VARCHAR(10),
            phone_number VARCHAR(20)
        )
    ''')
    connection.commit()
    cursor.close()
    connection.close()

# حفظ البيانات في قاعدة البيانات
def save_to_database(username, answers, phone_number=None):
    connection = connect_to_database()
    cursor = connection.cursor()
    add_date = datetime.now()
    nationality, age, gender, resident = answers

    cursor.execute('''
        INSERT INTO responses (add_date, username, nationality, age, gender, resident, phone_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (add_date, username, nationality, age, gender, resident, phone_number if phone_number else None))

    connection.commit()
    cursor.close()
    connection.close()

# رسالة ترحيب أولية
async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("مرحباً بك في البوت! اضغط /start للبدء في الاستبيان.")

# رسالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["answers"] = []
    await update.message.reply_text("مرحباً! سأطرح عليك سلسلة من الأسئلة لتوجيهك إلى القروب المناسب. أجب على الأسئلة التالية.")
    await ask_question(update, context)

# طرح السؤال التالي
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    answers = context.user_data["answers"]
    question, options = QUESTIONS[len(answers)]
    buttons = [[InlineKeyboardButton(option, callback_data=option)] for option in options]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(question, reply_markup=reply_markup)

# التعامل مع الإجابات
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["answers"].append(query.data)

    if len(context.user_data["answers"]) < len(QUESTIONS):
        await ask_question(query, context)
    else:
        await finish_quiz(query, context)

# إنهاء الاستبيان وحفظ البيانات
async def finish_quiz(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = query.from_user
    answers = context.user_data["answers"]
    nationality, _, _, resident = answers

    group_link = BAHRAIN_GROUP_LINK if nationality == "بحريني" else OTHER_GROUP_LINK

    # حفظ بيانات المستخدم في قاعدة البيانات
    phone_number = query.message.contact.phone_number if query.message.contact else None
    save_to_database(user.username, answers, phone_number)

    await query.message.reply_text(f"شكرًا لإجابتك على الأسئلة! يمكنك الانضمام إلى القروب المناسب من هنا: {group_link}")

# إعداد التطبيق
def main() -> None:
    # إنشاء الجدول عند بدء التشغيل
    initialize_database()

    app = Application.builder().token("7324354293:AAESUs8cyUVS6lt1TXE3hNVx4uC3u1nBSfU").build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, welcome_message))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_answer))

    app.run_polling()

if __name__ == "__main__":
    main()
