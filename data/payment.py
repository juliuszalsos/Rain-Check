import sqlite3
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QDateTime

class PaymentTableWidget(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()

        # ---- TOP CONTROLS SECTION ----
        controls_group = QGroupBox("Process Fine Collections")
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Penalty ID Input
        self.penalty_id_input = QLineEdit()
        self.penalty_id_input.setPlaceholderText("Penalty ID (e.g., DMG-052426-001)")
        self.penalty_id_input.setMinimumWidth(200)

        # Payment Method Dropdown
        self.method_dropdown = QComboBox()
        self.method_dropdown.addItems(["Cash", "GCash", "Maya"])
        self.method_dropdown.setMinimumWidth(100)

        # Amount Paid Input (Pre-filled with Peso Sign)
        self.amount_input = QLineEdit()
        self.amount_input.setText("₱")
        self.amount_input.setMinimumWidth(120)
        self.amount_input.textChanged.connect(self.ensure_peso_sign)

        # Action Button
        btn_pay = QPushButton("Process Payment")
        btn_pay.clicked.connect(self.process_payment)

        # Assemble Top Header Layout
        controls_layout.addWidget(QLabel("Penalty ID:"))
        controls_layout.addWidget(self.penalty_id_input)
        controls_layout.addWidget(QLabel("Method:"))
        controls_layout.addWidget(self.method_dropdown)
        controls_layout.addWidget(QLabel("Amount Paid:"))
        controls_layout.addWidget(self.amount_input)
        controls_layout.addWidget(btn_pay)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # ---- DATA TABLE LEDGER SECTION ----
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Payment ID", "Penalty ID", "Method", "Amount Paid", "Payment Date"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def ensure_peso_sign(self, text):
        """Forces the amount input box to always begin with a Peso sign."""
        if not text.startswith("₱"):
            self.amount_input.blockSignals(True)
            self.amount_input.setText("₱" + text.replace("₱", ""))
            self.amount_input.blockSignals(False)

    def load_data(self):
        """Loads payment log details directly from the database schema."""
        self.table.setRowCount(0)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT payment_id, penalty_id, method, amount_paid, payment_date FROM payments")
        rows = cursor.fetchall()
        
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(row_data):
                if col_idx == 3 and isinstance(data, (int, float)):
                    item_text = f"₱{data:.2f}"
                else:
                    item_text = str(data)
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(item_text))
                
        conn.close()

    def process_payment(self):
        pid = self.penalty_id_input.text().strip()
        method = self.method_dropdown.currentText()
        raw_amount = self.amount_input.text().replace("₱", "").strip()

        if not pid or not raw_amount:
            QMessageBox.warning(self, "Input Error", "Please provide a valid Penalty ID and Amount.")
            return

        try:
            input_amount = float(raw_amount)
        except ValueError:
            QMessageBox.critical(self, "Format Error", "Please input a valid numeric amount.")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT amount, paid_status FROM penalty WHERE penalty_id = ?", (pid,))
        penalty_record = cursor.fetchone()

        if not penalty_record:
            QMessageBox.critical(self, "Not Found", f"Penalty ID '{pid}' does not exist.")
            conn.close()
            return

        required_amount, current_status = penalty_record

        if current_status == "Paid":
            QMessageBox.information(self, "Settled", f"Penalty '{pid}' has already been paid.")
            conn.close()
            return

        if abs(input_amount - required_amount) > 0.01:
            QMessageBox.warning(self, "Payment Mismatch", f"Required Balance: ₱{required_amount:.2f}")
            conn.close()
            return

        # --- GENERATE TIMESTAMP & ID ---
        now = QDateTime.currentDateTime()
        date_prefix = now.toString("MMddyy")
        
        cursor.execute("SELECT payment_id FROM payments WHERE payment_id LIKE ? ORDER BY payment_id DESC LIMIT 1", (f"{date_prefix}-%",))
        last_payment = cursor.fetchone()
        new_sequence = int(last_payment[0].split("-")[1]) + 1 if last_payment else 1
        custom_payment_id = f"{date_prefix}-{new_sequence:03d}"
        
        # Capture the time of collection
        payment_timestamp_str = now.toString("yyyy-MM-dd hh:mm AP")

        # ---- DATABASE UPDATES ----
        cursor.execute("UPDATE penalty SET paid_status = 'Paid' WHERE penalty_id = ?", (pid,))
        cursor.execute("""
            INSERT INTO payments (payment_id, penalty_id, method, amount_paid, payment_date)
            VALUES (?, ?, ?, ?, ?)
        """, (custom_payment_id, pid, method, input_amount, payment_timestamp_str))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", f"Payment recorded!\nID: {custom_payment_id}\nProcessed: {payment_timestamp_str}")
        self.penalty_id_input.clear()
        self.amount_input.setText("₱")
        self.load_data()