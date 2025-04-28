import telegram
from telegram.ext import Updater, MessageHandler, Filters

def echo(update, context):
    chat_id = update.effective_chat.id
    print(f"Chat IDmu yaitu {chat_id}")
    

bot_token = "7807161260:AAHAnhLzPqLprHr_inS9ixhmb3jJwHxxdMI"


updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher


echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

# Start the bot
print("Coba kirim pesan ke bot telegram kamu...")
updater.start_polling()