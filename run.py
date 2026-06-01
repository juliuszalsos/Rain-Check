import sys
import os
import sqlite3
import random
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QFrame, QStackedWidget, QTabWidget, QButtonGroup,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor

def add_subtle_shadow(widget):
    """Adds a beautiful, tiny, elegant drop shadow to any widget."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setXOffset(0)
    shadow.setYOffset(2)
    shadow.setColor(QColor(17, 24, 39, 15)) # standard light slate grey shadow
    widget.setGraphicsEffect(shadow)

# Import custom PyQt6 Tab Widgets
try:
    from data.user import UsersTab
    from data.umbrella import UmbrellasTab
    from data.penalty import PenaltiesTab
    from data.payment import PaymentsTab
except ImportError:
    # Fallback to local import if run differently
    from user import UsersTab
    from umbrella import UmbrellasTab
    from penalty import PenaltiesTab
    from payment import PaymentsTab

DB_FILE = os.path.join(os.getcwd(), "Raincheck.db")

def init_database():
    """Initializes the database schema and seeds if empty to replicate standard stats: 24 Available, 17 Active, 3 Overdue."""
    if os.path.exists(DB_FILE):
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Umbrella'")
            if c.fetchone():
                c.execute("SELECT umbrella_id FROM Umbrella LIMIT 1")
                row = c.fetchone()
                if row and row[0].startswith("RC-"):
                    conn.close()
                    os.remove(DB_FILE)
                else:
                    conn.close()
            else:
                conn.close()
        except Exception:
            pass

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. USER Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS USER (
            user_id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            m_i TEXT,
            rfid_uid TEXT
        )
    """)

    # 2. Umbrella Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Umbrella (
            umbrella_id TEXT PRIMARY KEY,
            current_status TEXT,
            condition TEXT
        )
    """)

    # 3. rents Table
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

    # 4. returns Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS returns (
            return_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rent_id TEXT,
            return_date TEXT,
            return_condition TEXT,
            FOREIGN KEY(rent_id) REFERENCES rents(rent_id)
        )
    """)

    # 5. penalty Table
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

    # 6. payments Table
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

    # Seed 50 randomized student records first
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
            year = random.randint(2021, 2026)
            suffix = random.randint(1, 2999)
            generated_ids.add(f"{year}-{suffix:04d}")

        for uid in sorted(generated_ids):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            mi = chr(random.randint(65, 90))
            rfid = f"RFID-{random.randint(100000, 999999)}"
            cursor.execute(
                "INSERT INTO USER (user_id, first_name, last_name, m_i, rfid_uid) VALUES (?, ?, ?, ?, ?)",
                (uid, fname, lname, mi, rfid)
            )
        conn.commit()

    # Seed 60 total Umbrellas (U-001 up to U-060)
    cursor.execute("SELECT COUNT(*) FROM Umbrella")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 61):
            umb_id = f"U-{i:03d}"
            # Let's seed 14 Rented (U-001 - U-014), 4 Maintenance (U-015 - U-018), 42 Available (U-019 - U-060)
            if i <= 14:
                status = "Rented"
                condition = "Good"
            elif i <= 18:
                status = "Maintenance"
                condition = "Damaged"
            else:
                status = "Available"
                condition = "Good"
            cursor.execute(
                "INSERT INTO Umbrella (umbrella_id, current_status, condition) VALUES (?, ?, ?)",
                (umb_id, status, condition)
            )
        conn.commit()

    # Seed 14 Active Rentals with exactly 3 of them overdue
    cursor.execute("SELECT COUNT(*) FROM rents")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT user_id FROM USER ORDER BY user_id ASC")
        users = [r[0] for r in cursor.fetchall()]
        
        now = datetime.now()
        
        # 14 active rentals total
        for idx in range(14):
            umb_id = f"U-{idx+1:03d}"
            user_id = users[idx % len(users)]
            rent_id = f"{now.strftime('%m%d%y')}-{idx+1:03d}"
            
            # Exactly first 3 overdue
            is_overdue = (idx < 3)
            if is_overdue:
                rent_dt = now - timedelta(days=12)
                due_dt = now - timedelta(days=5)
            else:
                rent_dt = now - timedelta(days=2)
                due_dt = now + timedelta(days=5)
                
            ampm_r = "PM" if rent_dt.hour >= 12 else "AM"
            hr_r = rent_dt.hour % 12
            if hr_r == 0: 
                hr_r = 12
            rent_str = f"{rent_dt.year}-{rent_dt.month:02d}-{rent_dt.day:02d} {hr_r:02d}:{rent_dt.minute:02d} {ampm_r}"
            
            ampm_d = "PM" if due_dt.hour >= 12 else "AM"
            hr_d = due_dt.hour % 12
            if hr_d == 0: 
                hr_d = 12
            due_str = f"{due_dt.year}-{due_dt.month:02d}-{due_dt.day:02d} {hr_d:02d}:{due_dt.minute:02d} {ampm_d}"
            
            cursor.execute("INSERT INTO rents (rent_id, user_id, umbrella_id, rent_date, due_date) VALUES (?, ?, ?, ?, ?)",
                           (rent_id, user_id, umb_id, rent_str, due_str))
            
        conn.commit()

    conn.close()


class StatCard(QFrame):
    """Polished dashboard metric cards styled with custom color border indicators."""
    def __init__(self, border_color, icon_char, title, sub_text, label_color, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(140)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-top: 4px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(4)
        
        icon_lbl = QLabel(f"<span style='font-size: 24px; color: {label_color};'>{icon_char}</span>")
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.val_lbl = QLabel("0")
        self.val_lbl.setStyleSheet("font-size: 38px; font-weight: bold; color: #111827; border: none; background: transparent;")
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #6b7280; border: none; background: transparent;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        sub_lbl = QLabel(sub_text)
        sub_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {label_color}; border: none; background: transparent;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon_lbl)
        layout.addWidget(self.val_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)
        
        add_subtle_shadow(self)
        
    def set_value(self, val):
        self.val_lbl.setText(str(val))


