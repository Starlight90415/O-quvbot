import logging
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from sheets_manager import GoogleSheetsManager
from config import TELEGRAM_TOKEN

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Google Sheets manager
sheets_manager = GoogleSheetsManager()

# Conversation states
NAME, PHONE, SUBJECT = range(3)
STUDENT_ID, DATE, AMOUNT = range(3, 6)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    keyboard = [
        ["/royxat", "/davomat"],
        ["/tolov", "/hisobot"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Salom, {user.first_name}! Siz botga muvaffaqiyatli kirdingiz.\n\n"
        f"Bo'limlardan birini tanlang:\n"
        f"• /royxat – o'quvchi ma'lumotlarini kiritish\n"
        f"• /davomat – o'quvchining darsga kelganini belgisi\n"
        f"• /tolov – to'lov sanasi va summasi yozish\n"
        f"• /hisobot – o'quvchilar hisoboti",
        reply_markup=reply_markup
    )
    logger.info(f"User {user.id} ({user.username}) started the bot")

async def attendance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Record attendance when the command /davomat is issued."""
    user = update.effective_user
    username = user.username or user.first_name or "NoName"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Record attendance in Google Sheets
        sheets_manager.record_attendance(str(user.id), username, "Davomat", date_str)
        await update.message.reply_text("✅ Davomatingiz yozildi!")
        logger.info(f"Recorded attendance for user {user.id} ({username})")
    except Exception as e:
        logger.error(f"Failed to record attendance: {e}")
        await update.message.reply_text("❌ Davomatingizni yozishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the student registration process."""
    await update.message.reply_text(
        "O'quvchi ro'yxatga olish uchun ma'lumotlarni kiriting.\n"
        "Avval, o'quvchining to'liq ismini kiriting:"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the student's name and ask for phone number."""
    context.user_data["name"] = update.message.text
    await update.message.reply_text(
        "O'quvchining telefon raqamini kiriting:"
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the student's phone and ask for subject."""
    context.user_data["phone"] = update.message.text
    
    # Fan tanlash uchun tugmalar yaratish
    keyboard = [
        ["Matematika", "Fizika"],
        ["Ingliz tili", "Rus tili"],
        ["Kimyo", "Biologiya"],
        ["Informatika", "Tarix"],
        ["Ona tili", "Adabiyot"],
        ["Geografiya", "Chizmachilik"],
        ["Musiqa", "Jismoniy tarbiya"],
        ["Boshqa..."]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "📚 O'quvchi qaysi fan bo'yicha o'qiydi?\n"
        "Quyidagi fanlardan birini tanlang yoki o'zingiz kiriting:",
        reply_markup=reply_markup
    )
    return SUBJECT

async def get_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the student's subject and save all data."""
    user = update.effective_user
    
    # "Boshqa..." tugmasi bosilganmi yo'qmi tekshirish
    if update.message.text == "Boshqa...":
        await update.message.reply_text(
            "Iltimos, fan nomini o'zingiz kiriting:"
        )
        # O'quvchi boshqa fanni kiritishini kutamiz
        return SUBJECT
    
    context.user_data["subject"] = update.message.text
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Save student information to Google Sheets
        sheets_manager.record_student(
            str(user.id), 
            context.user_data["name"], 
            context.user_data["phone"], 
            context.user_data["subject"], 
            date_str
        )
        
        await update.message.reply_text(
            f"✅ O'quvchi ma'lumotlari saqlandi:\n"
            f"Ism: {context.user_data['name']}\n"
            f"Telefon: {context.user_data['phone']}\n"
            f"Fan: {context.user_data['subject']}"
        )
        logger.info(f"User {user.id} registered student {context.user_data['name']}")
    except Exception as e:
        logger.error(f"Failed to register student: {e}")
        await update.message.reply_text("❌ O'quvchi ma'lumotlarini saqlashda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")
    
    # Clear the user data
    context.user_data.clear()
    return ConversationHandler.END

async def payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the payment recording process."""
    await update.message.reply_text(
        "To'lov ma'lumotlarini kiritish uchun, avval o'quvchi ID raqamini kiriting:"
    )
    return STUDENT_ID

async def get_student_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the student ID and ask for payment date."""
    context.user_data["student_id"] = update.message.text
    await update.message.reply_text(
        "To'lov sanasini kiriting (kun.oy.yil formatida, masalan: 15.05.2025):"
    )
    return DATE

async def get_payment_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the payment date and ask for amount."""
    context.user_data["date"] = update.message.text
    await update.message.reply_text(
        "To'lov miqdorini so'm bilan kiriting (faqat raqamlar):"
    )
    return AMOUNT

async def get_payment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the payment amount and save all data."""
    user = update.effective_user
    context.user_data["amount"] = update.message.text
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Save payment information to Google Sheets
        sheets_manager.record_payment(
            str(user.id),
            context.user_data["student_id"],
            context.user_data["date"],
            context.user_data["amount"],
            current_date
        )
        
        await update.message.reply_text(
            f"✅ To'lov ma'lumotlari saqlandi:\n"
            f"O'quvchi ID: {context.user_data['student_id']}\n"
            f"Sana: {context.user_data['date']}\n"
            f"Miqdor: {context.user_data['amount']} so'm"
        )
        logger.info(f"User {user.id} recorded payment for student {context.user_data['student_id']}")
    except Exception as e:
        logger.error(f"Failed to record payment: {e}")
        await update.message.reply_text("❌ To'lov ma'lumotlarini saqlashda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")
    
    # Clear the user data
    context.user_data.clear()
    return ConversationHandler.END

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send a report for students."""
    user = update.effective_user
    
    try:
        # Get report from Google Sheets
        report_data = sheets_manager.get_student_report()
        
        if not report_data:
            await update.message.reply_text("⚠️ Hisobot uchun ma'lumotlar topilmadi.")
            return
        
        # Format report message
        report_message = "📊 O'quvchilar hisoboti:\n\n"
        for student in report_data:
            report_message += f"ID: {student['id']}\n"
            report_message += f"Ism: {student['name']}\n"
            report_message += f"Fan: {student['subject']}\n"
            report_message += f"Davomatlar soni: {student['attendance_count']}\n"
            report_message += f"So'ngi to'lov: {student['last_payment']} so'm\n"
            report_message += f"To'lov sanasi: {student['payment_date']}\n"
            report_message += "------------------------\n"
        
        await update.message.reply_text(report_message)
        logger.info(f"User {user.id} requested student report")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        await update.message.reply_text("❌ Hisobotni yaratishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "Jarayon bekor qilindi. Asosiy menyuga qaytish uchun /start buyrug'ini bosing."
    )
    # Clear the user data
    context.user_data.clear()
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(f"Exception while handling an update: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("Botda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

def setup_bot():
    """Set up the bot with handlers and start polling."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("davomat", attendance_command))
    application.add_handler(CommandHandler("hisobot", report_command))
    
    # Add conversation handlers for student registration
    register_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("royxat", register_command)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_subject)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(register_conv_handler)
    
    # Add conversation handlers for payment recording
    payment_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("tolov", payment_command)],
        states={
            STUDENT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_student_id)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment_date)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(payment_conv_handler)
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    return application
