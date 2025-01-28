from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Define global variables for modes and owner ID
OWNER_ID = 1094941160
MODE = "text"  # Default mode is text
DUMP_GROUP = -1002495370228  # Dump group ID
SECOND_GROUP = -1002495370228  # Replace with the second group's ID

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Use /setmode to choose between Text Mode and Split Mode.")

# Set mode command
def set_mode(update: Update, context: CallbackContext):
    global MODE
    if len(context.args) == 0:
        update.message.reply_text("Please specify the mode: 'text' or 'split'.")
        return

    mode = context.args[0].lower()
    if mode in ["text", "split"]:
        MODE = mode
        update.message.reply_text(f"Mode set to {MODE.capitalize()} Mode.")
    else:
        update.message.reply_text("Invalid mode. Please choose 'text' or 'split'.")

# Handle text messages
def handle_text(update: Update, context: CallbackContext):
    global MODE
    text = update.message.text

    if MODE == "text":
        # Automatically send text to both groups
        context.bot.send_message(chat_id=SECOND_GROUP, text=text)
        context.bot.send_message(chat_id=DUMP_GROUP, text=text)  # Auto-forward to dump group
    elif MODE == "split":
        update.message.reply_text("Please upload a text file to split.")

# Handle file uploads
def handle_file(update: Update, context: CallbackContext):
    global MODE
    file = update.message.document

    if MODE == "split" and file.mime_type == "text/plain":
        # Download the file
        file_path = file.get_file().download()

        # Split the file into parts
        with open(file_path, "r") as f:
            content = f.read()

        # Ask user for split size
        update.message.reply_text("Please specify the number of parts to split the file into.")
        context.user_data["file_content"] = content
    else:
        update.message.reply_text("Please switch to Split Mode to process text files.")

# Handle split size input
def handle_split_size(update: Update, context: CallbackContext):
    if "file_content" not in context.user_data:
        update.message.reply_text("No file content found. Please upload a text file first.")
        return

    try:
        num_parts = int(update.message.text)
        content = context.user_data["file_content"]
        lines = content.splitlines()
        part_size = len(lines) // num_parts

        # Split the content and send to groups
        for i in range(num_parts):
            part = "\n".join(lines[i * part_size:(i + 1) * part_size])
            context.bot.send_message(chat_id=SECOND_GROUP, text=part)
            context.bot.send_message(chat_id=DUMP_GROUP, text=part)  # Auto-forward to dump group

        update.message.reply_text("File split and sent to groups successfully.")
    except ValueError:
        update.message.reply_text("Invalid input. Please enter a valid number.")

# Reboot command (restricted to owner)
def reboot(update: Update, context: CallbackContext):
    if update.message.from_user.id == OWNER_ID:
        update.message.reply_text("Rebooting bot...")
        # Add your reboot logic here (e.g., restart the script or server)
    else:
        update.message.reply_text("You are not authorized to use this command.")

# Main function to set up the bot
def main():
    updater = Updater("8152265435:AAGlI9uO1EGshFzcLiZIkCB013ZYF9pR5PM", use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("setmode", set_mode))
    dp.add_handler(CommandHandler("reboot", reboot))

    # Message handlers
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.document.mime_type("text/plain"), handle_file))
    dp.add_handler(MessageHandler(Filters.regex(r"^\d+$"), handle_split_size))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
