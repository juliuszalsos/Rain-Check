import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListView, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QCursor
from datetime import datetime

try:
    from data.success_dialogs import PaymentSuccessDialog
except ImportError:
    from success_dialogs import PaymentSuccessDialog

def sync_overdue_penalties(db_path):
    import sqlite3
    from datetime import datetime
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Correctly query active rentals using RENTAL table
        cursor.execute("""
            SELECT r.rental_id, r.user_id, r.due_date 
            FROM RENTAL r
            WHERE r.return_date IS NULL OR r.return_date = ''
        """)
        active_rentals = cursor.fetchall()
        
        now = datetime.now()
        
        for rent_id, user_id, due_date_str in active_rentals:
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
                continue
                
            if now > due_datetime:
                penalty_id = f"LATE-{rent_id}"
                cursor.execute("SELECT COUNT(*) FROM penalty WHERE penalty_id = ?", (penalty_id,))
                if cursor.fetchone()[0] == 0:
                    ampm = "PM" if now.hour >= 12 else "AM"
                    hours = now.hour % 12
                    if hours == 0:
                        hours = 12
                    today_str = f"{now.year}-{now.month:02d}-{now.day:02d} {hours:02d}:{now.minute:02d} {ampm}"
                    
                    cursor.execute("""
                        INSERT INTO penalty (penalty_id, user_id, penalty_reason, date_issued, amount, paid_status)
                        VALUES (?, ?, 'Late Return Overdue Fee', ?, 15.00, 'Unpaid')
                    """, (penalty_id, user_id, today_str))
                    
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error in sync_overdue_penalties: {e}")