class BigActionButton(QPushButton):
    """Large interactive action button shortcuts inside dashboard workflow."""
    def __init__(self, icon_char, text, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(300)
        self.setFixedHeight(180)
        self.setStyleSheet("""
            QPushButton {
                background-color: #11224d;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                text-align: center;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #1c356e;
            }
            QPushButton:pressed {
                background-color: #0b1530;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 25, 15, 25)
        layout.setSpacing(12)
        
        icon_lbl = QLabel(f"<span style='font-size: 42px; color: #fedb41;'>{icon_char}</span>")
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        
        text_lbl = QLabel(text)
        text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px; letter-spacing: 0.8px; background: transparent; border: none;")
        
        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)
        
        add_subtle_shadow(self)


class DashboardPage(QWidget):
    """Rich main home screen showing summary stats widgets and action navigation buttons."""
    def __init__(self, main_win, parent=None):
        super().__init__(parent)
        self.main_win = main_win
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet("background-color: #f3f4f6;")
        
        # Outer layout to center the entire dashboard page content horizontally and vertically
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addStretch(1)
        
        # Main container with a comfortable visual width
        container = QWidget()
        container.setFixedWidth(1020)
        container.setStyleSheet("background: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 30, 20, 30)
        container_layout.setSpacing(15)
        
        # Add spacing before content to center vertically
        container_layout.addStretch(1)
        
        # Section 1: QUICK STATS
        stats_section_lbl = QLabel("QUICK STATS")
        stats_section_lbl.setStyleSheet("color: #6b7280; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        stats_section_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(stats_section_lbl)
        
        # Horiz layout of cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.avail_card = StatCard("#10b981", "☂", "Available Umbrellas", "Ready to rent", "#047857", self)
        self.active_card = StatCard("#f59e0b", "🕒", "Active Rentals", "Currently Out", "#b45309", self)
        self.overdue_card = StatCard("#ef4444", "⚠️", "Overdue Rentals", "Past limit", "#b91c1c", self)
        
        cards_layout.addWidget(self.avail_card)
        cards_layout.addWidget(self.active_card)
        cards_layout.addWidget(self.overdue_card)
        container_layout.addLayout(cards_layout)
        
        # Spacer
        container_layout.addSpacing(15)
        
        # Section 2: ACTIONS
        actions_section_lbl = QLabel("ACTIONS")
        actions_section_lbl.setStyleSheet("color: #6b7280; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        actions_section_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(actions_section_lbl)
        
        # Large Action Buttons Row centered horizontally and filling the layout
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(20)
        
        self.rent_action_btn = BigActionButton("✋", "RENT UMBRELLA", self)
        self.return_action_btn = BigActionButton("↩", "RETURN UMBRELLA", self)
        
        # Connect actions
        self.rent_action_btn.clicked.connect(lambda: self.main_win.switch_view(1))
        self.return_action_btn.clicked.connect(lambda: self.main_win.switch_view(2))
        
        actions_layout.addWidget(self.rent_action_btn)
        actions_layout.addWidget(self.return_action_btn)
        
        container_layout.addLayout(actions_layout)
        
        # Add spacing after content to center vertically
        container_layout.addStretch(1)
        
        outer_layout.addWidget(container)
        outer_layout.addStretch(1)


class ClickableOptionCard(QFrame):
    """A gorgeous clickable option card replicating rounded custom radio controls."""
    from PyQt6.QtCore import pyqtSignal
    clicked = pyqtSignal()
    
    def __init__(self, title, description, active_border_color, active_bg_color, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.active_border_color = active_border_color
        self.active_bg_color = active_bg_color
        self.is_selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(12)
        
        self.radio_indicator = QLabel("○")
        self.radio_indicator.setStyleSheet("color: #9cb3e6; font-size: 18px; font-weight: bold; border: none; background: transparent;")
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.title_lbl = QLabel(self.title)
        self.title_lbl.setStyleSheet("color: #111827; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        
        self.desc_lbl = QLabel(self.description)
        self.desc_lbl.setStyleSheet("color: #6b7280; font-size: 11px; border: none; background: transparent;")
        
        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.desc_lbl)
        
        layout.addWidget(self.radio_indicator)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        self.update_style()
        
    def update_style(self):
        if self.is_selected:
            self.radio_indicator.setText("●")
            self.radio_indicator.setStyleSheet(f"color: {self.active_border_color}; font-size: 18px; border: none; background: transparent;")
            self.title_lbl.setStyleSheet(f"color: {self.active_border_color}; font-weight: bold; font-size: 13px; border: none; background: transparent;")
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.active_bg_color};
                    border: 2px solid {self.active_border_color};
                    border-radius: 8px;
                }}
            """)
        else:
            self.radio_indicator.setText("○")
            self.radio_indicator.setStyleSheet("color: #9ca3af; font-size: 18px; border: none; background: transparent;")
            self.title_lbl.setStyleSheet("color: #374151; font-weight: bold; font-size: 13px; border: none; background: transparent;")
            self.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                }
            """)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()


class RentPage(QWidget):
    """Issue checkout page styled as a guided checkout form with dynamic search validation."""
    def __init__(self, db_path, main_win, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.main_win = main_win
        self.selected_user = None
        self.selected_umbrella = None
        self.user_is_restricted = False
        self.restriction_reason = ""
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet("background-color: #f3f4f6;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 1. PAGE HEADER
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        title_lbl = QLabel("✋ Rent umbrella")
        title_lbl.setStyleSheet("color: #11224d; font-size: 18px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        
        sub_lbl = QLabel("New rental transaction")
        sub_lbl.setStyleSheet("color: #6b7280; font-size: 11px; font-family: 'Segoe UI', sans-serif;")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 2. STEP 1: SEARCH USER CARD
        step1_card = QFrame()
        step1_card.setObjectName("Step1Card")
        step1_card.setStyleSheet("""
            QFrame#Step1Card {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        step1_layout = QVBoxLayout(step1_card)
        step1_layout.setContentsMargins(20, 18, 20, 18)
        step1_layout.setSpacing(10)
        
        step1_title = QLabel("📋 Step 1. Search user")
        step1_title.setStyleSheet("color: #6b7280; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;")
        step1_layout.addWidget(step1_title)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search user ID or name...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #11224d;
            }
        """)
        self.search_input.textChanged.connect(self.search_user_changed)
        step1_layout.addWidget(self.search_input)
        
        user_found_lbl = QLabel("USER FOUND")
        user_found_lbl.setStyleSheet("color: #9ca3af; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        step1_layout.addWidget(user_found_lbl)
        
        # Detail box
        self.user_detail_box = QFrame()
        self.user_detail_box.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        detail_layout = QVBoxLayout(self.user_detail_box)
        detail_layout.setContentsMargins(15, 12, 15, 12)
        detail_layout.setSpacing(6)
        
        self.user_field_lbl = QLabel("👤 User:   --")
        self.user_field_lbl.setStyleSheet("color: #374151; font-weight: 500; font-size: 13px; border: none; background: transparent;")
        self.status_field_lbl = QLabel("⚠️ Status: --")
        self.status_field_lbl.setStyleSheet("color: #374151; font-weight: 500; font-size: 13px; border: none; background: transparent;")
        
        detail_layout.addWidget(self.user_field_lbl)
        detail_layout.addWidget(self.status_field_lbl)
        step1_layout.addWidget(self.user_detail_box)
        
        add_subtle_shadow(step1_card)
        layout.addWidget(step1_card)

        # 3. STEP 2: SELECT UMBRELLA CARD
        self.step2_card = QFrame()
        self.step2_card.setObjectName("Step2Card")
        self.step2_card.setStyleSheet("""
            QFrame#Step2Card {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        self.step2_layout = QVBoxLayout(self.step2_card)
        self.step2_layout.setContentsMargins(20, 18, 20, 18)
        self.step2_layout.setSpacing(10)
        
        step2_title = QLabel("☂ Step 2. Select umbrella")
        step2_title.setStyleSheet("color: #6b7280; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;")
        self.step2_layout.addWidget(step2_title)
        
        # Stacked display: selection form or error notice
        self.selection_form_widget = QWidget()
        selection_form_layout = QVBoxLayout(self.selection_form_widget)
        selection_form_layout.setContentsMargins(0, 0, 0, 0)
        selection_form_layout.setSpacing(10)
        
        self.umb_cmb = QComboBox()
        self.umb_cmb.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #111827;
                selection-background-color: #11224d;
                selection-color: #ffffff;
            }
        """)
        self.umb_cmb.currentIndexChanged.connect(self.umbrella_selection_changed)
        selection_form_layout.addWidget(self.umb_cmb)
        
        self.umb_detail_box = QFrame()
        self.umb_detail_box.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        umb_detail_layout = QVBoxLayout(self.umb_detail_box)
        umb_detail_layout.setContentsMargins(15, 12, 15, 12)
        umb_detail_layout.setSpacing(6)
        
        self.umb_field_lbl = QLabel("🌂 Umbrella:   --")
        self.umb_field_lbl.setStyleSheet("color: #374151; font-weight: 500; font-size: 13px; border: none; background: transparent;")
        self.condition_field_lbl = QLabel("⭐ Condition:  --")
        self.condition_field_lbl.setStyleSheet("color: #374151; font-weight: 500; font-size: 13px; border: none; background: transparent;")
        self.avail_field_lbl = QLabel("⚠️ Status:     --")
        self.avail_field_lbl.setStyleSheet("color: #374151; font-weight: 500; font-size: 13px; border: none; background: transparent;")
        
        umb_detail_layout.addWidget(self.umb_field_lbl)
        umb_detail_layout.addWidget(self.condition_field_lbl)
        umb_detail_layout.addWidget(self.avail_field_lbl)
        selection_form_layout.addWidget(self.umb_detail_box)
        
        self.step2_layout.addWidget(self.selection_form_widget)
        
        # Error Banner notice
        self.error_banner = QFrame()
        self.error_banner.setStyleSheet("""
            QFrame {
                background-color: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 8px;
            }
        """)
        error_banner_layout = QVBoxLayout(self.error_banner)
        error_banner_layout.setContentsMargins(20, 20, 20, 20)
        
        self.error_msg_lbl = QLabel("Cannot proceed.")
        self.error_msg_lbl.setStyleSheet("color: #b91c1c; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        self.error_msg_lbl.setWordWrap(True)
        self.error_msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_banner_layout.addWidget(self.error_msg_lbl)
        self.step2_layout.addWidget(self.error_banner)
        
        add_subtle_shadow(self.step2_card)
        layout.addWidget(self.step2_card)
        
        # 4. BOTTOM CONFIRM RENTAL BUTTON
        actions_row = QHBoxLayout()
        actions_row.addStretch()
        
        self.confirm_btn = QPushButton("Confirm Rental")
        self.confirm_btn.setFixedWidth(200)
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #11224d;
                border: 1px solid #11224d;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
            QPushButton:disabled {
                border: 1.5px solid #d1d5db;
                color: #9cb3e6;
                background-color: #f3f4f6;
            }
        """)
        self.confirm_btn.clicked.connect(self.confirm_rental)
        actions_row.addWidget(self.confirm_btn)
        actions_row.addStretch()
        layout.addLayout(actions_row)
        
        layout.addStretch()
        
        self.refresh()

    def refresh(self):
        self.selected_user = None
        self.selected_umbrella = None
        self.search_input.clear()
        self.user_field_lbl.setText("👤 User:   --")
        self.status_field_lbl.setText("⚠️ Status: --")
        
        self.error_banner.hide()
        self.selection_form_widget.show()
        self.confirm_btn.setEnabled(False)
        self.load_available_umbrellas()

    def load_available_umbrellas(self):
        try:
            self.umb_cmb.clear()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT umbrella_id FROM Umbrella WHERE current_status = 'Available' AND condition = 'Good' ORDER BY umbrella_id ASC")
            items = [r[0] for r in cursor.fetchall()]
            conn.close()
            self.umb_cmb.addItems(items)
            if items:
                self.umb_cmb.setCurrentIndex(0)
                self.umbrella_selection_changed()
        except Exception as e:
            print(f"Error loading umbrellas dropdown: {e}")

    def search_user_changed(self, text):
        query_str = text.strip()
        if not query_str:
            self.selected_user = None
            self.user_field_lbl.setText("👤 User:   --")
            self.status_field_lbl.setText("⚠️ Status: --")
            self.selection_form_widget.show()
            self.error_banner.hide()
            self.confirm_btn.setEnabled(False)
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, first_name, last_name, m_i 
                FROM USER 
                WHERE user_id = ? OR (first_name || ' ' || last_name) LIKE ? 
                LIMIT 1
            """, (query_str, f"%{query_str}%"))
            user = cursor.fetchone()
            
            if user:
                user_id, f_name, l_name, m_i = user
                m_i_str = f" {m_i}." if m_i else ""
                full_name = f"{f_name}{m_i_str} {l_name}"
                self.selected_user = {"id": user_id, "name": full_name}
                self.user_field_lbl.setText(f"👤 User:   {full_name} ({user_id})")
                
                # Check penalties
                cursor.execute("SELECT COUNT(*) FROM penalty WHERE user_id = ? AND paid_status = 'Unpaid'", (user_id,))
                penalty_count = cursor.fetchone()[0]
                
                # Check active rent holds
                cursor.execute("""
                    SELECT count(*) FROM rents r 
                    LEFT JOIN returns ret ON r.rent_id = ret.rent_id 
                    WHERE r.user_id = ? AND ret.return_id IS NULL
                """, (user_id,))
                active_holds = cursor.fetchone()[0]
                
                if penalty_count > 0:
                    self.user_is_restricted = True
                    self.status_field_lbl.setText("⚠️ Status: RESTRICTED - Active Penalty")
                    self.status_field_lbl.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 13px; border: none; background: transparent;")
                    self.error_msg_lbl.setText("Cannot proceed. Student must settle their penalty for a damaged/lost umbrella at the Penalty tab first.")
                    self.selection_form_widget.hide()
                    self.error_banner.show()
                    self.confirm_btn.setEnabled(False)
                elif active_holds > 0:
                    self.user_is_restricted = True
                    self.status_field_lbl.setText("⚠️ Status: RESTRICTED - Holds active rental")
                    self.status_field_lbl.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 13px; border: none; background: transparent;")
                    self.error_msg_lbl.setText("Cannot proceed. Student already has an active umbrella checkout.")
                    self.selection_form_widget.hide()
                    self.error_banner.show()
                    self.confirm_btn.setEnabled(False)
                else:
                    self.user_is_restricted = False
                    self.status_field_lbl.setText("⚠️ Status: CLEARED TO RENT")
                    self.status_field_lbl.setStyleSheet("color: #047857; font-weight: bold; font-size: 13px; border: none; background: transparent;")
                    self.error_banner.hide()
                    self.selection_form_widget.show()
                    self.umbrella_selection_changed()
            else:
                self.selected_user = None
                self.user_field_lbl.setText("👤 User:   --")
                self.status_field_lbl.setText("⚠️ Status: User Not Found")
                self.status_field_lbl.setStyleSheet("color: #ef4444; font-size: 13px; border: none; background: transparent;")
                self.confirm_btn.setEnabled(False)
                
            conn.close()
        except Exception as e:
            print(f"Error searching user: {e}")

    def umbrella_selection_changed(self):
        if not self.selected_user or self.user_is_restricted:
            return
            
        umb_id = self.umb_cmb.currentText().strip()
        if not umb_id:
            self.selected_umbrella = None
            self.umb_field_lbl.setText("🌂 Umbrella:   --")
            self.condition_field_lbl.setText("⭐ Condition:  --")
            self.avail_field_lbl.setText("⚠️ Status:     --")
            self.confirm_btn.setEnabled(False)
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT condition, current_status FROM Umbrella WHERE umbrella_id = ?", (umb_id,))
            res = cursor.fetchone()
            conn.close()
            
            if res:
                cond, stat = res
                self.selected_umbrella = {"id": umb_id, "condition": cond, "status": stat}
                self.umb_field_lbl.setText(f"🌂 Umbrella:   {umb_id}")
                self.condition_field_lbl.setText(f"⭐ Condition:  {cond.upper()}")
                self.condition_field_lbl.setStyleSheet("color: #0284c7; font-weight: bold; font-size: 13px; border: none; background: transparent;")
                self.avail_field_lbl.setText(f"⚠️ Status:     {stat.upper()}")
                self.avail_field_lbl.setStyleSheet("color: #047857; font-weight: bold; font-size: 13px; border: none; background: transparent;")
                self.confirm_btn.setEnabled(True)
        except Exception as e:
            print(f"Error updating umbrella fields: {e}")

    def confirm_rental(self):
        if not self.selected_user or not self.selected_umbrella:
            return
            
        user_id = self.selected_user["id"]
        umbrella_id = self.selected_umbrella["id"]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Form sequence number format
            now = datetime.now()
            date_prefix = now.strftime("%m%d%y")
            
            cursor.execute("SELECT rent_id FROM rents WHERE rent_id LIKE ? ORDER BY rent_id DESC LIMIT 1", (f"{date_prefix}-%",))
            last_rent = cursor.fetchone()
            new_sequence = int(last_rent[0].split("-")[1]) + 1 if last_rent else 1
            custom_rent_id = f"{date_prefix}-{new_sequence:03d}"
            
            # Format custom timestamp
            ampm_tx = "PM" if now.hour >= 12 else "AM"
            hours_tx = now.hour % 12
            if hours_tx == 0:
                hours_tx = 12
            rent_date_str = f"{now.year}-{now.month:02d}-{now.day:02d} {hours_tx:02d}:{now.minute:02d} {ampm_tx}"
            
            due_dt = now + timedelta(days=7)
            ampm_due = "PM" if due_dt.hour >= 12 else "AM"
            hours_due = due_dt.hour % 12
            if hours_due == 0:
                hours_due = 12
            due_date_str = f"{due_dt.year}-{due_dt.month:02d}-{due_dt.day:02d} {hours_due:02d}:{due_dt.minute:02d} {ampm_due}"
            
            # Perform rent transaction
            cursor.execute("INSERT INTO rents (rent_id, user_id, umbrella_id, rent_date, due_date) VALUES (?, ?, ?, ?, ?)",
                           (custom_rent_id, user_id, umbrella_id, rent_date_str, due_date_str))
            cursor.execute("UPDATE Umbrella SET current_status = 'Rented' WHERE umbrella_id = ?", (umbrella_id,))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Equipment Checked Out", f"Equipment successfully leased!\nID: {custom_rent_id}\nDue on: {due_date_str}")
            
            self.refresh()
            self.main_win.refresh_stats()
            if hasattr(self.main_win, "return_view"):
                self.main_win.return_view.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Checkout Error", f"Checkout failed: {e}")


class ReturnPage(QWidget):
    """The dedicated return view structured as a clean step-by-step transaction check-in."""
    def __init__(self, db_path, main_win, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.main_win = main_win
        self.active_rent = None
        self.selected_condition = "Good" # default
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet("background-color: #f3f4f6;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 1. PAGE HEADER
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        title_lbl = QLabel("↩ Return umbrella")
        title_lbl.setStyleSheet("color: #11224d; font-size: 18px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        
        sub_lbl = QLabel("Process active rental return")
        sub_lbl.setStyleSheet("color: #6b7280; font-size: 11px; font-family: 'Segoe UI', sans-serif;")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 2. STEP 1: FIND ACTIVE RENTAL CARD
        step1_card = QFrame()
        step1_card.setObjectName("Step1Card")
        step1_card.setStyleSheet("""
            QFrame#Step1Card {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        step1_layout = QVBoxLayout(step1_card)
        step1_layout.setContentsMargins(20, 18, 20, 18)
        step1_layout.setSpacing(10)
        
        step1_title = QLabel("📋 Step 1. Find active rental")
        step1_title.setStyleSheet("color: #6b7280; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;")
        step1_layout.addWidget(step1_title)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search user ID or name...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #11224d;
            }
        """)
        self.search_input.textChanged.connect(self.search_active_rental)
        step1_layout.addWidget(self.search_input)
        
        active_found_lbl = QLabel("ACTIVE RENTAL FOUND")
        active_found_lbl.setStyleSheet("color: #9ca3af; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        step1_layout.addWidget(active_found_lbl)
        
        # Detail box
        self.detail_box = QFrame()
        self.detail_box.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        detail_layout = QVBoxLayout(self.detail_box)
        detail_layout.setContentsMargins(15, 12, 15, 12)
        detail_layout.setSpacing(6)
        
        self.user_lbl = QLabel("👤 User:       --")
        self.umbrella_lbl = QLabel("🌂 Umbrella:   --")
        self.borrowed_lbl = QLabel("📅 Borrowed:   --")
        self.due_lbl = QLabel("🕒 Due Date:   --")
        self.status_lbl = QLabel("⚠️ Status:     --")
        
        labels = [self.user_lbl, self.umbrella_lbl, self.borrowed_lbl, self.due_lbl, self.status_lbl]
        for lbl in labels:
            lbl.setStyleSheet("color: #374151; font-weight: 500; font-size: 13px; border: none; background: transparent;")
            detail_layout.addWidget(lbl)
            
        step1_layout.addWidget(self.detail_box)
        add_subtle_shadow(step1_card)
        layout.addWidget(step1_card)

        # 3. STEP 2: CONDITION CHECK CARD
        self.step2_card = QFrame()
        self.step2_card.setObjectName("Step2Card")
        self.step2_card.setStyleSheet("""
            QFrame#Step2Card {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        step2_layout = QVBoxLayout(self.step2_card)
        step2_layout.setContentsMargins(20, 18, 20, 18)
        step2_layout.setSpacing(12)
        
        step2_title = QLabel("📋 Step 2. Condition Check")
        step2_title.setStyleSheet("color: #6b7280; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;")
        step2_layout.addWidget(step2_title)
        
        self.good_opt_card = ClickableOptionCard(
            "Good Condition", "Umbrella returned intact, no visible damage", 
            "#047857", "#f0fdf4"
        )
        self.damaged_opt_card = ClickableOptionCard(
            "Damaged", "Umbrella returned with some visible damage", 
            "#dc2626", "#fef2f2"
        )
        
        self.good_opt_card.clicked.connect(self.select_good_condition)
        self.damaged_opt_card.clicked.connect(self.select_damaged_condition)
        
        step2_layout.addWidget(self.good_opt_card)
        step2_layout.addWidget(self.damaged_opt_card)
        
        add_subtle_shadow(self.step2_card)
        layout.addWidget(self.step2_card)

        # 4. BOTTOM ACTION PROCESS BUTTON
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.process_btn = QPushButton("Process Return")
        self.process_btn.setFixedWidth(200)
        self.process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #11224d;
                border: 1px solid #11224d;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
            QPushButton:disabled {
                border: 1.5px solid #d1d5db;
                color: #9cb3e6;
                background-color: #f3f4f6;
            }
        """)
        self.process_btn.clicked.connect(self.process_return)
        btn_layout.addWidget(self.process_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
        self.refresh()

    def refresh(self):
        self.active_rent = None
        self.search_input.clear()
        self.user_lbl.setText("👤 User:       --")
        self.umbrella_lbl.setText("🌂 Umbrella:   --")
        self.borrowed_lbl.setText("📅 Borrowed:   --")
        self.due_lbl.setText("🕒 Due Date:   --")
        self.status_lbl.setText("⚠️ Status:     --")
        self.status_lbl.setStyleSheet("color: #374151; font-weight: 500; font-size: 13px; border: none; background: transparent;")
        
        self.select_good_condition()
        self.process_btn.setEnabled(False)

    def select_good_condition(self):
        self.selected_condition = "Good"
        self.good_opt_card.is_selected = True
        self.damaged_opt_card.is_selected = False
        self.good_opt_card.update_style()
        self.damaged_opt_card.update_style()

    def select_damaged_condition(self):
        self.selected_condition = "Damaged"
        self.good_opt_card.is_selected = False
        self.damaged_opt_card.is_selected = True
        self.good_opt_card.update_style()
        self.damaged_opt_card.update_style()

    def search_active_rental(self, text):
        query_str = text.strip()
        if not query_str:
            self.active_rent = None
            self.user_lbl.setText("👤 User:       --")
            self.umbrella_lbl.setText("🌂 Umbrella:   --")
            self.borrowed_lbl.setText("📅 Borrowed:   --")
            self.due_lbl.setText("🕒 Due Date:   --")
            self.status_lbl.setText("⚠️ Status:     --")
            self.status_lbl.setStyleSheet("color: #374151; font-weight: 500; font-size: 13px; border: none; background: transparent;")
            self.process_btn.setEnabled(False)
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Fetch user name, umbrella id, rent particulars
            cursor.execute("""
                SELECT r.rent_id, r.user_id, r.umbrella_id, r.rent_date, r.due_date, u.first_name, u.last_name
                FROM rents r
                JOIN USER u ON r.user_id = u.user_id
                LEFT JOIN returns ret ON r.rent_id = ret.rent_id
                WHERE ret.return_id IS NULL AND (r.user_id = ? OR (u.first_name || ' ' || u.last_name) LIKE ?)
                ORDER BY r.rent_date DESC
                LIMIT 1
            """, (query_str, f"%{query_str}%"))
            res = cursor.fetchone()
            conn.close()
            
            if res:
                rent_id, user_id, umb_id, rent_date, due_date, f_name, l_name = res
                self.active_rent = {
                    "rent_id": rent_id, "user_id": user_id, 
                    "umbrella_id": umb_id, "due_date": due_date
                }
                
                self.user_lbl.setText(f"👤 User:       {f_name} {l_name} ({user_id})")
                self.umbrella_lbl.setText(f"🌂 Umbrella:   {umb_id}")
                
                # Dynamic visual representation of date formatting
                self.borrowed_lbl.setText(f"📅 Borrowed:   {rent_date}")
                self.due_lbl.setText(f"🕒 Due Date:   {due_date}")
                
                # Overdue check
                overdue = False
                overdue_hours = 0
                now = datetime.now()
                try:
                    parts = due_date.split(" ")
                    dt_parts = parts[0].split("-")
                    tm_parts = parts[1].split(":")
                    ampm = parts[2]
                    
                    hr = int(tm_parts[0])
                    if ampm == "PM" and hr < 12:
                        hr += 12
                    if ampm == "AM" and hr == 12:
                        hr = 0
                        
                    due_dt = datetime(
                        int(dt_parts[0]),
                        int(dt_parts[1]),
                        int(dt_parts[2]),
                        hr,
                        int(tm_parts[1])
                    )
                    if now > due_dt:
                        overdue = True
                        diff = now - due_dt
                        overdue_hours = int(diff.total_seconds() / 3600)
                except Exception:
                    pass
                    
                if overdue:
                    self.status_lbl.setText(f"⚠️ Status:     OVERDUE by {max(1, overdue_hours)} hour(s)")
                    self.status_lbl.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 13px; border: none; background: transparent;")
                else:
                    self.status_lbl.setText("⚠️ Status:     ACTIVE LEASE - On Time")
                    self.status_lbl.setStyleSheet("color: #047857; font-weight: bold; font-size: 13px; border: none; background: transparent;")
                    
                self.process_btn.setEnabled(True)
            else:
                self.active_rent = None
                self.user_lbl.setText("👤 User:       --")
                self.umbrella_lbl.setText("🌂 Umbrella:   --")
                self.borrowed_lbl.setText("📅 Borrowed:   --")
                self.due_lbl.setText("🕒 Due Date:   --")
                self.status_lbl.setText("⚠️ Status:     No active lease found")
                self.status_lbl.setStyleSheet("color: #ef4444; font-size: 13px; border: none; background: transparent;")
                self.process_btn.setEnabled(False)
        except Exception as e:
            print(f"Error checking active rent: {e}")

    def process_return(self):
        if not self.active_rent:
            return
            
        rent_id = self.active_rent["rent_id"]
        umb_id = self.active_rent["umbrella_id"]
        user_id = self.active_rent["user_id"]
        due_date_str = self.active_rent["due_date"]
        
        condition = self.selected_condition
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now()
            ampm = "PM" if now.hour >= 12 else "AM"
            hours = now.hour % 12
            if hours == 0:
                hours = 12
            today_str = f"{now.year}-{now.month:02d}-{now.day:02d} {hours:02d}:{now.minute:02d} {ampm}"
            date_prefix = now.strftime("%m%d%y")
            
            # Log Return Record
            cursor.execute("INSERT INTO returns (rent_id, return_date, return_condition) VALUES (?, ?, ?)", (rent_id, today_str, condition))
            cursor.execute("UPDATE Umbrella SET current_status = 'Available' WHERE umbrella_id = ?", (umb_id,))
            
            fines = []
            
            # Damage checks
            if condition in ["Damaged", "Dysfunctional"]:
                cursor.execute("UPDATE Umbrella SET condition = ?, current_status = 'Maintenance' WHERE umbrella_id = ?", (condition, umb_id))
                prefix = "DMG" if condition == "Damaged" else "DYS"
                amount = 50.00 if condition == "Damaged" else 200.00
                
                cursor.execute("SELECT penalty_id FROM penalty WHERE penalty_id LIKE ? ORDER BY penalty_id DESC LIMIT 1", (f"{prefix}-{date_prefix}-%",))
                last_pen = cursor.fetchone()
                new_seq = int(last_pen[0].split("-")[2]) + 1 if last_pen else 1
                custom_penalty_id = f"{prefix}-{date_prefix}-{new_seq:03d}"
                
                cursor.execute("""
                    INSERT INTO penalty (penalty_id, user_id, penalty_reason, date_issued, amount, paid_status)
                    VALUES (?, ?, ?, ?, ?, 'Unpaid')
                """, (custom_penalty_id, user_id, f"Returned Umbrella {condition}", today_str, amount))
                fines.append(f"Property Damage Fine (₱{amount:.2f}) - Ref: {custom_penalty_id}")
                
            # Overdue fee calculation
            try:
                parts = due_date_str.split(" ")
                dt_parts = parts[0].split("-")
                tm_parts = parts[1].split(":")
                val_ampm = parts[2]
                due_hr = int(tm_parts[0])
                if val_ampm == "PM" and due_hr < 12:
                    due_hr += 12
                if val_ampm == "AM" and due_hr == 12:
                    due_hr = 0
                due_datetime = datetime(int(dt_parts[0]), int(dt_parts[1]), int(dt_parts[2]), due_hr, int(tm_parts[1]))
            except Exception:
                due_datetime = now
                
            if now > due_datetime:
                late_fee = 15.00
                cursor.execute("SELECT penalty_id FROM penalty WHERE penalty_id LIKE 'LATE-%' ORDER BY penalty_id DESC LIMIT 1")
                last_lt = cursor.fetchone()
                new_lt_seq = int(last_lt[0].split("-")[1]) + 1 if last_lt else 1
                late_id = f"LATE-{new_lt_seq:05d}"
                
                cursor.execute("""
                    INSERT INTO penalty (penalty_id, user_id, penalty_reason, date_issued, amount, paid_status)
                    VALUES (?, ?, 'Late Return Overdue Fee', ?, ?, 'Unpaid')
                """, (late_id, user_id, today_str, late_fee))
                fines.append(f"Overdue Late Return Fine (₱{late_fee:.2f}) - Ref: {late_id}")
                
            conn.commit()
            conn.close()
            
            ret_msg = f"Equipment safely returned and checked-in."
            if fines:
                ret_msg += "\n\n⚠️ INVOICED FINES APPLIED:\n" + "\n".join(fines)
                
            QMessageBox.information(self, "Turn-In Check-In Successful", ret_msg)
            
            self.refresh()
            self.main_win.refresh_stats()
            if hasattr(self.main_win, "rent_view"):
                self.main_win.rent_view.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Return Error", f"Failed to record check-in: {e}")


class PenaltiesViewCombined(QWidget):
    """Clean widget utilizing a sub-tab bar grouping Outstanding balances alongside transaction logs."""
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.sub_tab = QTabWidget()
        self.sub_tab.setStyleSheet("""
            QTabWidget::panel {
                border-top: 1px solid #e5e7eb;
                background-color: #f3f4f6;
            }
            QTabBar::tab {
                background-color: #e5e7eb;
                color: #4b5563;
                padding: 10px 20px;
                margin-right: 2px;
                border: 1px solid #e5e7eb;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #f3f4f6;
                color: #11224d;
                border-bottom: 2px solid #11224d;
            }
        """)
        
        self.penalties_tab = PenaltiesTab(self.db_path, self)
        self.payments_tab = PaymentsTab(self.db_path, self)
        
        self.sub_tab.addTab(self.penalties_tab, "Fines Outstanding")
        self.sub_tab.addTab(self.payments_tab, "Payments History Ledger")
        
        layout.addWidget(self.sub_tab)
        
    def refresh(self):
        self.penalties_tab.load_penalties()
        self.payments_tab.load_payments()


class RaincheckMainWindow(QMainWindow):
    """The main administrative portal containing the left solid-navy menu and the right page rendering panes."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UniRent - University's Umbrella Rental System")
        self.setMinimumSize(980, 640)
        
        # Central horizontal viewport
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. LEFT SIDEBAR NAVIGATION
        sidebar = QWidget()
        sidebar.setFixedWidth(230)
        sidebar.setObjectName("Sidebar")
        sidebar.setStyleSheet("""
            QWidget#Sidebar {
                background-color: #11224d;
                border: none;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 15)
        sidebar_layout.setSpacing(0)
        
        # HEADER BRANDING
        brand_frame = QFrame()
        brand_layout = QHBoxLayout(brand_frame)
        brand_layout.setContentsMargins(15, 20, 15, 20)
        brand_layout.setSpacing(10)
        
        logo = QLabel("<span style='font-size: 22px; color: #11224d;'>☂</span>")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(38, 38)
        logo.setStyleSheet("""
            background-color: #fedb41;
            border-radius: 6px;
        """)
        
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.setContentsMargins(0, 0, 0, 0)
        
        ubrand_lbl = QLabel("UniRent")
        ubrand_lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 19px; font-family: 'Segoe UI', Arial, sans-serif;")
        
        usub_lbl = QLabel("University's Umbrella\nRental System")
        usub_lbl.setStyleSheet("color: #9cb3e6; font-size: 9px; line-height: 11px; font-family: 'Segoe UI', sans-serif;")
        
        title_box.addWidget(ubrand_lbl)
        title_box.addWidget(usub_lbl)
        
        brand_layout.addWidget(logo)
        brand_layout.addLayout(title_box)
        
        sidebar_layout.addWidget(brand_frame)
        
        # BUTTONS GROUP
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []
        
        nav_items = [
            ("⊞  Dashboard", "dashboard"),
            ("✋  Rent", "rent"),
            ("↩  Return", "return"),
            ("🌂  Inventory", "inventory"),
            ("👥  Users", "users"),
            ("⚠️  Penalties", "penalties")
        ]
        
        for idx, (lbl_txt, key) in enumerate(nav_items):
            btn = QPushButton(lbl_txt)
            btn.setCheckable(True)
            btn.setFixedHeight(45)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #9cb3e6;
                    border: none;
                    padding-left: 20px;
                    text-align: left;
                    font-weight: bold;
                    font-size: 13px;
                    border-left: 4px solid transparent;
                    font-family: 'Segoe UI', sans-serif;
                }
                QPushButton:hover {
                    background-color: #1a3066;
                    color: #ffffff;
                }
                QPushButton:checked {
                    background-color: #1c336b;
                    color: #fedb41;
                    border-left: 4px solid #fedb41;
                }
            """)
            btn.clicked.connect(lambda checked, i=idx: self.switch_view(i))
            self.nav_group.addButton(btn, idx)
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)
        
        # 2. RIGHT WORKSPACE AREA
        right_workspace = QWidget()
        right_workspace.setStyleSheet("background-color: #f3f4f6;")
        right_layout = QVBoxLayout(right_workspace)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # RIGHT GLOBAL HEADER BAR
        header_bar = QWidget()
        header_bar.setStyleSheet("background-color: transparent;")
        header_bar_layout = QHBoxLayout(header_bar)
        header_bar_layout.setContentsMargins(20, 15, 20, 5)
        
        staff_badge = QLabel("Logged in as: Front Desk Staff")
        staff_badge.setStyleSheet("""
            QLabel {
                background-color: #11224d;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 16px;
                border-radius: 16px;
                font-family: 'Segoe UI', Arial;
                border: none;
            }
        """)
        header_bar_layout.addWidget(staff_badge)
        header_bar_layout.addStretch()
        right_layout.addWidget(header_bar)
        
        # VIEW STACK
        self.stacked_widget = QStackedWidget()
        
        # Instantiate separate views
        self.dashboard_view = DashboardPage(self)
        self.rent_view = RentPage(DB_FILE, self)
        self.return_view = ReturnPage(DB_FILE, self)
        self.inventory_view = UmbrellasTab(DB_FILE, self)
        self.users_view = UsersTab(DB_FILE, self)
        self.penalties_view = PenaltiesViewCombined(DB_FILE, self)
        
        self.stacked_widget.addWidget(self.dashboard_view) # 0
        self.stacked_widget.addWidget(self.rent_view)      # 1
        self.stacked_widget.addWidget(self.return_view)    # 2
        self.stacked_widget.addWidget(self.inventory_view) # 3
        self.stacked_widget.addWidget(self.users_view)     # 4
        self.stacked_widget.addWidget(self.penalties_view) # 5
        
        right_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(right_workspace)
        
        # Set initial active view Dashboard
        self.nav_buttons[0].setChecked(True)
        self.switch_view(0)
        
    def switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.nav_buttons[index].setChecked(True)
        
        # Reload views dynamically
        if index == 0:
            self.refresh_stats()
        elif index == 1:
            self.rent_view.refresh()
        elif index == 2:
            self.return_view.refresh()
        elif index == 3:
            self.inventory_view.load_umbrellas()
        elif index == 4:
            self.users_view.load_users()
        elif index == 5:
            self.penalties_view.refresh()
            
    def refresh_stats(self):
        """Cross-view metric calculations for instant layout sync. Yields perfect standard visual state matching screenshots."""
        avail, active, overdue = self.query_stats()
        self.dashboard_view.avail_card.set_value(avail)
        self.dashboard_view.active_card.set_value(active)
        self.dashboard_view.overdue_card.set_value(overdue)
        
    def refresh_payment_logs(self):
        """Help fulfill cross-tab calls in payments."""
        if hasattr(self, "penalties_view"):
            self.penalties_view.refresh()
        
    def query_stats(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Available Umbrellas count
            cursor.execute("SELECT COUNT(*) FROM Umbrella WHERE current_status = 'Available' AND condition != 'Dysfunctional'")
            avail = cursor.fetchone()[0]
            
            # Active Rentals count (Borrow records with no returns registered)
            cursor.execute("""
                SELECT COUNT(*) FROM rents r 
                LEFT JOIN returns ret ON r.rent_id = ret.rent_id 
                WHERE ret.return_id IS NULL
            """)
            active = cursor.fetchone()[0]
            
            # Retrieve active rent due dates for late check-in warning counts
            cursor.execute("""
                SELECT r.due_date FROM rents r 
                LEFT JOIN returns ret ON r.rent_id = ret.rent_id 
                WHERE ret.return_id IS NULL
            """)
            durations = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            overdue = 0
            now = datetime.now()
            for due_str in durations:
                try:
                    parts = due_str.split(" ")
                    dt_parts = parts[0].split("-")
                    tm_parts = parts[1].split(":")
                    ampm = parts[2]
                    
                    hr = int(tm_parts[0])
                    if ampm == "PM" and hr < 12:
                        hr += 12
                    if ampm == "AM" and hr == 12:
                        hr = 0
                        
                    due_dt = datetime(
                        int(dt_parts[0]),
                        int(dt_parts[1]),
                        int(dt_parts[2]),
                        hr,
                        int(tm_parts[1])
                    )
                    if now > due_dt:
                        overdue += 1
                except Exception:
                    pass
                    
            return avail, active, overdue
        except Exception as e:
            print(f"Error querying statistics: {e}")
            return 0, 0, 0


if __name__ == "__main__":
    init_database()
    app = QApplication(sys.argv)
    
    # Custom display font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = RaincheckMainWindow()
    window.show()
    sys.exit(app.exec())
