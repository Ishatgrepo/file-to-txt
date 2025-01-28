import os
import mimetypes
import asyncio  # For adding delays
from gtts import gTTS  # For text-to-speech
from PyPDF2 import PdfReader  # For PDF file reading
from docx import Document  # For Word document reading
import pytesseract  # For OCR (install Tesseract OCR separately)
from PIL import Image  # For image processing
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# File size limit in bytes (5 MB)
FILE_SIZE_LIMIT = 5 * 1024 * 1024

# Function to handle the /start command
async def start(update: Update, context):
    await update.message.reply_text(
        "👋 Hello! I'm your enhanced bot.\n\n"
        "📄 Send me any file (e.g., .txt, .pdf, .docx, .xlsx, images), and I'll extract its content for you. "
        "You can also convert the text to speech or download the file!"
    )

# Function to handle file uploads
async def handle_file(update: Update, context):
    # Get the file information
    file = update.message.document

    # Check if the file is too large
    if file.file_size > FILE_SIZE_LIMIT:
        await update.message.reply_text("❌ The file is too large! Please send a file smaller than 5 MB.")
        return

    # Show typing indicator while processing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Download the file
    file_path = f"{file.file_name}"
    await file.get_file().download_to_drive(file_path)

    # Detect the file type
    mime_type, _ = mimetypes.guess_type(file_path)
    content = None

    try:
        # Process the file based on its type
        if file.file_name.endswith('.txt'):
            with open(file_path, 'r') as f:
                content = f.read()
        elif file.file_name.endswith('.pdf'):
            reader = PdfReader(file_path)
            content = "\n".join(page.extract_text() for page in reader.pages)
        elif file.file_name.endswith('.docx'):
            doc = Document(file_path)
            content = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        elif mime_type and mime_type.startswith('image'):
            image = Image.open(file_path)
            content = pytesseract.image_to_string(image)
        else:
            content = "❌ Unsupported file type. I can only process .txt, .pdf, .docx, and images."

    except Exception as e:
        content = f"❌ An error occurred while processing the file: {str(e)}"

    # Clean up the file after processing
    os.remove(file_path)

    # Send the content back to the user
    if content:
        await send_long_message(update, context, content)

        # Add inline keyboard for further options
        keyboard = [
            [InlineKeyboardButton("🎧 Convert to Audio", callback_data=f"convert_audio|{content[:1000]}")],
            [InlineKeyboardButton("📤 Share Again", callback_data="share_again")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("What would you like to do next?", reply_markup=reply_markup)

# Function to send long messages with flood control
async def send_long_message(update: Update, context, text):
    # Telegram has a 4096-character limit per message
    chunk_size = 4096
    for i in range(0, len(text), chunk_size):
        await update.message.reply_text(text[i:i + chunk_size])
        await asyncio.sleep(2)  # Add a 2-second delay between messages to avoid flooding [[2]][[8]]

# Function to handle inline keyboard button clicks
async def button_click(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Parse the callback data
    data = query.data
    if data.startswith("convert_audio"):
        # Extract the text content (limited to 1000 characters for simplicity)
        text = data.split("|")[1]

        # Generate audio using gTTS
        tts = gTTS(text)
        audio_path = "output_audio.mp3"
        tts.save(audio_path)

        # Send the audio file to the user
        await query.message.reply_audio(audio=open(audio_path, 'rb'), caption="🎧 Here is your text as audio!")
        
        # Clean up the audio file
        os.remove(audio_path)

    elif data == "share_again":
        await query.message.reply_text("📄 You can send me another file anytime!")

# Main function to set up the bot
def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    bot_token = "8152265435:AAH9ex75KOmXl6lb_M79EAQgUvnPjbfkYUA"

    # Create the bot application
    app = ApplicationBuilder().token(bot_token).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(CallbackQueryHandler(button_click))

    # Run the bot
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
