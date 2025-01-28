import os
import asyncio
from telegram import Update, Document
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Function to handle the /start command
async def start(update: Update, context):
    await update.message.reply_text(
        "👋 Hi! I'm your bot.\n\n"
        "📄 Send me any file, and I'll extract its text content and send it back to you in chunks with a 5-second delay between messages!\n"
        "📊 After processing, I'll also show the number of lines and words in the file."
    )

# Function to handle file uploads
async def handle_file(update: Update, context):
    file: Document = update.message.document

    # Show typing indicator while processing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Download the file
    file_path = f"{file.file_name}"
    try:
        await file.get_file().download_to_drive(file_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to download the file: {str(e)}")
        return

    # Try to extract text content from the file
    try:
        content = extract_text(file_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to extract text from the file: {str(e)}")
        os.remove(file_path)  # Clean up the file
        return

    # Clean up the file after processing
    os.remove(file_path)

    # Send the content back to the user in chunks
    if content.strip():
        await send_large_text(update, context, content)

        # Calculate and display the number of lines and words
        num_lines = len(content.splitlines())
        num_words = len(content.split())
        await update.message.reply_text(
            f"✅ File processed successfully!\n\n"
            f"📄 **Statistics:**\n"
            f"- **Lines:** {num_lines}\n"
            f"- **Words:** {num_words}"
        )
    else:
        await update.message.reply_text("❌ The file doesn't contain any readable text.")

# Function to extract text from a file
def extract_text(file_path):
    # Check the file extension
    _, file_extension = os.path.splitext(file_path)

    # Handle .txt files
    if file_extension.lower() == ".txt":
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    # Handle other file types (e.g., PDF, DOCX)
    if file_extension.lower() == ".pdf":
        from PyPDF2 import PdfReader
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

    if file_extension.lower() in [".docx", ".doc"]:
        from docx import Document
        doc = Document(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    # Handle unsupported file types
    raise ValueError("Unsupported file type. Please upload a .txt, .pdf, or .docx file.")

# Function to send large text with a 5-second delay
async def send_large_text(update: Update, context, text):
    chunk_size = 4096
    for i in range(0, len(text), chunk_size):
        await update.message.reply_text(text[i:i + chunk_size])
        await asyncio.sleep(5)  # Add a 5-second delay between messages

# Main function to set up the bot
def main():
    bot_token = "8152265435:AAEyz22gisoXyUoY7wpdCN4NLAJNpzGuRag"  # Your bot token

    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
