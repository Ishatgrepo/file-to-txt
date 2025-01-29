import os
import asyncio
from telegram import Update, Document
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler

# Constants for conversation states
SPLIT_LINES, SPLIT_WORDS = range(2)

# Group IDs for logging and dumping
LOG_GROUP_ID = -1002495370228  # Replace with your log group ID
DUMP_GROUP_ID = -1002495370228  # Replace with your dump group ID

# Owner ID for reboot access
OWNER_ID = 1094941160  # Replace with your Telegram user ID

# Function to handle the /start command
async def start(update: Update, context):
    await update.message.reply_text(
        "👋 Hi! I'm your bot.\n\n"
        "📄 Send me any file, and I'll extract its text content and send it back to you in chunks with a 5-second delay between messages!\n"
        "📊 After processing, I'll also show the number of lines and words in the file.\n\n"
        "🛠️ You can also split a `.txt` file into smaller files by specifying the number of lines or words per file."
    )

# Function to handle file uploads
async def handle_file(update: Update, context):
    file: Document = update.message.document

    # Show typing indicator while processing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Log the file upload to the log group
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

    # Check if the file is a .txt file
    if not file.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Only `.txt` files are supported for splitting.")
        os.remove(file_path)  # Clean up the file
        return

    # Ask the user how they want to split the file
    await update.message.reply_text(
        "📄 How would you like to split the file?\n\n"
        "1️⃣ Send `/lines <number>` to split by a specific number of lines per file.\n"
        "2️⃣ Send `/words <number>` to split by a specific number of words per file."
    )

    # Save the file path in the context for later use
    context.user_data["file_path"] = file_path

# Function to split the file by lines
async def split_by_lines(update: Update, context):
    try:
        num_lines = int(context.args[0])  # Get the number of lines from the command argument
        file_path = context.user_data.get("file_path")

        if not file_path:
            await update.message.reply_text("❌ No file found to split. Please upload a `.txt` file first.")
            return

        # Split the file into smaller files
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        split_files = []
        for i in range(0, len(lines), num_lines):
            split_file_path = f"{file_path}_part_{i // num_lines + 1}.txt"
            with open(split_file_path, "w", encoding="utf-8") as split_file:
                split_file.writelines(lines[i:i + num_lines])
            split_files.append(split_file_path)

        # Send the split files to the user
        for split_file in split_files:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(split_file, "rb"))
            os.remove(split_file)  # Clean up the split file after sending

        # Clean up the original file
        os.remove(file_path)
        await update.message.reply_text("✅ File successfully split by lines and sent to you!")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Please provide a valid number of lines. Example: `/lines 100`")
    except Exception as e:
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")

# Function to split the file by words
async def split_by_words(update: Update, context):
    try:
        num_words = int(context.args[0])  # Get the number of words from the command argument
        file_path = context.user_data.get("file_path")

        if not file_path:
            await update.message.reply_text("❌ No file found to split. Please upload a `.txt` file first.")
            return

        # Split the file into smaller files
        with open(file_path, "r", encoding="utf-8") as f:
            words = f.read().split()

        split_files = []
        for i in range(0, len(words), num_words):
            split_file_path = f"{file_path}_part_{i // num_words + 1}.txt"
            with open(split_file_path, "w", encoding="utf-8") as split_file:
                split_file.write(" ".join(words[i:i + num_words]))
            split_files.append(split_file_path)

        # Send the split files to the user
        for split_file in split_files:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(split_file, "rb"))
            os.remove(split_file)  # Clean up the split file after sending

        # Clean up the original file
        os.remove(file_path)
        await update.message.reply_text("✅ File successfully split by words and sent to you!")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Please provide a valid number of words. Example: `/words 500`")
    except Exception as e:
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")

# Main function to set up the bot
def main():
    bot_token = "7707224209:AAESxgYPv4YYF9LAeAe9vp3RNVz_YnFnGtY"  # Your bot token

    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(CommandHandler("lines", split_by_lines))
    app.add_handler(CommandHandler("words", split_by_words))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
