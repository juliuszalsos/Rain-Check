import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from datetime import datetime

class PenaltiesTab(QWidget):
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
        layout.setSpacing(15)

        # Control card
        control_card = QFrame()
        control_card.setObjectName("ControlCard")
        control_card.setStyleSheet("""
            QFrame#ControlCard {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        ctl_card_layout = QVBoxLayout(control_card)
        ctl_card_layout.setContentsMargins(16, 16, 16, 16)

        # Title
        ctl_title = QLabel("PENALTY MANAGEMENT WORKFLOW")
        ctl_title.setStyleSheet("color: #111827; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; padding-bottom: 4px;")
        ctl_card_layout.addWidget(ctl_title)

        # Control Row for paying fine
        ctl_layout = QHBoxLayout()
        ctl_layout.setSpacing(10)

        self.pay_btn = QPushButton("Process Payment for Selected Penalty")
        self.pay_btn.setStyleSheet("""
            QPushButton {
                background-color: #11224d;
                color: #ffffff;
                border: none;
                padding: 8px 18px;
                font-weight: bold;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1d3570;
            }
        """)
        self.pay_btn.clicked.connect(self.process_payment)

        ctl_layout.addWidget(self.pay_btn)
        ctl_layout.addStretch()
        
        ctl_card_layout.addLayout(ctl_layout)
        layout.addWidget(control_card)

        # List title
        table_lbl = QLabel("OUTSTANDING & SETTLED PENALTIES LEDGER")
        table_lbl.setStyleSheet("color: #111827; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-top: 5px;")
        layout.addWidget(table_lbl)

        # Table showing lists of fines / penalties
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Penalty ID", "User ID", "Reason", "Date Issued", "Amount (₱)", "Paid Status"])
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
        self.load_penalties()

    def load_penalties(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT penalty_id, user_id, penalty_reason, date_issued, amount, paid_status FROM penalty ORDER BY date_issued DESC")
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(0)
            for idx, row in enumerate(rows):
                self.table.insertRow(idx)
                for col_idx, val in enumerate(row):
                    if col_idx == 4: # Amount column gets standard formatted
                        item = QTableWidgetItem(f"₱{float(val):.2f}")
                    else:
                        item = QTableWidgetItem(str(val))
                    
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    
                    # Alignments and status colors
                    if col_idx in [0, 1, 3, 5]:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    elif col_idx == 4:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    if col_idx == 0:
                        item.setForeground(QColor("#11224d"))
                        
                    if col_idx == 5:
                        if val == "Paid":
                            item.setForeground(QColor("#047857"))  # Green
                            bf = QFont()
                            bf.setBold(True)
                            item.setFont(bf)
                        else:
                            item.setForeground(QColor("#b91c1c"))  # Red

                    self.table.setItem(idx, col_idx, item)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to retrieve penalties: {e}")

    def process_payment(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please click on a penalty item in the list to trigger payment check.")
            return

        p_id = self.table.item(selected_row, 0).text()
        status = self.table.item(selected_row, 5).text()
        raw_amt_txt = self.table.item(selected_row, 4).text().replace("₱", "")
        amount = float(raw_amt_txt)

        if status == "Paid":
            QMessageBox.warning(self, "Already Paid", f"Penalty fine '{p_id}' has already been processed.")
            return

        # Elegant Clean White dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Process Payment Setup")
        dialog.setFixedWidth(320)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #111827;
            }
            QLabel {
                color: #374151;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.setContentsMargins(20, 20, 20, 20)
        dlg_layout.setSpacing(12)

        header_lbl = QLabel("PROCESS PENALTY PENALTY")
        header_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #11224d; letter-spacing: 0.5px;")
        dlg_layout.addWidget(header_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #e5e7eb; max-height: 1px;")
        dlg_layout.addWidget(line)

        lbl = QLabel(f"Processing Payment of ₱{amount:.2f} for ID:")
        lbl.setStyleSheet("font-size: 12px; color: #4b5563;")
        lbl_val = QLabel(p_id)
        lbl_val.setStyleSheet("font-weight: bold; font-size: 14px; color: #11224d; font-family: monospace;")
        
        dlg_layout.addWidget(lbl)
        dlg_layout.addWidget(lbl_val)

        method_lbl = QLabel("Payment Method:")
        method_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #4b5563;")
        method_cmb = QComboBox()
        method_cmb.addItems(["Cash", "Gcash", "Maya", "RFID Link"])
        method_cmb.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #111827;
                padding: 6px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        dlg_layout.addWidget(method_lbl)
        dlg_layout.addWidget(method_cmb)

        pay_val_lbl = QLabel("Verify exact paid amount (₱):")
        pay_val_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #4b5563;")
        pay_input = QLineEdit(f"{amount:.2f}")
        pay_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #111827;
                padding: 6px;
                font-family: monospace;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        dlg_layout.addWidget(pay_val_lbl)
        dlg_layout.addWidget(pay_input)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        
        ok_btn = QPushButton("Confirm Pay")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #047857;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #065f46;
            }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4b5563;
                padding: 8px 16px;
                border-radius: 4px;
                border: 1px solid #d1d5db;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f9fafb;
            }
        """)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)

        dlg_layout.addLayout(btn_layout)

        def click_confirm():
            try:
                entered_paid = float(pay_input.text().strip())
                if abs(entered_paid - amount) > 0.01:
                    QMessageBox.warning(dialog, "Amount Mismatch", f"Paid amount must exactly equal: ₱{amount:.2f}")
                    return

                # Record Transaction
                now = datetime.now()
                date_prefix = now.strftime("%m%d%y")

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Get latest receipt sequence
                cursor.execute("SELECT payment_id FROM payments WHERE payment_id LIKE ? ORDER BY payment_id DESC LIMIT 1", (f"{date_prefix}-%",))
                last_pay = cursor.fetchone()
                new_sequence = int(last_pay[0].split("-")[1]) + 1 if last_pay else 1
                custom_payment_id = f"{date_prefix}-{new_sequence:03d}"

                # Helpers matching standard AM/PM QDateTime parsing
                ampm = "PM" if now.hour >= 12 else "AM"
                hours = now.hour % 12
                if hours == 0:
                    hours = 12
                payment_date_str = f"{now.year}-{now.month:02d}-{now.day:02d} {hours:02d}:{now.minute:02d} {ampm}"

                # Update database
                cursor.execute("UPDATE penalty SET paid_status = 'Paid' WHERE penalty_id = ?", (p_id,))
                cursor.execute("""
                    INSERT INTO payments (payment_id, penalty_id, method, amount_paid, payment_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (custom_payment_id, p_id, method_cmb.currentText(), entered_paid, payment_date_str))

                conn.commit()
                conn.close()

                QMessageBox.information(dialog, "Payment Recorded", f"Successfully settled balance! Payment receipt ticket ID created: {custom_payment_id}")
                dialog.accept()
                self.load_penalties()
                
                # Try triggering refresh on sibling tabs if needed
                main_win = self.window()
                if main_win:
                    if hasattr(main_win, "refresh_payment_logs"):
                        main_win.refresh_payment_logs()
                    if hasattr(main_win, "refresh_stats"):
                        main_win.refresh_stats()

            except ValueError:
                QMessageBox.warning(dialog, "Invalid Format", "Please enter a valid numeric value.")
            except Exception as ex:
                QMessageBox.critical(dialog, "Database Error", f"Failed to record transaction: {ex}")

        ok_btn.clicked.connect(click_confirm)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

