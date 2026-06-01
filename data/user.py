import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

def add_subtle_shadow(widget):
    import PyQt6.QtWidgets as QW
    shadow = QW.QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setXOffset(0)
    shadow.setYOffset(2)
    shadow.setColor(QColor(17, 24, 39, 15))
    widget.setGraphicsEffect(shadow)

class UsersTab(QWidget):
    """Clean widget grouping student user registries with a quick search filters panel."""
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

        # Control Row Card
        control_card = QFrame()
        control_card.setObjectName("ControlCard")
        control_card.setStyleSheet("""
            QFrame#ControlCard {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        ctl_layout = QHBoxLayout(control_card)
        ctl_layout.setContentsMargins(16, 16, 16, 16)
        ctl_layout.setSpacing(10)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search student ID, name or RFID...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border: 1px solid #11224d;
            }
        """)
        self.search_input.textChanged.connect(self.load_users)

        # Add Student Button
        self.add_btn = QPushButton("Register New Student")
        self.add_btn.setStyleSheet("""
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
                background-color: #1a3066;
            }
        """)
        self.add_btn.clicked.connect(self.add_student)

        ctl_layout.addWidget(self.search_input)
        ctl_layout.addStretch()
        ctl_layout.addWidget(self.add_btn)
        add_subtle_shadow(control_card)
        layout.addWidget(control_card)

        # Table title
        table_lbl = QLabel("STUDENT & STAFF REGISTRIES")
        table_lbl.setStyleSheet("color: #111827; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-top: 5px;")
        layout.addWidget(table_lbl)

        # Users Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Student / User ID", "First Name", "Last Name", "M.I.", "RFID UID"])
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
        """)
        layout.addWidget(self.table)
        self.load_users()

    def load_users(self):
        query_str = self.search_input.text().strip()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if query_str:
                cursor.execute("""
                    SELECT user_id, first_name, last_name, m_i, rfid_uid 
                    FROM USER 
                    WHERE user_id LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR rfid_uid LIKE ?
                    ORDER BY user_id ASC
                """, (f"%{query_str}%", f"%{query_str}%", f"%{query_str}%", f"%{query_str}%"))
            else:
                cursor.execute("SELECT user_id, first_name, last_name, m_i, rfid_uid FROM USER ORDER BY user_id ASC")
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(0)
            for idx, row in enumerate(rows):
                self.table.insertRow(idx)
                for col_idx, val in enumerate(row):
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    if col_idx in [0, 3, 4]:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        if col_idx == 0:
                            item.setForeground(QColor("#11224d"))
                    self.table.setItem(idx, col_idx, item)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to retrieve user registry: {e}")

    def add_student(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register New Student")
        dialog.setFixedWidth(300)
        dialog.setStyleSheet("background-color: #ffffff;")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Form fields
        id_lbl = QLabel("Student ID (e.g. 2024-0001):")
        id_input = QLineEdit()
        fn_lbl = QLabel("First Name:")
        fn_input = QLineEdit()
        ln_lbl = QLabel("Last Name:")
        ln_input = QLineEdit()
        mi_lbl = QLabel("Middle Initial:")
        mi_input = QLineEdit()
        rfid_lbl = QLabel("RFID UID:")
        rfid_input = QLineEdit()

        inputs = [id_input, fn_input, ln_input, mi_input, rfid_input]
        for inp in inputs:
            inp.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 12px;
                }
            """)

        layout.addWidget(id_lbl)
        layout.addWidget(id_input)
        layout.addWidget(fn_lbl)
        layout.addWidget(fn_input)
        layout.addWidget(ln_lbl)
        layout.addWidget(ln_input)
        layout.addWidget(mi_lbl)
        layout.addWidget(mi_input)
        layout.addWidget(rfid_lbl)
        layout.addWidget(rfid_input)

        # Buttons
        btn_box = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #11224d;
                color: #ffffff;
                border: none;
                padding: 6px 14px;
                font-weight: bold;
                border-radius: 4px;
            }
        """)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e5e7eb;
                color: #374151;
                border: none;
                padding: 6px 14px;
                border-radius: 4px;
            }
        """)
        
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

        cancel_btn.clicked.connect(dialog.reject)
        
        def save():
            uid = id_input.text().strip()
            fn = fn_input.text().strip()
            ln = ln_input.text().strip()
            mi = mi_input.text().strip()
            rf = rfid_input.text().strip()

            if not uid or not fn or not ln:
                QMessageBox.warning(dialog, "Missing Fields", "ID, First Name, and Last Name are required.")
                return

            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO USER (user_id, first_name, last_name, m_i, rfid_uid) 
                    VALUES (?, ?, ?, ?, ?)
                """, (uid, fn, ln, mi, rf))
                conn.commit()
                conn.close()
                dialog.accept()
                self.load_users()
            except Exception as e:
                QMessageBox.critical(dialog, "Database Error", f"Registration failed: {e}")

        save_btn.clicked.connect(save)
        dialog.exec()
