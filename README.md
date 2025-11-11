# Telegram Expense Tracker Bot

A comprehensive expense tracking bot for Telegram, deployed on Google App Engine with PostgreSQL (Cloud SQL) integration.

## Features

- **Expense Management**: Record and track expenses with categorization
- **Transaction History**: View recent transactions with detailed information
- **Category Management**: Create and manage expense categories
- **Bank Integration**: View and manage bank accounts
- **Monthly Reports**: Generate detailed monthly expense summaries
- **Secure Database**: PostgreSQL integration via Google Cloud SQL

## Bot Commands

- `/start` - Introduction and help
- `/add_expense` - Record a new expense (interactive)
- `/view_transactions` - View recent transactions (last 10)
- `/add_category` - Create a new expense category (interactive)
- `/view_banks` - List available banks
- `/monthly_summary` - Generate monthly expense report
  - Usage: `/monthly_summary` (current month) or `/monthly_summary YYYY MM`

## Project Structure

```
bot-telegram/
├── main.py              # Telegram bot webhook handler
├── database.py          # PostgreSQL connection and query methods
├── app.yaml            # Google App Engine configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Prerequisites

1. **Python 3.11+**
2. **Google Cloud Platform Account**
3. **Telegram Bot Token** (from [@BotFather](https://t.me/botfather))
4. **PostgreSQL Database** (Cloud SQL instance)

## Database Schema

The bot expects the following tables in your PostgreSQL database:

### banks
```sql
CREATE TABLE banks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### categories
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### merchants
```sql
CREATE TABLE merchants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### transactions
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    merchant_id INTEGER REFERENCES merchants(id),
    bank_id INTEGER REFERENCES banks(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### receipts
```sql
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    merchant_id INTEGER REFERENCES merchants(id),
    receipt_date TIMESTAMP NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### receipt_items
```sql
CREATE TABLE receipt_items (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER REFERENCES receipts(id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/bot-telegram.git
cd bot-telegram
```

### 2. Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Save the bot token provided

### 3. Set Up Google Cloud Platform

#### Create a Project
```bash
gcloud projects create your-project-id
gcloud config set project your-project-id
```

#### Enable Required APIs
```bash
gcloud services enable sqladmin.googleapis.com
gcloud services enable appengine.googleapis.com
```

#### Create Cloud SQL Instance
```bash
gcloud sql instances create expense-tracker-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1
```

#### Create Database
```bash
gcloud sql databases create expense_tracker --instance=expense-tracker-db
```

#### Create Database User
```bash
gcloud sql users create dbuser \
    --instance=expense-tracker-db \
    --password=your-secure-password
```

#### Get Connection Name
```bash
gcloud sql instances describe expense-tracker-db --format="get(connectionName)"
```

### 4. Initialize Database Schema

Connect to your Cloud SQL instance and run the SQL schema provided in the "Database Schema" section above.

```bash
# Using Cloud SQL Proxy
cloud_sql_proxy -instances=PROJECT_ID:REGION:INSTANCE_NAME=tcp:5432

# In another terminal, connect with psql
psql -h localhost -U dbuser -d expense_tracker
```

### 5. Configure Environment Variables

#### For Local Development
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

#### For App Engine Deployment
Edit `app.yaml` and set the environment variables in the `env_variables` section, or use Google Secret Manager for sensitive data.

### 6. Install Dependencies (Local Development)

```bash
pip install -r requirements.txt
```

### 7. Deploy to App Engine

```bash
gcloud app deploy
```

### 8. Set Webhook

After deployment, set the webhook URL:

```bash
# Visit this URL in your browser or use curl
curl https://your-project-id.appspot.com/set_webhook
```

Alternatively, set it manually:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-project-id.appspot.com/webhook"
```

## Local Development

### Using Flask Development Server

```bash
# Set environment variables
export $(cat .env | xargs)

# Run the application
python main.py
```

### Expose Local Server to Internet

For webhook testing, use ngrok or similar:

```bash
ngrok http 8080
# Update WEBHOOK_URL in .env with the ngrok URL
```

## Usage Examples

### Adding an Expense

1. Send `/add_expense` to the bot
2. Enter the amount (e.g., `25.50`)
3. Select a category from the inline keyboard
4. Select a merchant (or skip)
5. Enter a description (or skip)
6. Expense is saved!

### Viewing Transactions

Send `/view_transactions` to see your last 10 expenses with details.

### Monthly Summary

Send `/monthly_summary` for current month, or `/monthly_summary 2024 1` for January 2024.

## Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use Google Secret Manager** for production credentials
3. **Enable HTTPS only** - Already configured in `app.yaml`
4. **Use strong database passwords**
5. **Limit database user permissions**
6. **Regular security updates** - Keep dependencies updated

## Error Handling

The bot includes comprehensive error handling:
- Database connection errors are logged and user-friendly messages are shown
- Invalid input is validated with helpful error messages
- Transaction failures are rolled back automatically
- All errors are logged for debugging

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [Google Cloud Platform](https://cloud.google.com/) - Hosting and database infrastructure
- [PostgreSQL](https://www.postgresql.org/) - Database system
