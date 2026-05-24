import os
import sys
import sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox

# Explicitly direct Python to look inside the correct project directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.user import UserTableWidget
from data.umbrella import UmbrellaTableWidget
from data.penalty import PenaltyTableWidget
from data.payment import PaymentTableWidget

# This forces the database file to ALWAYS generate in your main project folder
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Raincheck.db')

def init_database():
    """Initializes the database using your precise 5-column layout configuration."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Users Table (Matches your seed script layout exactly)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS USER (
            user_id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            m_i TEXT,
            rfid_uid TEXT
        )
    """)

    # 2. Umbrellas Inventory Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Umbrella (
            umbrella_id TEXT PRIMARY KEY,
            current_status TEXT,
            condition TEXT
        )
    """)

    # 3. Rents Transaction Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rents (
            rent_id TEXT PRIMARY KEY,
            user_id TEXT,
            umbrella_id TEXT,
            rent_date TEXT,
            due_date TEXT,
            FOREIGN KEY(user_id) REFERENCES USER(user_id),
            FOREIGN KEY(umbrella_id) REFERENCES Umbrella(umbrella_id)
        )
    """)

    # 4. Returns Historical Log Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS returns (
            return_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rent_id TEXT,
            return_date TEXT,
            return_condition TEXT,
            FOREIGN KEY(rent_id) REFERENCES rents(rent_id)
        )
    """)

    # 5. Penalties Tracking Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS penalty (
            penalty_id TEXT PRIMARY KEY,
            user_id TEXT,
            penalty_reason TEXT,
            date_issued TEXT,
            amount REAL,
            paid_status TEXT,
            FOREIGN KEY(user_id) REFERENCES USER(user_id)
        )
    """)

    # 6. Payments Log Ledger Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            penalty_id TEXT,
            method TEXT,
            amount_paid REAL,
            payment_date TEXT,
            FOREIGN KEY(penalty_id) REFERENCES penalty(penalty_id)
        )
    """)

    conn.commit()
    conn.close()


class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Umbrella Management Database System")
        self.setGeometry(100, 100, 1000, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Build instances pointing directly to our unified DB location
        self.user_view = UserTableWidget(DB_FILE)
        self.umbrella_view = UmbrellaTableWidget(DB_FILE)
        self.penalty_view = PenaltyTableWidget(DB_FILE)
        self.payment_view = PaymentTableWidget(DB_FILE)

        self.tabs.addTab(self.user_view, "Users")
        self.tabs.addTab(self.umbrella_view, "Umbrellas & Rentals")
        self.tabs.addTab(self.penalty_view, "Penalties")
        self.tabs.addTab(self.payment_view, "Payments")

        self.tabs.currentChanged.connect(self.refresh_tab_data)

    def refresh_tab_data(self, index):
        try:
            if index == 0: self.user_view.load_data()
            elif index == 1: self.umbrella_view.load_all_data()
            elif index == 2: self.penalty_view.load_data()
            elif index == 3: self.payment_view.load_data()
        except Exception as e:
            print(f"Tab sync refresh note: {e}")


if __name__ == "__main__":
    init_database()
    
    app = QApplication(sys.argv)
    window = MainApplicationWindow()
    window.show()
    sys.exit(app.exec())