import sqlite3
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt

class UserTableWidget(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.init_ui()
        self.auto_seed_users()  # Automatically generate the 50 random users if empty
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()

        # Input Form
        form_layout = QHBoxLayout()
        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("User ID (e.g., 2024-0021)")
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("First Name")
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last Name")
        self.mi_input = QLineEdit()
        self.mi_input.setPlaceholderText("M.I.")
        self.mi_input.setMaxLength(1)
        self.rfid_input = QLineEdit()
        self.rfid_input.setPlaceholderText("RFID UID")
        
        btn_add = QPushButton("Add User")
        btn_add.clicked.connect(self.add_user)

        form_layout.addWidget(self.user_id_input)
        form_layout.addWidget(self.first_name_input)
        form_layout.addWidget(self.last_name_input)
        form_layout.addWidget(self.mi_input)
        form_layout.addWidget(self.rfid_input)
        form_layout.addWidget(btn_add)
        layout.addLayout(form_layout)

        # Table View
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["User ID", "First Name", "Last Name", "M.I.", "RFID UID"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def auto_seed_users(self):
        """Generates 50 distinct random users based on custom localized strings and custom ID ranges."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if users already exist to prevent repeated appending on every code execution
        cursor.execute("SELECT COUNT(*) FROM USER")
        if cursor.fetchone()[0] == 0:
            first_names = [
                "John", "Mark", "Angelo", "Christian", "Joseph", "Joshua", "Miguel", 
                "Gabriel", "James", "Patrick", "Francis", "Dave", "Kyle", "Michael", 
                "Mary", "Joy", "Maria", "Theresa", "Princess", "Sarah", "Nicole", 
                "Anne", "Christine", "Samantha", "Mae", "Hannah", "Grace", "Patricia", 
                "Marie", "Alyssa", "Ashley", "Jerome", "Renz", "Neil", "Bryan", 
                "Adrian", "Aljon", "Jenny", "Katrina", "Rochelle", "Camille", "Kyla", 
                "Charisse"
            ]

            last_names = [
                "Canoy", "Cailing", "Adlaon", "Jabagat", "Catian", "Daligdig", 
                "Ermac", "Cagampang", "Yacapin", "Flores", "Maglangit", 
                "Macalisang", "Actub", "Lluch"
            ]

            generated_ids = set()

            while len(generated_ids) < 50:
                # Select a random year between 2021 and 2026
                year = random.randint(2021, 2026)
                # Select a random numeric suffix from 0001 to 2999
                suffix = random.randint(1, 2999)
                custom_id = f"{year}-{suffix:04d}"
                generated_ids.add(custom_id)

            for uid in sorted(generated_ids):
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                mi = chr(random.randint(65, 90))  # Selects a random character capital letter A-Z
                rfid = f"RFID-{random.randint(100000, 999999)}" # Placeholder simulation string for RFIDs

                cursor.execute(
                    "INSERT INTO USER (user_id, first_name, last_name, m_i, rfid_uid) VALUES (?, ?, ?, ?, ?)",
                    (uid, fname, lname, mi, rfid)
                )
            conn.commit()
        conn.close()

    def load_data(self):
        """Loads users from database and automatically sorts them by ID number."""
        # 1. Temporarily turn off sorting while building rows
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Pull your 5 columns: user_id, first_name, last_name, m_i, rfid_uid
        cursor.execute("SELECT user_id, first_name, last_name, m_i, rfid_uid FROM USER")
        rows = cursor.fetchall()
        
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
                
        conn.close()
        
        # 2. Re-enable sorting and force sort by Column 0 (User ID)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        
    def add_user(self):
        uid = self.user_id_input.text().strip()
        fn = self.first_name_input.text().strip()
        ln = self.last_name_input.text().strip()
        mi = self.mi_input.text().strip().upper()
        rfid = self.rfid_input.text().strip()

        if uid and fn and ln:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO USER (user_id, first_name, last_name, m_i, rfid_uid) VALUES (?, ?, ?, ?, ?)",
                    (uid, fn, ln, mi, rfid if rfid else None)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # Prevents crashes if someone manually adds a User ID that already exists
                pass
            conn.close()
            
            self.user_id_input.clear()
            self.first_name_input.clear()
            self.last_name_input.clear()
            self.mi_input.clear()
            self.rfid_input.clear()
            self.load_data()