import os
import io
import logging
import PyPDF2
import google.generativeai as genai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, ConversationHandler
)

# Holatlar
CHAT, QUIZ = range(2)

# Tokenlarni olish
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! /chat yoki /quiz buyrug'ini tanlang.")

async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chat rejimi. Savolingizni yozing:")
    return CHAT

async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = model.generate_content(update.message.text)
    await update.message.reply_text(response.text)
    return CHAT

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("PDF fayl yuboring:")
    return QUIZ

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.document.file_id)
    file_bytes = await file.download_as_bytearray()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = "".join([page.extract_text() for page in pdf_reader.pages])
    
    prompt = f"Ushbu matn asosida 3 ta test tuz: {text[:5000]}"
    response = model.generate_content(prompt)
    await update.message.reply_text(response.text)
    return QUIZ

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bekor qilindi.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("chat", start_chat), CommandHandler("quiz", start_quiz)],
        states={
            CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat)],
            QUIZ: [MessageHandler(filters.Document.PDF, handle_pdf)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.run_polling()
