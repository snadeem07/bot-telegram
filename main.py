"""
Telegram Expense Tracker Bot - Main Application
Webhook handler for Google App Engine deployment
"""

import os
import logging
from datetime import datetime
from typing import Optional

from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

from database import Database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize database
db = Database()

# Conversation states
AMOUNT, CATEGORY, MERCHANT, DATE, DESCRIPTION = range(5)
CATEGORY_NAME, CATEGORY_DESC = range(5, 7)

# Environment variables
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')


# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command - Bot introduction.

    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    welcome_message = f"""
👋 Welcome to Expense Tracker Bot, {user.first_name}!

I can help you track your expenses and manage your finances.

Available commands:
📝 /add_expense - Record a new expense
📊 /view_transactions - View your recent transactions
🏷️ /add_category - Create a new expense category
🏦 /view_banks - List available banks
📈 /monthly_summary - Get your monthly expense report
❓ /help - Show this help message

Let's start tracking your expenses!
    """
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /help command.

    Args:
        update: Telegram update object
        context: Callback context
    """
    await start_command(update, context)


# ==================== ADD EXPENSE CONVERSATION ====================

async def add_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the add expense conversation.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: Next conversation state
    """
    await update.message.reply_text(
        "💰 Let's add a new expense!\n\n"
        "Please enter the amount (e.g., 25.50):"
    )
    return AMOUNT


async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle expense amount input.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: Next conversation state
    """
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text(
                "❌ Amount must be greater than 0. Please try again:"
            )
            return AMOUNT

        context.user_data['expense_amount'] = amount

        # Get categories
        categories = db.get_all_categories()
        if not categories:
            await update.message.reply_text(
                "❌ No categories found. Please add a category first using /add_category"
            )
            return ConversationHandler.END

        # Create keyboard with categories
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(cat['name'], callback_data=f"cat_{cat['id']}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"✅ Amount: ${amount:.2f}\n\n"
            "Please select a category:",
            reply_markup=reply_markup
        )
        return CATEGORY

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please enter a valid number:"
        )
        return AMOUNT


async def expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle category selection.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: Next conversation state
    """
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.split('_')[1])
    context.user_data['expense_category_id'] = category_id

    # Get category name
    categories = db.get_all_categories()
    category_name = next((c['name'] for c in categories if c['id'] == category_id), 'Unknown')

    # Get merchants
    merchants = db.get_all_merchants()

    keyboard = [[InlineKeyboardButton("Skip", callback_data="merchant_skip")]]
    for merchant in merchants:
        keyboard.append([InlineKeyboardButton(merchant['name'], callback_data=f"mer_{merchant['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"✅ Category: {category_name}\n\n"
        "Please select a merchant (or skip):",
        reply_markup=reply_markup
    )
    return MERCHANT


async def expense_merchant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle merchant selection.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: Next conversation state
    """
    query = update.callback_query
    await query.answer()

    if query.data == "merchant_skip":
        context.user_data['expense_merchant_id'] = None
        merchant_name = "None"
    else:
        merchant_id = int(query.data.split('_')[1])
        context.user_data['expense_merchant_id'] = merchant_id
        merchants = db.get_all_merchants()
        merchant_name = next((m['name'] for m in merchants if m['id'] == merchant_id), 'Unknown')

    await query.edit_message_text(
        f"✅ Merchant: {merchant_name}\n\n"
        "Please enter a description (or type 'skip' to skip):"
    )
    return DESCRIPTION


async def expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle description input and save expense.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: End conversation
    """
    description = update.message.text if update.message.text.lower() != 'skip' else None
    user_id = update.effective_user.id

    try:
        # Save transaction
        transaction_id = db.add_transaction(
            user_id=user_id,
            amount=context.user_data['expense_amount'],
            transaction_date=datetime.now(),
            category_id=context.user_data['expense_category_id'],
            merchant_id=context.user_data.get('expense_merchant_id'),
            description=description
        )

        await update.message.reply_text(
            f"✅ Expense added successfully!\n\n"
            f"💰 Amount: ${context.user_data['expense_amount']:.2f}\n"
            f"🆔 Transaction ID: {transaction_id}\n\n"
            f"Use /view_transactions to see your recent expenses."
        )

    except Exception as e:
        logger.error(f"Error adding transaction: {e}")
        await update.message.reply_text(
            f"❌ Error adding expense: {str(e)}\n\n"
            f"Please try again later."
        )

    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel the current conversation.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: End conversation
    """
    await update.message.reply_text(
        "❌ Operation cancelled."
    )
    context.user_data.clear()
    return ConversationHandler.END


# ==================== VIEW TRANSACTIONS ====================

async def view_transactions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /view_transactions command.

    Args:
        update: Telegram update object
        context: Callback context
    """
    user_id = update.effective_user.id

    try:
        transactions = db.get_user_transactions(user_id, limit=10)

        if not transactions:
            await update.message.reply_text(
                "📭 No transactions found.\n\n"
                "Use /add_expense to add your first expense!"
            )
            return

        message = "📊 Your Recent Transactions:\n\n"
        for i, txn in enumerate(transactions, 1):
            date = txn['transaction_date'].strftime('%Y-%m-%d') if txn['transaction_date'] else 'N/A'
            amount = f"${txn['amount']:.2f}"
            category = txn.get('category_name', 'N/A')
            merchant = txn.get('merchant_name', 'N/A')
            description = txn.get('description', '')

            message += f"{i}. {date} - {amount}\n"
            message += f"   🏷️ {category}"
            if merchant and merchant != 'N/A':
                message += f" | 🏪 {merchant}"
            if description:
                message += f"\n   📝 {description}"
            message += "\n\n"

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        await update.message.reply_text(
            f"❌ Error fetching transactions: {str(e)}"
        )


# ==================== ADD CATEGORY ====================

async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the add category conversation.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: Next conversation state
    """
    await update.message.reply_text(
        "🏷️ Let's add a new category!\n\n"
        "Please enter the category name:"
    )
    return CATEGORY_NAME


async def category_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle category name input.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: Next conversation state
    """
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "❌ Category name cannot be empty. Please try again:"
        )
        return CATEGORY_NAME

    # Check if category already exists
    existing = db.get_category_by_name(name)
    if existing:
        await update.message.reply_text(
            f"❌ Category '{name}' already exists!\n\n"
            f"Please choose a different name:"
        )
        return CATEGORY_NAME

    context.user_data['category_name'] = name
    await update.message.reply_text(
        f"✅ Category name: {name}\n\n"
        "Please enter a description (or type 'skip' to skip):"
    )
    return CATEGORY_DESC


async def category_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle category description and save category.

    Args:
        update: Telegram update object
        context: Callback context

    Returns:
        int: End conversation
    """
    description = update.message.text if update.message.text.lower() != 'skip' else None

    try:
        category_id = db.add_category(
            name=context.user_data['category_name'],
            description=description
        )

        await update.message.reply_text(
            f"✅ Category '{context.user_data['category_name']}' added successfully!\n"
            f"🆔 Category ID: {category_id}"
        )

    except Exception as e:
        logger.error(f"Error adding category: {e}")
        await update.message.reply_text(
            f"❌ Error adding category: {str(e)}"
        )

    context.user_data.clear()
    return ConversationHandler.END


# ==================== VIEW BANKS ====================

async def view_banks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /view_banks command.

    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        banks = db.get_all_banks()

        if not banks:
            await update.message.reply_text(
                "🏦 No banks found in the database."
            )
            return

        message = "🏦 Available Banks:\n\n"
        for i, bank in enumerate(banks, 1):
            message += f"{i}. {bank['name']}\n"
            if bank.get('description'):
                message += f"   {bank['description']}\n"

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error fetching banks: {e}")
        await update.message.reply_text(
            f"❌ Error fetching banks: {str(e)}"
        )


# ==================== MONTHLY SUMMARY ====================

async def monthly_summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /monthly_summary command.

    Args:
        update: Telegram update object
        context: Callback context
    """
    user_id = update.effective_user.id
    now = datetime.now()

    # Allow user to specify month/year or use current
    args = context.args
    if args and len(args) >= 2:
        try:
            year = int(args[0])
            month = int(args[1])
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid format. Use: /monthly_summary YYYY MM\n"
                "Example: /monthly_summary 2024 1"
            )
            return
    else:
        year = now.year
        month = now.month

    try:
        summary = db.get_monthly_summary(user_id, year, month)

        if summary['total'] == 0:
            await update.message.reply_text(
                f"📈 Monthly Summary for {year}-{month:02d}\n\n"
                f"No expenses recorded for this month."
            )
            return

        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]

        message = f"📈 Monthly Summary - {month_names[month-1]} {year}\n\n"
        message += f"💰 Total Expenses: ${summary['total']:.2f}\n\n"
        message += "📊 Breakdown by Category:\n\n"

        for item in summary['breakdown']:
            category = item['category_name'] or 'Uncategorized'
            amount = item['amount']
            count = item['transaction_count']
            percentage = (amount / summary['total'] * 100) if summary['total'] > 0 else 0

            message += f"🏷️ {category}\n"
            message += f"   ${amount:.2f} ({percentage:.1f}%) - {count} transaction(s)\n\n"

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error generating monthly summary: {e}")
        await update.message.reply_text(
            f"❌ Error generating summary: {str(e)}"
        )


