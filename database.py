"""
Database module for PostgreSQL connection and query methods.
Handles interactions with expense tracker database tables.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """
    Database class for managing PostgreSQL connections and operations.
    """

    def __init__(self):
        """Initialize database connection parameters from environment variables."""
        self.db_config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': os.environ.get('DB_PORT', '5432'),
            'database': os.environ.get('DB_NAME'),
            'user': os.environ.get('DB_USER'),
            'password': os.environ.get('DB_PASSWORD'),
        }

        # For Cloud SQL connections (Unix socket)
        self.cloud_sql_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            psycopg2.connection: Database connection object
        """
        conn = None
        try:
            if self.cloud_sql_connection_name:
                # Cloud SQL connection via Unix socket
                unix_socket = f'/cloudsql/{self.cloud_sql_connection_name}'
                conn = psycopg2.connect(
                    host=unix_socket,
                    database=self.db_config['database'],
                    user=self.db_config['user'],
                    password=self.db_config['password']
                )
            else:
                # Standard TCP connection
                conn = psycopg2.connect(**self.db_config)

            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    # ==================== BANKS ====================

    def get_all_banks(self) -> List[Dict[str, Any]]:
        """
        Retrieve all banks from the database.

        Returns:
            List[Dict[str, Any]]: List of bank records
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM banks ORDER BY name")
                return [dict(row) for row in cur.fetchall()]

    def get_bank_by_id(self, bank_id: int) -> Optional[Dict[str, Any]]:
        """
        Get bank by ID.

        Args:
            bank_id: Bank ID

        Returns:
            Optional[Dict[str, Any]]: Bank record or None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM banks WHERE id = %s", (bank_id,))
                result = cur.fetchone()
                return dict(result) if result else None

    # ==================== CATEGORIES ====================

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """
        Retrieve all expense categories.

        Returns:
            List[Dict[str, Any]]: List of category records
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM categories ORDER BY name")
                return [dict(row) for row in cur.fetchall()]

    def add_category(self, name: str, description: Optional[str] = None) -> int:
        """
        Add a new expense category.

        Args:
            name: Category name
            description: Optional category description

        Returns:
            int: ID of newly created category
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO categories (name, description) VALUES (%s, %s) RETURNING id",
                    (name, description)
                )
                return cur.fetchone()[0]

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get category by name.

        Args:
            name: Category name

        Returns:
            Optional[Dict[str, Any]]: Category record or None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM categories WHERE LOWER(name) = LOWER(%s)", (name,))
                result = cur.fetchone()
                return dict(result) if result else None

    # ==================== MERCHANTS ====================

    def get_all_merchants(self) -> List[Dict[str, Any]]:
        """
        Retrieve all merchants.

        Returns:
            List[Dict[str, Any]]: List of merchant records
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM merchants ORDER BY name")
                return [dict(row) for row in cur.fetchall()]

    def add_merchant(self, name: str, category_id: Optional[int] = None) -> int:
        """
        Add a new merchant.

        Args:
            name: Merchant name
            category_id: Optional category ID

        Returns:
            int: ID of newly created merchant
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO merchants (name, category_id) VALUES (%s, %s) RETURNING id",
                    (name, category_id)
                )
                return cur.fetchone()[0]

    def get_merchant_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get merchant by name.

        Args:
            name: Merchant name

        Returns:
            Optional[Dict[str, Any]]: Merchant record or None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM merchants WHERE LOWER(name) = LOWER(%s)", (name,))
                result = cur.fetchone()
                return dict(result) if result else None

    # ==================== TRANSACTIONS ====================

    def add_transaction(
        self,
        user_id: int,
        amount: float,
        transaction_date: datetime,
        category_id: int,
        merchant_id: Optional[int] = None,
        bank_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> int:
        """
        Add a new transaction.

        Args:
            user_id: Telegram user ID
            amount: Transaction amount
            transaction_date: Date of transaction
            category_id: Category ID
            merchant_id: Optional merchant ID
            bank_id: Optional bank ID
            description: Optional transaction description

        Returns:
            int: ID of newly created transaction
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO transactions
                    (user_id, amount, transaction_date, category_id, merchant_id, bank_id, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, amount, transaction_date, category_id, merchant_id, bank_id, description)
                )
                return cur.fetchone()[0]

    def get_user_transactions(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a specific user.

        Args:
            user_id: Telegram user ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List[Dict[str, Any]]: List of transaction records
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        t.*,
                        c.name as category_name,
                        m.name as merchant_name,
                        b.name as bank_name
                    FROM transactions t
                    LEFT JOIN categories c ON t.category_id = c.id
                    LEFT JOIN merchants m ON t.merchant_id = m.id
                    LEFT JOIN banks b ON t.bank_id = b.id
                    WHERE t.user_id = %s
                    ORDER BY t.transaction_date DESC, t.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset)
                )
                return [dict(row) for row in cur.fetchall()]

    def get_monthly_summary(
        self,
        user_id: int,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        Get monthly expense summary for a user.

        Args:
            user_id: Telegram user ID
            year: Year
            month: Month (1-12)

        Returns:
            Dict[str, Any]: Summary with total and breakdown by category
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Total expenses
                cur.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0) as total
                    FROM transactions
                    WHERE user_id = %s
                    AND EXTRACT(YEAR FROM transaction_date) = %s
                    AND EXTRACT(MONTH FROM transaction_date) = %s
                    """,
                    (user_id, year, month)
                )
                total_result = cur.fetchone()
                total = float(total_result['total']) if total_result else 0.0

                # Breakdown by category
                cur.execute(
                    """
                    SELECT
                        c.name as category_name,
                        COALESCE(SUM(t.amount), 0) as amount,
                        COUNT(t.id) as transaction_count
                    FROM transactions t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE t.user_id = %s
                    AND EXTRACT(YEAR FROM t.transaction_date) = %s
                    AND EXTRACT(MONTH FROM t.transaction_date) = %s
                    GROUP BY c.name
                    ORDER BY amount DESC
                    """,
                    (user_id, year, month)
                )
                breakdown = [dict(row) for row in cur.fetchall()]

                return {
                    'total': total,
                    'breakdown': breakdown,
                    'year': year,
                    'month': month
                }

    # ==================== RECEIPTS ====================

    def add_receipt(
        self,
        user_id: int,
        merchant_id: Optional[int],
        receipt_date: datetime,
        total_amount: float,
        image_url: Optional[str] = None
    ) -> int:
        """
        Add a new receipt.

        Args:
            user_id: Telegram user ID
            merchant_id: Merchant ID
            receipt_date: Date of receipt
            total_amount: Total amount on receipt
            image_url: Optional URL to receipt image

        Returns:
            int: ID of newly created receipt
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO receipts
                    (user_id, merchant_id, receipt_date, total_amount, image_url)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, merchant_id, receipt_date, total_amount, image_url)
                )
                return cur.fetchone()[0]

    # ==================== RECEIPT ITEMS ====================

    def add_receipt_item(
        self,
        receipt_id: int,
        item_name: str,
        quantity: float,
        unit_price: float,
        total_price: float,
        category_id: Optional[int] = None
    ) -> int:
        """
        Add an item to a receipt.

        Args:
            receipt_id: Receipt ID
            item_name: Name of the item
            quantity: Quantity purchased
            unit_price: Price per unit
            total_price: Total price for this item
            category_id: Optional category ID

        Returns:
            int: ID of newly created receipt item
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO receipt_items
                    (receipt_id, item_name, quantity, unit_price, total_price, category_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (receipt_id, item_name, quantity, unit_price, total_price, category_id)
                )
                return cur.fetchone()[0]

    # ==================== UTILITY METHODS ====================

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
