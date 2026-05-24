import sqlite3
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QDialog, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QDateTime

# =====================================================================
# 1. RENT DIALOG POPUP WINDOW
# =====================================================================
class RentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rent Umbrella")
        self.setFixedWidth(300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("User ID")
        layout.addWidget(QLabel("User ID:"))
        layout.addWidget(self.user_id_input)

        self.umb_id_input = QLineEdit()
        self.umb_id_input.setPlaceholderText("Umbrella ID (e.g., RC-001)")
        layout.addWidget(QLabel("Umbrella ID:"))
        layout.addWidget(self.umb_id_input)

        self.btn_confirm = QPushButton("Confirm")
        self.btn_confirm.clicked.connect(self.accept)
        layout.addWidget(self.btn_confirm)

        self.setLayout(layout)

    def get_data(self):
        return self.user_id_input.text().strip(), self.umb_id_input.text().strip()


# =====================================================================
# 2. RETURN DIALOG POPUP WINDOW
# =====================================================================
class ReturnDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Return Umbrella")
        self.setFixedWidth(300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.rent_id_input = QLineEdit()
        self.rent_id_input.setPlaceholderText("Rent ID (e.g., 052426-001)")
        layout.addWidget(QLabel("Rent ID:"))
        layout.addWidget(self.rent_id_input)

        self.condition_dropdown = QComboBox()
        self.condition_dropdown.addItems(["Good", "Damaged", "Dysfunctional"])
        layout.addWidget(QLabel("Return Condition:"))
        layout.addWidget(self.condition_dropdown)

        self.btn_confirm = QPushButton("Confirm")
        self.btn_confirm.clicked.connect(self.accept)
        layout.addWidget(self.btn_confirm)

        self.setLayout(layout)

    def get_data(self):
        return self.rent_id_input.text().strip(), self.condition_dropdown.currentText()


# =====================================================================
# 3. MAIN TAB WIDGET MODULE
# =====================================================================
class UmbrellaTableWidget(QWidget):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.init_db_stock()
        self.init_ui()
        self.load_all_data()

    def init_db_stock(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Umbrella")
        if cursor.fetchone()[0] == 0:
            for i in range(1, 31):
                umb_id = f"RC-{i:03d}"
                cursor.execute(
                    "INSERT INTO Umbrella (umbrella_id, current_status, condition) VALUES (?, ?, ?)",
                    (umb_id, "Available", "Good")
                )
            conn.commit()
        conn.close()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # ---- TRANSACTIONS ACTION BUTTONS ----
        rr_group = QGroupBox("Transactions (Rents & Returns)")
        rr_layout = QHBoxLayout()
        rr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_rent = QPushButton("Rent Umbrella")
        btn_rent.setMinimumWidth(150)
        btn_rent.clicked.connect(self.open_rent_popup)
        
        btn_return = QPushButton("Return Umbrella")
        btn_return.setMinimumWidth(150)
        btn_return.clicked.connect(self.open_return_popup)

        rr_layout.addWidget(btn_rent)
        rr_layout.addWidget(btn_return)
        rr_group.setLayout(rr_layout)
        main_layout.addWidget(rr_group)

        # Transactions History Table
        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(6)
        self.trans_table.setHorizontalHeaderLabels(["Rent ID", "User ID", "Umbrella ID", "Rent Date", "Due Date", "Returned?"])
        self.trans_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.trans_table)

        # ---- UMBRELLA INVENTORY VIEW ----
        umb_group = QGroupBox("Umbrella Inventory")
        umb_layout = QVBoxLayout()
        
        self.umb_table = QTableWidget()
        self.umb_table.setColumnCount(3)
        self.umb_table.setHorizontalHeaderLabels(["Umbrella ID", "Current Status", "Condition"])
        self.umb_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        umb_layout.addWidget(self.umb_table)
        umb_group.setLayout(umb_layout)
        main_layout.addWidget(umb_group)

        self.setLayout(main_layout)

    def load_all_data(self):
        self.umb_table.setRowCount(0)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Umbrella")
        for r_idx, row in enumerate(cursor.fetchall()):
            self.umb_table.insertRow(r_idx)
            for c_idx, data in enumerate(row):
                self.umb_table.setItem(r_idx, c_idx, QTableWidgetItem(str(data)))

        self.trans_table.setRowCount(0)
        cursor.execute("""
            SELECT r.rent_id, r.user_id, r.umbrella_id, r.rent_date, r.due_date, 
            CASE WHEN ret.return_id IS NOT NULL THEN 'Yes' ELSE 'No' END 
            FROM rents r LEFT JOIN returns ret ON r.rent_id = ret.rent_id
        """)
        for r_idx, row in enumerate(cursor.fetchall()):
            self.trans_table.insertRow(r_idx)
            for c_idx, data in enumerate(row):
                self.trans_table.setItem(r_idx, c_idx, QTableWidgetItem(str(data)))
        conn.close()

    def open_rent_popup(self):
        dialog = RentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            uid, ubid = dialog.get_data()
            if not uid or not ubid:
                QMessageBox.warning(self, "Input Error", "Both User ID and Umbrella ID fields must be completed.")
                return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT first_name, last_name FROM USER WHERE user_id = ?", (uid,))
            user_exists = cursor.fetchone()
            
            if not user_exists:
                QMessageBox.critical(self, "Access Denied", f"User ID '{uid}' does not exist.")
                conn.close()
                return
            
            first_name, last_name = user_exists

            cursor.execute("SELECT current_status FROM Umbrella WHERE umbrella_id = ?", (ubid,))
            status = cursor.fetchone()
            if not status or status[0] == "Rented":
                QMessageBox.warning(self, "Unavailable", f"Umbrella status invalid or already rented.")
                conn.close()
                return

            # --- TIMESTAMP UPDATES ---
            now = QDateTime.currentDateTime()
            date_prefix = now.toString("MMddyy")
            
            cursor.execute("SELECT rent_id FROM rents WHERE rent_id LIKE ? ORDER BY rent_id DESC LIMIT 1", (f"{date_prefix}-%",))
            last_rent = cursor.fetchone()
            new_sequence = int(last_rent[0].split("-")[1]) + 1 if last_rent else 1
            custom_rent_id = f"{date_prefix}-{new_sequence:03d}"

            # Saves date with exact hours and minutes
            rent_timestamp_str = now.toString("yyyy-MM-dd hh:mm AP")
            due_timestamp_str = now.addDays(7).toString("yyyy-MM-dd hh:mm AP")

            cursor.execute("""
                INSERT INTO rents (rent_id, user_id, umbrella_id, rent_date, due_date) 
                VALUES (?, ?, ?, ?, ?)
            """, (custom_rent_id, uid, ubid, rent_timestamp_str, due_timestamp_str))
            cursor.execute("UPDATE Umbrella SET current_status = 'Rented' WHERE umbrella_id = ?", (ubid,))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", f"Rent ID: {custom_rent_id}\nRent Date: {rent_timestamp_str}\nDue Date: {due_timestamp_str}")
            self.load_all_data()

    def open_return_popup(self):
        dialog = ReturnDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rent_id, return_cond = dialog.get_data()
            if not rent_id: return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT due_date, user_id, umbrella_id FROM rents WHERE rent_id = ?", (rent_id,))
            rent_info = cursor.fetchone()
            if not rent_info:
                QMessageBox.critical(self, "Not Found", "Rent ID does not exist.")
                conn.close()
                return

            due_date_str, user_id, umb_id = rent_info
            
            now = QDateTime.currentDateTime()
            today_str = now.toString("yyyy-MM-dd hh:mm AP")
            date_pattern = now.toString("MMddyy")

            cursor.execute("INSERT INTO returns (rent_id, return_date, return_condition) VALUES (?, ?, ?)", (rent_id, today_str, return_cond))
            cursor.execute("UPDATE Umbrella SET current_status = 'Available' WHERE umbrella_id = ?", (umb_id,))

            penalties_issued = []

            if return_cond in ["Damaged", "Dysfunctional"]:
                cursor.execute("UPDATE Umbrella SET condition = ? WHERE umbrella_id = ?", (return_cond, umb_id))
                prefix = "DMG" if return_cond == "Damaged" else "DYS"
                fine_amount = 50.00 if return_cond == "Damaged" else 200.00

                cursor.execute("SELECT penalty_id FROM penalty WHERE penalty_id LIKE ? ORDER BY penalty_id DESC LIMIT 1", (f"{prefix}-{date_pattern}-%",))
                last_penalty = cursor.fetchone()
                new_sequence = int(last_penalty[0].split("-")[2]) + 1 if last_penalty else 1
                custom_penalty_id = f"{prefix}-{date_pattern}-{new_sequence:03d}"

                cursor.execute("""
                    INSERT INTO penalty (penalty_id, user_id, penalty_reason, date_issued, amount, paid_status) 
                    VALUES (?, ?, ?, ?, ?, 'Unpaid')
                """, (custom_penalty_id, user_id, f"Returned Umbrella {return_cond}", today_str, fine_amount))
                penalties_issued.append(f"• Property Damage Fee (₱{fine_amount:.2f}) - {custom_penalty_id}")

            # Fallback checking logic for late records via timestamps
            due_datetime = QDateTime.fromString(due_date_str, "yyyy-MM-dd hh:mm AP")
            if now > due_datetime:
                late_fee_amount = 15.00
                cursor.execute("SELECT penalty_id FROM penalty WHERE penalty_id LIKE 'LATE-%' ORDER BY penalty_id DESC LIMIT 1")
                last_late = cursor.fetchone()
                new_late_seq = int(last_late[0].split("-")[1]) + 1 if last_late else 1
                late_id = f"LATE-{new_late_seq:05d}"

                cursor.execute("""
                    INSERT INTO penalty (penalty_id, user_id, penalty_reason, date_issued, amount, paid_status) 
                    VALUES (?, ?, 'Late Return', ?, ?, 'Unpaid')
                """, (late_id, user_id, today_str, late_fee_amount))
                penalties_issued.append(f"• Overdue Late Return Fee (₱{late_fee_amount:.2f}) - {late_id}")

            conn.commit()
            conn.close()
            self.load_all_data()