# ==================== ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors.

    Args:
        update: Telegram update object
        context: Callback context
    """
    logger.error(f"Update {update} caused error {context.error}")


# ==================== APPLICATION SETUP ====================

def create_application() -> Application:
    """
    Create and configure the Telegram bot application.

    Returns:
        Application: Configured bot application
    """
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add expense conversation handler
    add_expense_conv = ConversationHandler(
        entry_points=[CommandHandler('add_expense', add_expense_start)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)],
            CATEGORY: [CallbackQueryHandler(expense_category)],
            MERCHANT: [CallbackQueryHandler(expense_merchant)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_description)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
    )

    # Add category conversation handler
    add_category_conv = ConversationHandler(
        entry_points=[CommandHandler('add_category', add_category_start)],
        states={
            CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_name)],
            CATEGORY_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_description)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
    )

    # Add handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(add_expense_conv)
    application.add_handler(CommandHandler('view_transactions', view_transactions_command))
    application.add_handler(add_category_conv)
    application.add_handler(CommandHandler('view_banks', view_banks_command))
    application.add_handler(CommandHandler('monthly_summary', monthly_summary_command))

    # Add error handler
    application.add_error_handler(error_handler)

    return application


# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'Telegram Expense Tracker Bot is running'})


@app.route('/webhook', methods=['POST'])
async def webhook():
    """
    Handle incoming webhook requests from Telegram.

    Returns:
        Response: JSON response
    """
    try:
        application = create_application()
        await application.initialize()

        # Process update
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)

        await application.shutdown()

        return jsonify({'status': 'ok'})

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/set_webhook', methods=['GET', 'POST'])
async def set_webhook():
    """
    Set the webhook URL for the Telegram bot.

    Returns:
        Response: JSON response
    """
    try:
        application = create_application()
        await application.initialize()

        webhook_url = f"{WEBHOOK_URL}/webhook"
        await application.bot.set_webhook(url=webhook_url)

        await application.shutdown()

        return jsonify({
            'status': 'ok',
            'message': f'Webhook set to {webhook_url}'
        })

    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
