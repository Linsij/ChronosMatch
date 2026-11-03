
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


class TradeLedger:
    def __init__(self, db_path="data/trades.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()

        self.connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )

        self.initialize()

    def initialize(self):
        with self.lock:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buy_order_id INTEGER NOT NULL,
                    sell_order_id INTEGER NOT NULL,
                    execution_price INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    executed_at TEXT NOT NULL
                )
            """)
            self.connection.commit()

    def insert_trades(self, trades):
        if not trades:
            return 0

        timestamp = datetime.now(timezone.utc).isoformat()

        records = [
            (buy_id, sell_id, price, quantity, timestamp)
            for buy_id, sell_id, price, quantity in trades
        ]

        with self.lock:
            self.connection.executemany("""
                INSERT INTO trades (
                    buy_order_id,
                    sell_order_id,
                    execution_price,
                    quantity,
                    executed_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, records)

            self.connection.commit()

        return len(records)

    def get_all_trades(self):
        with self.lock:
            cursor = self.connection.execute("""
                SELECT buy_order_id, sell_order_id,
                       execution_price, quantity, executed_at
                FROM trades
                ORDER BY id
            """)
            return cursor.fetchall()

    def count_trades(self):
        with self.lock:
            cursor = self.connection.execute(
                "SELECT COUNT(*) FROM trades"
            )
            return cursor.fetchone()[0]

    def close(self):
        with self.lock:
            self.connection.close()

