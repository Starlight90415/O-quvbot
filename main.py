import logging
import asyncio
import threading
from app import app as flask_app
from attendance_bot import setup_bot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def run_bot():
    """Start the Telegram bot in a separate thread with proper async handling."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start the bot
        bot_app = setup_bot()
        loop.run_until_complete(bot_app.initialize())
        loop.run_until_complete(bot_app.start())
        loop.run_until_complete(bot_app.updater.start_polling())
        
        logging.info("Bot started successfully in polling mode")
        loop.run_forever()
    except Exception as e:
        logging.error(f"Error starting bot: {e}")

def main():
    """Main function to run the bot and web server."""
    # Start the Telegram bot in a background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Export the Flask app for Gunicorn
    return flask_app

# For direct execution (not through Gunicorn)
if __name__ == '__main__':
    # Create a separate thread for the bot
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask app for development
    flask_app.run(host='0.0.0.0', port=5000, debug=True)

# Export the Flask app for Gunicorn
app = main()
