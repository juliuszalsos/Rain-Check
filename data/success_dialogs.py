import sqlite3
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

class CustomSuccessDialogBase(QDialog):
    """Base dialog container implementing the clean aesthetic, professional spacing, and shadow of the mockups."""
    def __init__(self, border_top_color, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(400)
        
        # Outer container for shadowing
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(10, 10, 10, 10)
        
        self.frame = QFrame()
        self.frame.setObjectName("DialogCard")
        # Top accent border, white background, rounded border
        self.frame.setStyleSheet(f"""
            QFrame#DialogCard {{
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-top: 4px solid {border_top_color};
                border-radius: 12px;
            }}
        """)
        
        # Soft shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(17, 24, 39, 25))
        self.frame.setGraphicsEffect(shadow)
        
        self.layout = QVBoxLayout(self.frame)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(14)
        
        self.outer_layout.addWidget(self.frame)
        
    def add_header(self, title, subtitle, is_orange=False):
        """Header with structured icon and text alignment."""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Rounded Info Circle
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        circle_color = "#f59e0b" if is_orange else "#10b981"
        icon_char = "ℹ️"
        
        # Clean circular label styling
        icon_lbl.setStyleSheet(f"""
            QLabel {{
                border: 2px solid {circle_color};
                border-radius: 16px;
                background-color: transparent;
                font-size: 14px;
                color: {circle_color};
                font-weight: bold;
            }}
        """)
        icon_lbl.setText(icon_char)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: bold;
                color: #111827;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
        """)
        
        sub_lbl = QLabel(subtitle)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #4b5563;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
        """)
        
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(sub_lbl)
        
        header_layout.addWidget(icon_lbl)
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        
        self.layout.addLayout(header_layout)
        
    def add_ok_button(self):
        """Standard beautiful OK button aligned on the right."""
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setFixedSize(60, 28)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #11224d;
                border: 1px solid #11224d;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        self.layout.addLayout(btn_layout)


