from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Define global variables for modes and owner ID
OWNER_ID = 1094941160
MODE = "text"  # Default mode is text
DUMP_GROUP = -1002495370228  # Dump group ID
SECOND_GROUP = -1002495370228  # Replace with the second group's ID

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /setmode to choose between Text Mode and Split Mode.")

# Set mode command
async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MODE
    if len(context.args) == 0:
        await update.message.reply_text("Please specify the mode: 'text' or 'split'.")
        return

    mode = context.args[0].lower()
    if mode in ["text", "split"]:
        MODE = mode
        await update.message.reply_text(f"Mode set to {MODE.capitalize()} Mode.")
    else:
        await update.message.reply_text("Invalid mode. Please choose 'text' or 'split'.")

# Handle text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MODE
    text = update.message.text

    if MODE == "text":
        # Automatically send text to both groups
        await context.bot.send_message(chat_id=SECOND_GROUP, text=text)
        await context.bot.send_message(chat_id=DUMP_GROUP, text=text)  # Auto-forward to dump group
    elif MODE == "split":
        await update.message.reply_text("Please upload a text file to split.")

# Handle file uploads
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MODE
    file = update.message.document

    if MODE == "split" and file.mime_type == "text/plain":
        # Download the file
        file_path = await file.get_file().download()

        # Split the file into parts
        with open(file_path, "r") as f:
            content = f.read()

        # Ask user for split size
        await update.message.reply_text("Please specify the number of parts to split the file into.")
        context.user_data["file_content"] = content
    else:
        await update.message.reply_text("Please switch to Split Mode to process text files.")

# Handle split size input
async def handle_split_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "file_content" not in context.user_data:
        await update.message.reply_text("No file content found. Please upload a text file first.")
        return

    try:
        num_parts = int(update.message.text)
        content = context.user_data["file_content"]
        lines = content.splitlines()
        part_size = len(lines) // num_parts

        # Split the content and send to groups
        for i in range(num_parts):
            part = "\n".join(lines[i * part_size:(i + 1) * part_size])
            await context.bot.send_message(chat_id=SECOND_GROUP, text=part)
            await context.bot.send_message(chat_id=DUMP_GROUP, text=part)  # Auto-forward to dump group

        await update.message.reply_text("File split and sent to groups successfully.")
    except ValueError:
        await update.message.reply_text("Invalid input. Please enter a valid number.")

# Reboot command (restricted to owner)
async def reboot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == OWNER_ID:
        await update.message.reply_text("Rebooting bot...")
        # Add your reboot logic here (e.g., restart the script or server)
    else:
        await update.message.reply_text("You are not authorized to use this command.")

# Main function to set up the bot
def main():
    application = Application.builder().token("8152265435:AAFo3fICFb6HwNA396hW09oZjqwQ0mpZgS0").build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setmode", set_mode))
    application.add_handler(CommandHandler("reboot", reboot))

    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Document.MimeType("text/plain"), handle_file))
    application.add_handler(MessageHandler(filters.Regex(r"^\d+$"), handle_split_size))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
