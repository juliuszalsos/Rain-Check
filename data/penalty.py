import sqlite3
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QGroupBox)

class PenaltyTableWidget(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.init_ui()
        self.load_data()

    def init_ui(self):
        # Main container layout
        layout = QVBoxLayout()

        # Wrap table inside a clean Group Box container
        penalty_group = QGroupBox("System Fine Violations & Penalty Ledger")
        group_layout = QVBoxLayout()

        # Build out the simplified data grid view layout
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Penalty ID", "User ID", "Reason", "Date Issued", "Amount", "Status"
        ])
        
        # Format columns to cleanly fill out the entire window space automatically
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Assemble layouts
        group_layout.addWidget(self.table)
        penalty_group.setLayout(group_layout)
        layout.addWidget(penalty_group)
        
        self.setLayout(layout)

    def load_data(self):
        """Reads active structural infraction files straight from the database."""
        self.table.setRowCount(0)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Read the current record logs from the penalty table
        cursor.execute("SELECT penalty_id, user_id, penalty_reason, date_issued, amount, paid_status FROM penalty")
        rows = cursor.fetchall()
        
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(row_data):
                # Format the amount value to display cleanly with standard pricing decimals
                if col_idx == 4 and isinstance(data, (int, float)):
                    item_text = f"₱{data:.2f}"
                else:
                    item_text = str(data)
                    
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(item_text))
                
        conn.close()