class RentSuccessDialog(CustomSuccessDialogBase):
    """Custom high-fidelity rent transaction success modal dialog."""
    def __init__(self, rent_id, due_date, parent=None):
        super().__init__("#10b981", parent)
        self.add_header("Equipment successfully leased!", "Umbrella is now checked out and assigned.")
        
        # Info Box 1: Rental ID (light blue card)
        rent_card = QFrame()
        rent_card.setStyleSheet("""
            QFrame {
                background-color: #eff6ff;
                border: none;
                border-radius: 6px;
            }
        """)
        rent_card_layout = QHBoxLayout(rent_card)
        rent_card_layout.setContentsMargins(12, 8, 12, 8)
        
        rent_lbl = QLabel(f"📋 Rental ID: {rent_id}")
        rent_lbl.setStyleSheet("""
            QLabel {
                color: #1e40af;
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        rent_card_layout.addWidget(rent_lbl)
        self.layout.addWidget(rent_card)
        
        # Info Box 2: Due Date (light green card)
        due_card = QFrame()
        due_card.setStyleSheet("""
            QFrame {
                background-color: #ecfdf5;
                border: none;
                border-radius: 6px;
            }
        """)
        due_card_layout = QHBoxLayout(due_card)
        due_card_layout.setContentsMargins(12, 8, 12, 8)
        
        due_lbl = QLabel(f"🕒 Due on: {due_date}")
        due_lbl.setStyleSheet("""
            QLabel {
                color: #065f46;
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        due_card_layout.addWidget(due_lbl)
        self.layout.addWidget(due_card)
        
        self.add_ok_button()


class ReturnSuccessDialog(CustomSuccessDialogBase):
    """Custom high-fidelity simple return checklist success modal dialog."""
    def __init__(self, parent=None):
        super().__init__("#10b981", parent)
        self.add_header("Return successful", "Equipment safely returned and checked in.")
        self.add_ok_button()


class PaymentSuccessDialog(CustomSuccessDialogBase):
    """Custom high-fidelity payment transaction receipt generation modal."""
    def __init__(self, payment_id, parent=None):
        super().__init__("#10b981", parent)
        self.add_header(
            "Payment recorded", 
            f"Successfully settled balance! Payment receipt ID created:\n{payment_id}"
        )
        self.add_ok_button()


class ReturnPenaltySuccessDialog(CustomSuccessDialogBase):
    """Custom high-fidelity penalty invoice modal overlay following late returns or property liabilities."""
    def __init__(self, reason, amount, penalty_id, parent=None):
        super().__init__("#f59e0b", parent)
        self.add_header(
            "Return successful", 
            "Equipment safely returned and checked in. An invoice has been issued for the following penalty.",
            is_orange=True
        )
        
        # Cream/Orange Invoiced Penalty Card
        penalty_card = QFrame()
        penalty_card.setStyleSheet("""
            QFrame {
                background-color: #fffbeb;
                border: 1px solid #fef3c7;
                border-radius: 6px;
            }
        """)
        penalty_layout = QHBoxLayout(penalty_card)
        penalty_layout.setContentsMargins(12, 10, 12, 10)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        type_lbl = QLabel("INVOICED PENALTY")
        type_lbl.setStyleSheet("""
            QLabel {
                color: #b45309;
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 0.5px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        
        desc_lbl = QLabel(reason)
        desc_lbl.setStyleSheet("""
            QLabel {
                color: #111827;
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        
        text_layout.addWidget(type_lbl)
        text_layout.addWidget(desc_lbl)
        
        amt_lbl = QLabel(f"₱ {amount:.2f}")
        amt_lbl.setStyleSheet("""
            QLabel {
                color: #b45309;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        amt_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        penalty_layout.addLayout(text_layout)
        penalty_layout.addStretch()
        penalty_layout.addWidget(amt_lbl)
        
        self.layout.addWidget(penalty_card)
        
        # Info Box 2: Reference Code Card (light blue)
        ref_card = QFrame()
        ref_card.setStyleSheet("""
            QFrame {
                background-color: #eff6ff;
                border: none;
                border-radius: 6px;
            }
        """)
        ref_layout = QHBoxLayout(ref_card)
        ref_layout.setContentsMargins(12, 8, 12, 8)
        
        ref_lbl = QLabel(f"REF: {penalty_id}")
        ref_lbl.setStyleSheet("""
            QLabel {
                color: #1e40af;
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        ref_layout.addWidget(ref_lbl)
        self.layout.addWidget(ref_card)
        
        self.add_ok_button()


class CustomDeleteConfirmationDialog(QDialog):
    """Custom high-fidelity confirmation dialog matching the Red Warning mockup."""
    def __init__(self, title, name_or_id, description_template, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(520)
        
        # Outer layout for shadowing
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #fecaca;
                border-top: 4px solid #ef4444;
                border-radius: 12px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(17, 24, 39, 20))
        frame.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header Row: Icon + Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Icon box
        icon_box = QFrame()
        icon_box.setFixedSize(40, 40)
        icon_box.setStyleSheet("""
            QFrame {
                background-color: #fee2e2;
                border-radius: 8px;
                border: none;
            }
        """)
        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel("🗑️")
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        icon_layout.addWidget(icon_lbl)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #111827;
                font-family: 'Segoe UI', system-ui, sans-serif;
                border: none;
                background: transparent;
            }
        """)
        
        header_layout.addWidget(icon_box)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Content Row
        content_lbl = QLabel()
        content_lbl.setWordWrap(True)
        content_lbl.setTextFormat(Qt.TextFormat.RichText)
        
        # Embed badge HTML
        badge_html = f"<span style='background-color: #fee2e2; color: #b91c1c; font-family: monospace; font-weight: bold; padding: 2px 6px; border-radius: 4px;'>{name_or_id}</span>"
        body_text = description_template.replace("{}", badge_html)
        
        content_lbl.setText(body_text)
        content_lbl.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #4b5563;
                font-family: 'Segoe UI', system-ui, sans-serif;
                line-height: 1.5;
                border: none;
                background: transparent;
            }
        """)
        layout.addWidget(content_lbl)
        
        # Buttons Row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedSize(85, 32)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #415163;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #f8fafc;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        delete_btn = QPushButton("DELETE")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setFixedSize(85, 32)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        delete_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)
        
        outer_layout.addWidget(frame)


class CustomCannotDeleteWarningDialog(QDialog):
    """Custom high-fidelity blocked warning matching the Amber Warning mockup."""
    def __init__(self, title, name_or_id, main_reason, sub_text=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(520)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #fef3c7;
                border-top: 4px solid #f59e0b;
                border-radius: 12px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(17, 24, 39, 20))
        frame.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header Row: Icon + Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        icon_box = QFrame()
        icon_box.setFixedSize(40, 40)
        icon_box.setStyleSheet("""
            QFrame {
                background-color: #fef3c7;
                border-radius: 20px;
                border: none;
            }
        """)
        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel("ⓘ")
        icon_lbl.setStyleSheet("""
            QLabel {
                font-size: 22px; 
                color: #d97706; 
                font-weight: bold; 
                background: transparent; 
                border: none;
            }
        """)
        icon_layout.addWidget(icon_lbl)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #111827;
                font-family: 'Segoe UI', system-ui, sans-serif;
                border: none;
                background: transparent;
            }
        """)
        
        header_layout.addWidget(icon_box)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Content Row
        content_lbl = QLabel()
        content_lbl.setWordWrap(True)
        content_lbl.setTextFormat(Qt.TextFormat.RichText)
        
        badge_html = f"<span style='background-color: #fef3c7; color: #b45309; font-family: monospace; font-weight: bold; padding: 2px 6px; border-radius: 4px;'>{name_or_id}</span>"
        body_text = f"{main_reason.replace('{}', badge_html)}"
        if sub_text:
            body_text += f"<br><span style='color: #7c2d12; font-weight: bold;'>{sub_text}</span>"
            
        content_lbl.setText(body_text)
        content_lbl.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #4b5563;
                font-family: 'Segoe UI', system-ui, sans-serif;
                line-height: 1.5;
                border: none;
                background: transparent;
            }
        """)
        layout.addWidget(content_lbl)
        
        # Buttons Row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setFixedSize(70, 32)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #11224d;
                border: 1px solid #11224d;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
        outer_layout.addWidget(frame)

