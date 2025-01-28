import os
import asyncio
from telegram import Update, Document
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Group ID for logging
LOG_GROUP_ID = -1002495370228  # Replace with your group ID

# Owner ID for reboot access
OWNER_ID = 1094941160  # Replace with your Telegram user ID

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

    # Log the file upload to the group
    await context.bot.send_message(
        chat_id=LOG_GROUP_ID,
        text=f"📥 File received from @{update.effective_user.username or 'unknown'} in chat {update.effective_chat.id}:\n"
             f"📄 File Name: {file.file_name}\n"
             f"📦 File Size: {file.file_size} bytes"
    )

    # Download the file
    file_path = f"./{file.file_name}"
    try:
        telegram_file = await context.bot.get_file(file.file_id)  # Get the file object
        await telegram_file.download_to_drive(file_path)  # Download the file locally
    except Exception as e:
        error_message = f"❌ Failed to download the file: {str(e)}"
        await update.message.reply_text(error_message)
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=error_message)
        return

    # Try to extract text content from the file
    try:
        content = extract_text(file_path)
    except Exception as e:
        error_message = f"❌ Failed to extract text from the file: {str(e)}"
        await update.message.reply_text(error_message)
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=error_message)
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
        stats_message = (
            f"✅ File processed successfully!\n\n"
            f"📄 **Statistics:**\n"
            f"- **Lines:** {num_lines}\n"
            f"- **Words:** {num_words}"
        )
        await update.message.reply_text(stats_message)

        # Log the statistics and content to the group
        await context.bot.send_message(
            chat_id=LOG_GROUP_ID,
            text=f"📊 File processed successfully:\n\n"
                 f"📄 **Statistics:**\n"
                 f"- **Lines:** {num_lines}\n"
                 f"- **Words:** {num_words}\n\n"
                 f"📜 **Extracted Text:**\n{content[:4000]}"  # Limit to 4000 characters for Telegram
        )
    else:
        error_message = "❌ The file doesn't contain any readable text."
        await update.message.reply_text(error_message)
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text=error_message)

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

# Function to reboot the bot (owner-only command)
async def reboot(update: Update, context):
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        await update.message.reply_text("♻️ Rebooting the bot...")
        await context.bot.send_message(chat_id=LOG_GROUP_ID, text="♻️ Bot is being rebooted by the owner.")
        os.execl(sys.executable, sys.executable, *sys.argv)  # Restart the script
    else:
        await update.message.reply_text("❌ You are not authorized to use this command.")

# Main function to set up the bot
def main():
    bot_token = "8152265435:AAH9ZV4X8iCHyz31hgLwHCw_vqvHCs2akgE"  # Your bot token

    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reboot", reboot))  # Add reboot command
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    import sys
    main()