class MiniStatCard(QFrame):
    """Mini stat card for penalty metrics with specialized background/borders."""
    def __init__(self, border_color, value, label, text_color, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-top: 4px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(2)
        
        icon_lbl = QLabel("⚖️")
        icon_lbl.setStyleSheet("border: none; background: transparent; font-size: 16px; color: #9ca3af;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet("font-size: 30px; font-weight: bold; color: #111827; border: none; background: transparent;")
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.lbl_lbl = QLabel(label)
        self.lbl_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {text_color}; border: none; background: transparent;")
        self.lbl_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(icon_lbl)
        layout.addWidget(self.val_lbl)
        layout.addWidget(self.lbl_lbl)
        
        # Soft shadow
        import PyQt6.QtWidgets as QW
        shadow = QW.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(17, 24, 39, 12))
        self.setGraphicsEffect(shadow)
        
    def set_value(self, value):
        self.val_lbl.setText(str(value))


class PenaltiesTab(QWidget):
    """Modern Admin Penalty ledger complete with live statistics, search filter, segment statuses, and full workflows."""
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.current_filter = "All"
        self.search_text = ""
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f3f4f6;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. HEADER ROW
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        title_lbl = QLabel("Penalty & Fines Ledger")
        title_lbl.setStyleSheet("color: #111827; font-size: 18px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        
        sub_lbl = QLabel("Student infractions, property liabilities and dues settlements")
        sub_lbl.setStyleSheet("color: #6b7280; font-size: 11px; font-family: 'Segoe UI', sans-serif;")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Action Buttons Row
        self.add_pen_btn = QPushButton("+ Issue Penalty")
        self.add_pen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_pen_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        self.add_pen_btn.clicked.connect(self.issue_penalty)
        header_layout.addWidget(self.add_pen_btn)

        self.pay_btn = QPushButton("💳 Process Payment")
        self.pay_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pay_btn.setStyleSheet("""
            QPushButton {
                background-color: #11224d;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1c356e;
            }
        """)
        self.pay_btn.clicked.connect(self.process_payment)
        header_layout.addWidget(self.pay_btn)
        
        layout.addLayout(header_layout)

        # 2. STATS CARDS BAR
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        
        self.unpaid_count_card = MiniStatCard("#ef4444", "0", "Fine Dues Unpaid", "#dc2626", self)
        self.unpaid_amt_card = MiniStatCard("#fbbf24", "₱0.00", "Total Outstanding (₱)", "#d97706", self)
        self.paid_count_card = MiniStatCard("#10b981", "0", "Settled Fines", "#059669", self)
        self.paid_amt_card = MiniStatCard("#3b82f6", "₱0.00", "Total Collected (₱)", "#2563eb", self)
        
        stats_layout.addWidget(self.unpaid_count_card)
        stats_layout.addWidget(self.unpaid_amt_card)
        stats_layout.addWidget(self.paid_count_card)
        stats_layout.addWidget(self.paid_amt_card)
        layout.addLayout(stats_layout)

        # 3. CONTAINER CARD FOR FILTER TOOLBAR & TABLE
        main_card = QFrame()
        main_card.setObjectName("MainCard")
        main_card.setStyleSheet("""
            QFrame#MainCard {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        
        main_card_layout = QVBoxLayout(main_card)
        main_card_layout.setContentsMargins(18, 18, 18, 18)
        main_card_layout.setSpacing(14)

        # Toolbar Row
        toolbar_layout = QHBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Penalty ID, student name, ID or reason...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border: 2px solid #11224d;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(self.search_input)
        
        toolbar_layout.addStretch()

        # Status segment buttons
        segment_layout = QHBoxLayout()
        segment_layout.setSpacing(2)
        
        self.seg_all = QPushButton("All")
        self.seg_unpaid = QPushButton("Outstanding")
        self.seg_paid = QPushButton("Settled")
        
        self.segment_btns = [self.seg_all, self.seg_unpaid, self.seg_paid]
        for btn in self.segment_btns:
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f3f4f6;
                    color: #4b5563;
                    border: 1px solid #d1d5db;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e5e7eb;
                }
                QPushButton:checked {
                    background-color: #11224d;
                    color: #ffffff;
                    border-color: #11224d;
                }
            """)
        
        self.seg_all.setChecked(True)
        self.seg_all.clicked.connect(lambda: self.switch_segment("All"))
        self.seg_unpaid.clicked.connect(lambda: self.switch_segment("Unpaid"))
        self.seg_paid.clicked.connect(lambda: self.switch_segment("Paid"))
        
        # Set border radius for visual pill look
        self.seg_all.setStyleSheet(self.seg_all.styleSheet() + "QPushButton { border-top-left-radius: 6px; border-bottom-left-radius: 6px; }")
        self.seg_paid.setStyleSheet(self.seg_paid.styleSheet() + "QPushButton { border-top-right-radius: 6px; border-bottom-right-radius: 6px; }")
        
        for btn in self.segment_btns:
            segment_layout.addWidget(btn)
            
        toolbar_layout.addLayout(segment_layout)
        main_card_layout.addLayout(toolbar_layout)

        # 4. LEDGER TABLE WIDGET
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Penalty ID", "Student ID", "Student Name", "Reason", "Date Issued", "Amount (₱)", "Status"
        ])
        
        # Layout fitting
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Name fits contents
        
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
                color: #374151;
                padding: 10px;
                border: 1px solid #e5e7eb;
                font-weight: bold;
                font-size: 11px;
            }
            QTableCornerButton::section {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
            }
        """)
        
        main_card_layout.addWidget(self.table)
        
        # Bottom status row
        self.status_lbl = QLabel("Showing 0 records")
        self.status_lbl.setStyleSheet("color: #6b7280; font-size: 11px; font-weight: bold;")
        main_card_layout.addWidget(self.status_lbl)
        
        layout.addWidget(main_card)
        
        # Seed dynamic loads
        self.setup_autocomplete()
        self.load_penalties()

    def update_metrics(self):
        """Fetch and render total aggregate KPIs dynamically."""
        sync_overdue_penalties(self.db_path)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. Unpaid penalty count
            cursor.execute("SELECT COUNT(*) FROM penalty WHERE paid_status = 'Unpaid'")
            unpaid_cnt = cursor.fetchone()[0]
            
            # 2. Unpaid total sum amount
            cursor.execute("SELECT SUM(amount) FROM penalty WHERE paid_status = 'Unpaid'")
            unpaid_sum_val = cursor.fetchone()[0] or 0.00
            
            # 3. Paid penalty count
            cursor.execute("SELECT COUNT(*) FROM penalty WHERE paid_status = 'Paid'")
            paid_cnt = cursor.fetchone()[0]
            
            # 4. Paid total sum receipts
            cursor.execute("SELECT SUM(amount) FROM penalty WHERE paid_status = 'Paid'")
            paid_sum_val = cursor.fetchone()[0] or 0.00
            
            conn.close()
            
            # Bind
            self.unpaid_count_card.set_value(unpaid_cnt)
            self.unpaid_amt_card.set_value(f"₱{unpaid_sum_val:.2f}")
            self.paid_count_card.set_value(paid_cnt)
            self.paid_amt_card.set_value(f"₱{paid_sum_val:.2f}")
            
        except Exception as e:
            print(f"Error fetching penalty metrics: {e}")

    def load_penalties(self):
        """Loads and filters fines directly from SQLite dynamic join structure."""
        self.update_metrics()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Dynamic query assembly
            query = """
                SELECT penalty.penalty_id, penalty.user_id, USER.first_name || ' ' || USER.last_name, 
                       penalty.penalty_reason, penalty.date_issued, penalty.amount, penalty.paid_status
                FROM penalty 
                LEFT JOIN USER ON penalty.user_id = USER.user_id
                WHERE 1=1
            """
            params = []
            
            # Segment filter
            if self.current_filter == "Unpaid":
                query += " AND penalty.paid_status = 'Unpaid'"
            elif self.current_filter == "Paid":
                query += " AND penalty.paid_status = 'Paid'"
                
            # Search query
            if self.search_text:
                query += """ AND (penalty.penalty_id LIKE ? 
                                 OR penalty.user_id LIKE ? 
                                 OR (USER.first_name || ' ' || USER.last_name) LIKE ?
                                 OR penalty.penalty_reason LIKE ?)"""
                like_str = f"%{self.search_text}%"
                params.extend([like_str, like_str, like_str, like_str])
                
            query += " ORDER BY penalty.date_issued DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(0)
            self.status_lbl.setText(f"Showing {len(rows)} records")
            
            for idx, row in enumerate(rows):
                self.table.insertRow(idx)
                for col_idx, val in enumerate(row):
                    if col_idx == 5: # Amount
                        item = QTableWidgetItem(f"₱{float(val):.2f}")
                    else:
                        item = QTableWidgetItem(str(val))
                        
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    
                    # Layout centering and custom color rendering styles
                    if col_idx in [0, 1, 4, 6]:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    elif col_idx == 5:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        
                    # Format ID cells as primary-color navy
                    if col_idx == 0:
                        item.setForeground(QColor("#11224d"))
                        bf = QFont()
                        bf.setBold(True)
                        item.setFont(bf)
                        
                    # Format Status Cells
                    if col_idx == 6:
                        bf = QFont()
                        if val == "Paid":
                            item.setForeground(QColor("#10b981")) # Fresh green
                            bf.setBold(True)
                        else:
                            item.setForeground(QColor("#ef4444")) # High danger alert red
                        item.setFont(bf)
                        
                    self.table.setItem(idx, col_idx, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "Retrieval Error", f"Failed to retrieve penalties: {e}")

    def setup_autocomplete(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT penalty.penalty_id, penalty.user_id, USER.first_name, USER.last_name, penalty.penalty_reason
                FROM penalty
                LEFT JOIN USER ON penalty.user_id = USER.user_id
            """)
            rows = cursor.fetchall()
            conn.close()
            
            suggestions = []
            for pid, uid, fn, ln, reason in rows:
                fn_str = fn if fn else ""
                ln_str = ln if ln else ""
                full_name = f"{fn_str} {ln_str}".strip()
                name_clause = f" ({full_name})" if full_name else ""
                suggestions.append(f"Ticket: {pid} - User: {uid}{name_clause} - Reason: {reason}")
                
            from PyQt6.QtWidgets import QCompleter
            completer = QCompleter(suggestions, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(10)
            
            completer.activated.connect(self.on_completer_activated)
            self.search_input.setCompleter(completer)
        except Exception as e:
            print(f"Error setting up penalty autocomplete: {e}")

    def on_completer_activated(self, text):
        import re
        match = re.search(r"Ticket:\s*(\w+)", text, re.IGNORECASE)
        if match:
            ticket_id = match.group(1)
            self.search_input.setText(ticket_id)
            self.on_search_changed(ticket_id)

    def on_search_changed(self, text):
        import re
        txt_to_parse = str(text) if text is not None else ""
        match = re.search(r"Ticket:\s*(\w+)", txt_to_parse, re.IGNORECASE)
        if match:
            self.search_text = match.group(1)
            self.search_input.setText(self.search_text)
        else:
            self.search_text = txt_to_parse.strip()
        self.load_penalties()

    def switch_segment(self, filter_type):
        self.current_filter = filter_type
        # Sync segments checked states
        if filter_type == "All":
            self.seg_all.setChecked(True)
            self.seg_unpaid.setChecked(False)
            self.seg_paid.setChecked(False)
        elif filter_type == "Unpaid":
            self.seg_all.setChecked(False)
            self.seg_unpaid.setChecked(True)
            self.seg_paid.setChecked(False)
        else:
            self.seg_all.setChecked(False)
            self.seg_unpaid.setChecked(False)
            self.seg_paid.setChecked(True)
            
        self.load_penalties()

    def issue_penalty(self):
        """Pops up high-fidelity issue manual penalty window."""
        dialog = IssuePenaltyDialog(self.db_path, self)
        if dialog.exec():
            # Sibling stats trigger if possible
            main_win = self.window()
            if main_win and hasattr(main_win, "refresh_stats"):
                main_win.refresh_stats()
                
            self.load_penalties()

    def process_payment(self):
        """Pops up modern confirmation penalty fine resolution window."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selection Required", "Please click on a fine ticket record row in the table below first to process.")
            return

        p_id = self.table.item(selected_row, 0).text()
        status = self.table.item(selected_row, 6).text()
        raw_amt_txt = self.table.item(selected_row, 5).text().replace("₱", "")
        amount = float(raw_amt_txt)

        if status == "Paid":
            QMessageBox.warning(self, "Settled Balance", f"Fine ticket ID '{p_id}' has already been processed and resolved.")
            return

        # Settle fine ticket pop up
        dialog = PenaltyPaymentDialog(self.db_path, p_id, amount, self)
        if dialog.exec():
            # Refresh payments sibling and app level stats
            self.load_penalties()
            main_win = self.window()
            if main_win:
                if hasattr(main_win, "refresh_payment_logs"):
                    main_win.refresh_payment_logs()
                if hasattr(main_win, "refresh_stats"):
                    main_win.refresh_stats()


class IssuePenaltyDialog(QDialog):
    """Custom high-fidelity dialog for issuing manual penalty tickets to students."""
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.init_ui()
        self.load_students()
        
    def init_ui(self):
        self.setWindowTitle("Issue Manual Penalty")
        self.setFixedWidth(420)
        self.setStyleSheet("QDialog { background-color: #ffffff; }")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- HEADER ---
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header_frame.setStyleSheet("""
            QFrame#HeaderFrame {
                background-color: #11224d;
                border: none;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 18, 20, 18)
        header_layout.setSpacing(14)
        
        icon_badge = QLabel()
        icon_badge.setFixedSize(44, 44)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(239, 68, 68, 0.12);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 8px;
                font-size: 20px;
                color: #ef4444;
            }
        """)
        icon_badge.setText("⚠️")
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel("Issue penalty ticket")
        title_lbl.setStyleSheet("QLabel { color: #ffffff; font-size: 16px; font-weight: bold; font-family: 'Segoe UI'; background: transparent; }")
        
        sub_lbl = QLabel("Raincheck | Umbrella Rental System")
        sub_lbl.setStyleSheet("QLabel { color: #8da2cf; font-size: 11px; font-family: 'Segoe UI'; background: transparent; }")
        
        title_layout.addWidget(title_lbl)
        title_layout.addWidget(sub_lbl)
        header_layout.addWidget(icon_badge)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)
        
        # --- BODY FORM ---
        body_frame = QFrame()
        body_frame.setObjectName("BodyFrame")
        body_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        body_frame.setStyleSheet("QFrame#BodyFrame { background-color: #ffffff; border: none; }")
        body_layout = QVBoxLayout(body_frame)
        body_layout.setContentsMargins(24, 24, 24, 24)
        body_layout.setSpacing(18)
        
        # 1. Target Student lookup
        stud_layout = QVBoxLayout()
        stud_layout.setSpacing(6)
        stud_lbl = QLabel("SELECT STUDENT")
        stud_lbl.setStyleSheet("QLabel { color: #6b7280; font-size: 10px; font-weight: bold; letter-spacing: 0.8px; }")
        
        self.stud_cmb = QComboBox()
        self.stud_cmb.setView(QListView())
        self.stud_cmb.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QComboBox:focus { border: 2px solid #11224d; }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #111827;
                selection-background-color: #11224d;
                selection-color: #ffffff;
                border: 1px solid #d1d5db;
            }
        """)
        stud_layout.addWidget(stud_lbl)
        stud_layout.addWidget(self.stud_cmb)
        body_layout.addLayout(stud_layout)
        
        # 2. Penalty Type / Reason
        reason_layout = QVBoxLayout()
        reason_layout.setSpacing(6)
        reason_lbl = QLabel("PENALTY REASON")
        reason_lbl.setStyleSheet("QLabel { color: #6b7280; font-size: 10px; font-weight: bold; letter-spacing: 0.8px; }")
        
        self.reason_cmb = QComboBox()
        self.reason_cmb.setView(QListView())
        self.reason_cmb.addItems([
            "Late Return Overdue Fee",
            "Damaged Umbrella",
            "Dysfunctional Umbrella",
            "Lost Umbrella",
            "Other Policy Violation"
        ])
        self.reason_cmb.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QComboBox:focus { border: 2px solid #11224d; }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #111827;
                selection-background-color: #11224d;
                selection-color: #ffffff;
                border: 1px solid #d1d5db;
            }
        """)
        self.reason_cmb.currentIndexChanged.connect(self.auto_fill_amount)
        reason_layout.addWidget(reason_lbl)
        reason_layout.addWidget(self.reason_cmb)
        body_layout.addLayout(reason_layout)
        
        # 3. Fine Amount
        amt_layout = QVBoxLayout()
        amt_layout.setSpacing(6)
        amt_lbl = QLabel("FINE AMOUNT (₱)")
        amt_lbl.setStyleSheet("QLabel { color: #6b7280; font-size: 10px; font-weight: bold; letter-spacing: 0.8px; }")
        
        self.amt_input = QLineEdit()
        self.amt_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                font-family: monospace;
            }
            QLineEdit:focus { border: 2px solid #11224d; }
        """)
        amt_layout.addWidget(amt_lbl)
        amt_layout.addWidget(self.amt_input)
        body_layout.addLayout(amt_layout)
        
        # Fill default amount
        self.auto_fill_amount(0)
        
        body_layout.addSpacing(6)
        
        # Actions Row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #11224d;
                border: 1px solid #11224d;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #f3f4f6; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.issue_btn = QPushButton("⚖️ Issue Ticket")
        self.issue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.issue_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
                min-width: 120px;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        self.issue_btn.clicked.connect(self.issue_ticket)
        
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.issue_btn)
        body_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(body_frame)

    def load_students(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, first_name, last_name FROM USER ORDER BY last_name ASC")
            students = cursor.fetchall()
            conn.close()
            
            for uid, f_name, l_name in students:
                self.stud_cmb.addItem(f"{uid} - {l_name}, {f_name}", uid)
        except Exception:
            self.stud_cmb.addItem("No students available", "")

    def auto_fill_amount(self, index):
        reason = self.reason_cmb.currentText()
        if reason == "Late Return Overdue Fee":
            self.amt_input.setText("15.00")
        elif reason == "Damaged Umbrella":
            self.amt_input.setText("50.00")
        elif reason == "Dysfunctional Umbrella":
            self.amt_input.setText("200.00")
        elif reason == "Lost Umbrella":
            self.amt_input.setText("250.00")
        else:
            self.amt_input.setText("20.00")

    def issue_ticket(self):
        user_id = self.stud_cmb.currentData()
        reason = self.reason_cmb.currentText()
        amt_str = self.amt_input.text().strip()
        
        if not user_id:
            QMessageBox.warning(self, "Validation Error", "Please select a valid student.")
            return
            
        try:
            amount = float(amt_str)
            if amount < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please provide a valid non-negative amount.")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate a custom ID
            now = datetime.now()
            date_prefix = now.strftime("%m%d%y")
            
            # Prefix mapping based on infraction
            if "Overdue" in reason or "Late" in reason:
                prefix = "LATE"
            elif "Damaged" in reason:
                prefix = "DMG"
            elif "Dysfunctional" in reason:
                prefix = "DYS"
            elif "Lost" in reason:
                prefix = "LOST"
            else:
                prefix = "GEN"
                
            cursor.execute("SELECT penalty_id FROM penalty WHERE penalty_id LIKE ? ORDER BY penalty_id DESC LIMIT 1", (f"{prefix}-{date_prefix}-%",))
            last_pen = cursor.fetchone()
            new_seq = int(last_pen[0].split("-")[2]) + 1 if last_pen else 1
            custom_penalty_id = f"{prefix}-{date_prefix}-{new_seq:03d}"
            
            # Date string standard
            ampm = "PM" if now.hour >= 12 else "AM"
            hours = now.hour % 12
            if hours == 0:
                hours = 12
            today_str = f"{now.year}-{now.month:02d}-{now.day:02d} {hours:02d}:{now.minute:02d} {ampm}"
            
            cursor.execute("""
                INSERT INTO penalty (penalty_id, user_id, penalty_reason, date_issued, amount, paid_status)
                VALUES (?, ?, ?, ?, ?, 'Unpaid')
            """, (custom_penalty_id, user_id, reason, today_str, amount))
            conn.commit()
            conn.close()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to issue manual penalty ticket: {e}")


class PenaltyPaymentDialog(QDialog):
    """Custom high-fidelity processing payment dialog matching the Raincheck signature UI aesthetics."""
    def __init__(self, db_path, penalty_id, amount, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.p_id = penalty_id
        self.amount = amount
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Settle Penalty Fine")
        self.setFixedWidth(400)
        self.setStyleSheet("QDialog { background-color: #ffffff; }")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- HEADER ---
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header_frame.setStyleSheet("""
            QFrame#HeaderFrame {
                background-color: #11224d;
                border: none;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 18, 20, 18)
        header_layout.setSpacing(14)
        
        icon_badge = QLabel()
        icon_badge.setFixedSize(44, 44)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(16, 185, 129, 0.12);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: 8px;
                font-size: 22px;
                color: #10b981;
                font-weight: bold;
            }
        """)
        icon_badge.setText("₱")
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel("Settle penalty fine")
        title_lbl.setStyleSheet("QLabel { color: #ffffff; font-size: 16px; font-weight: bold; font-family: 'Segoe UI'; background: transparent; }")
        
        sub_lbl = QLabel("Raincheck | Umbrella Rental System")
        sub_lbl.setStyleSheet("QLabel { color: #8da2cf; font-size: 11px; font-family: 'Segoe UI'; background: transparent; }")
        
        title_layout.addWidget(title_lbl)
        title_layout.addWidget(sub_lbl)
        header_layout.addWidget(icon_badge)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)
        
        # --- BODY PANEL ---
        body_frame = QFrame()
        body_frame.setObjectName("BodyFrame")
        body_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        body_frame.setStyleSheet("QFrame#BodyFrame { background-color: #ffffff; border: none; }")
        body_layout = QVBoxLayout(body_frame)
        body_layout.setContentsMargins(24, 24, 24, 24)
        body_layout.setSpacing(18)
        
        # Show citation info
        citation_layout = QVBoxLayout()
        citation_layout.setSpacing(4)
        citation_lbl = QLabel("PENALTY ACCOUNT")
        citation_lbl.setStyleSheet("QLabel { color: #6b7280; font-size: 10px; font-weight: bold; letter-spacing: 0.8px; }")
        
        self.cite_info = QLabel(f"Processing ID: {self.p_id}\nTotal Fine Amount Due: ₱{self.amount:.2f}")
        self.cite_info.setStyleSheet("""
            QLabel {
                background-color: #f9fafb;
                color: #374151;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        citation_layout.addWidget(citation_lbl)
        citation_layout.addWidget(self.cite_info)
        body_layout.addLayout(citation_layout)
        
        # 1. Payment Method
        method_layout = QVBoxLayout()
        method_layout.setSpacing(6)
        method_lbl = QLabel("PAYMENT METHOD")
        method_lbl.setStyleSheet("QLabel { color: #6b7280; font-size: 10px; font-weight: bold; letter-spacing: 0.8px; }")
        
        self.method_cmb = QComboBox()
        self.method_cmb.setView(QListView())
        self.method_cmb.addItems(["Cash", "Gcash", "Maya", "RFID Link"])
        self.method_cmb.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QComboBox:focus { border: 2px solid #11224d; }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #111827;
                selection-background-color: #11224d;
                selection-color: #ffffff;
                border: 1px solid #d1d5db;
            }
        """)
        method_layout.addWidget(method_lbl)
        method_layout.addWidget(self.method_cmb)
        body_layout.addLayout(method_layout)
        
        # 2. Amount verification
        ver_layout = QVBoxLayout()
        ver_layout.setSpacing(6)
        ver_lbl = QLabel("VERIFY PAID AMOUNT (₱)")
        ver_lbl.setStyleSheet("QLabel { color: #6b7280; font-size: 10px; font-weight: bold; letter-spacing: 0.8px; }")
        
        self.pay_input = QLineEdit(f"{self.amount:.2f}")
        self.pay_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                font-family: monospace;
            }
            QLineEdit:focus { border: 2px solid #11224d; }
        """)
        ver_layout.addWidget(ver_lbl)
        ver_layout.addWidget(self.pay_input)
        body_layout.addLayout(ver_layout)
        
        body_layout.addSpacing(6)
        
        # Buttons Row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #11224d;
                border: 1px solid #11224d;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #f3f4f6; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.pay_confirm_btn = QPushButton("💳 Confirm Pay")
        self.pay_confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pay_confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
                min-width: 120px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.pay_confirm_btn.clicked.connect(self.process_confirm)
        
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.pay_confirm_btn)
        body_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(body_frame)

    def process_confirm(self):
        try:
            entered_paid = float(self.pay_input.text().strip())
            if abs(entered_paid - self.amount) > 0.01:
                QMessageBox.warning(self, "Amount Mismatch", f"Paid amount must exactly equal the fine due: ₱{self.amount:.2f}")
                return

            now = datetime.now()
            date_prefix = now.strftime("%m%d%y")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Record Transaction
            cursor.execute("SELECT payment_id FROM payments WHERE payment_id LIKE ? ORDER BY payment_id DESC LIMIT 1", (f"{date_prefix}-%",))
            last_pay = cursor.fetchone()
            new_sequence = int(last_pay[0].split("-")[1]) + 1 if last_pay else 1
            custom_payment_id = f"{date_prefix}-{new_sequence:03d}"

            # Standard AM/PM formatting
            ampm = "PM" if now.hour >= 12 else "AM"
            hours = now.hour % 12
            if hours == 0:
                hours = 12
            payment_date_str = f"{now.year}-{now.month:02d}-{now.day:02d} {hours:02d}:{now.minute:02d} {ampm}"

            # Update database
            cursor.execute("UPDATE penalty SET paid_status = 'Paid' WHERE penalty_id = ?", (self.p_id,))
            cursor.execute("""
                INSERT INTO payments (payment_id, penalty_id, method, amount_paid, payment_date)
                VALUES (?, ?, ?, ?, ?)
            """, (custom_payment_id, self.p_id, self.method_cmb.currentText(), entered_paid, payment_date_str))

            conn.commit()
            conn.close()

            dlg = PaymentSuccessDialog(custom_payment_id, self)
            dlg.exec()
            self.accept()

        except ValueError:
            QMessageBox.warning(self, "Invalid Entry", "Please enter a valid numeric currency amount.")
        except Exception as e:
            QMessageBox.critical(self, "Transaction Failed", f"Database failed to process transaction: {e}")
