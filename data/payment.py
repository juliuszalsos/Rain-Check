import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

class PaymentsTab(QWidget):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f3f4f6;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Title
        tbl_lbl = QLabel("SYSTEM TRANSACTION REGISTER & RECEIPT RECORDS")
        tbl_lbl.setStyleSheet("color: #111827; font-weight: bold; font-size: 11px; letter-spacing: 0.5px;")
        layout.addWidget(tbl_lbl)

        # Simple static view table showing ledger logs
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Payment Receipt ID", "Penalty ID Ref", "Method", "Amount Settled", "Payment Date"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #111827;
                gridline-color: #f3f4f6;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f9fafb;
                color: #4b5563;
                padding: 8px;
                border: 1px solid #e5e7eb;
                font-weight: bold;
                font-size: 11px;
            }
            QTableCornerButton::section {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
            }
        """)
        self.table.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #cccccc;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #11224d;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        layout.addWidget(self.table)
        self.load_payments()

    def load_payments(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT payment_id, penalty_id, method, amount_paid, payment_date FROM payments ORDER BY payment_date DESC")
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(0)
            for idx, row in enumerate(rows):
                self.table.insertRow(idx)
                for col_idx, val in enumerate(row):
                    if col_idx == 3: # Amount column
                        item = QTableWidgetItem(f"₱{float(val):.2f}")
                    else:
                        item = QTableWidgetItem(str(val))
                    
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)

                    # Center aligns and formatting
                    if col_idx in [0, 1, 2, 4]:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        if col_idx == 0:
                            item.setForeground(QColor("#11224d"))
                    elif col_idx == 3:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        item.setForeground(QColor("#047857"))  # Forest green
                        bf = QFont()
                        bf.setBold(True)
                        item.setFont(bf)

                    self.table.setItem(idx, col_idx, item)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to retrieve ledger payments history: {e}")

