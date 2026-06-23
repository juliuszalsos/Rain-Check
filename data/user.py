import sqlite3
import re
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from data.success_dialogs import CustomDeleteConfirmationDialog, CustomCannotDeleteWarningDialog

def add_subtle_shadow(widget):
    import PyQt6.QtWidgets as QW
    shadow = QW.QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setXOffset(0)
    shadow.setYOffset(2)
    shadow.setColor(QColor(17, 24, 39, 15))
    widget.setGraphicsEffect(shadow)

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

class UsersTab(QWidget):
    """Clean widget grouping student user registries with a quick search filters panel."""
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.current_page = 0
        self.page_size = 8
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
        self.search_input.setPlaceholderText("🔍 Search student by ID, Name or RFID...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #11224d;
            }
        """)
        self.search_input.textChanged.connect(self.search_changed)
        ctl_layout.addWidget(self.search_input)
        
        ctl_layout.addStretch()

        # Add Student Button Layout Link
        self.add_btn = QPushButton("+ Register Student")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet("""
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
        self.add_btn.clicked.connect(self.add_student)
        ctl_layout.addWidget(self.add_btn)

        add_subtle_shadow(control_card)
        layout.addWidget(control_card)

        # Users Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Student / User ID", "First Name", "Last Name", "M.I.", "RFID UID", "Standing", "Actions"])
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 50)  # M.I.
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 110)  # Standing
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 150)  # Actions
        
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

        # Pagination Bar Card
        pagination_layout = QHBoxLayout()
        pagination_layout.setContentsMargins(5, 5, 5, 5)
        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet("color: #4b5563; font-size: 11px; font-weight: bold;")
        pagination_layout.addWidget(self.stats_lbl)
        pagination_layout.addStretch()
        
        self.pages_layout = QHBoxLayout()
        self.pages_layout.setSpacing(4)
        pagination_layout.addLayout(self.pages_layout)
        
        layout.addLayout(pagination_layout)

        self.setup_autocomplete()
        self.load_users()

    def setup_autocomplete(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, first_name, last_name, m_i, rfid_uid FROM USER")
            rows = cursor.fetchall()
            conn.close()
            
            suggestions = []
            for uid, fn, ln, mi, rfid in rows:
                mi_str = f" {mi}." if mi else ""
                full_name = f"{fn}{mi_str} {ln}"
                rfid_str = f" - RFID: {rfid}" if rfid else ""
                suggestions.append(f"{full_name} ({uid}){rfid_str}")
                
            from PyQt6.QtWidgets import QCompleter
            completer = QCompleter(suggestions, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(10)
            
            completer.activated.connect(self.on_completer_activated)
            self.search_input.setCompleter(completer)
        except Exception as e:
            print(f"Error setting up user autocomplete: {e}")

    def on_completer_activated(self, text):
        import re
        match = re.search(r"\(([^)]+)\)", text)
        if match:
            user_id = match.group(1)
            self.search_input.setText(user_id)
            self.search_changed(user_id)

    def search_changed(self, text):
        self.current_page = 0
        self.load_users()

    def switch_page(self, page):
        self.current_page = page
        self.load_users()

    def draw_pagination_controls(self, total_matches):
        while self.pages_layout.count():
            item = self.pages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        import math
        total_pages = math.ceil(total_matches / self.page_size)
        if total_pages <= 1:
            return
            
        def create_page_btn(text, target_page, active=False):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(28, 28)
            if active:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #11224d;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #4b5563;
                        border: 1px solid #e5e7eb;
                        border-radius: 4px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #f3f4f6;
                    }
                """)
            btn.clicked.connect(lambda checked, t=target_page: self.switch_page(t))
            return btn

        # Left arrow
        prev_page = max(0, self.current_page - 1)
        prev_btn = create_page_btn("<", prev_page)
        prev_btn.setEnabled(self.current_page > 0)
        if self.current_page == 0:
            prev_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #d1d5db;
                    border: 1px solid #e5e7eb;
                    border-radius: 4px;
                    font-size: 11px;
                }
            """)
        self.pages_layout.addWidget(prev_btn)
        
        # Sliding window calculation
        pages_to_show = []
        if total_pages <= 7:
            pages_to_show = list(range(total_pages))
        else:
            middle_start = max(1, self.current_page - 1)
            middle_end = min(total_pages - 2, self.current_page + 1)
            
            if self.current_page <= 2:
                middle_start = 1
                middle_end = 3
            elif self.current_page >= total_pages - 3:
                middle_start = total_pages - 4
                middle_end = total_pages - 2
                
            pages_to_show.append(0)
            if middle_start > 1:
                pages_to_show.append("...")
            for i in range(middle_start, middle_end + 1):
                pages_to_show.append(i)
            if middle_end < total_pages - 2:
                pages_to_show.append("...")
            pages_to_show.append(total_pages - 1)
            
        for item in pages_to_show:
            if item == "...":
                dots = QLabel("...")
                dots.setStyleSheet("color: #9ca3af; font-size: 11px;")
                dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
                dots.setFixedSize(28, 28)
                self.pages_layout.addWidget(dots)
            else:
                self.pages_layout.addWidget(create_page_btn(str(item + 1), item, active=(item == self.current_page)))
                
        # Right arrow
        next_page = min(total_pages - 1, self.current_page + 1)
        next_btn = create_page_btn(">", next_page)
        next_btn.setEnabled(self.current_page < total_pages - 1)
        if self.current_page == total_pages - 1:
            next_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #d1d5db;
                    border: 1px solid #e5e7eb;
                    border-radius: 4px;
                    font-size: 11px;
                }
            """)
        self.pages_layout.addWidget(next_btn)

    def load_users(self):
        sync_overdue_penalties(self.db_path)
        import re
        raw_text = self.search_input.text().strip()
        match = re.search(r"\(([^)]+)\)", raw_text)
        if match:
            query_str = match.group(1).strip()
            self.search_input.setText(query_str)
        else:
            query_str = raw_text
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Fetch active rentals via RENTAL table
            now = datetime.now()
            cursor.execute("""
                SELECT r.user_id, r.due_date 
                FROM RENTAL r
                WHERE r.return_date IS NULL OR r.return_date = ''
            """)
            active_rentals = {}
            for uid, due_str in cursor.fetchall():
                is_overdue = False
                try:
                    parts = due_str.split(" ")
                    dt_parts = parts[0].split("-")
                    tm_parts = parts[1].split(":")
                    ampm = parts[2]
                    hr = int(tm_parts[0])
                    mn = int(tm_parts[1])
                    if ampm == "PM" and hr < 12:
                        hr += 12
                    elif ampm == "AM" and hr == 12:
                        hr = 0
                    due_dt = datetime(int(dt_parts[0]), int(dt_parts[1]), int(dt_parts[2]), hr, mn)
                    if now > due_dt:
                        is_overdue = True
                except Exception:
                    pass
                if uid not in active_rentals:
                    active_rentals[uid] = []
                active_rentals[uid].append(is_overdue)
                
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

            total_matches = len(rows)
            start_num = self.current_page * self.page_size + 1 if total_matches > 0 else 0
            end_num = min(start_num + self.page_size - 1, total_matches)
            self.stats_lbl.setText(f"Showing {start_num}-{end_num} of {total_matches} students")
            
            paginated_rows = rows[self.current_page * self.page_size : (self.current_page + 1) * self.page_size]

            self.table.setRowCount(0)
            self.table.verticalHeader().setVisible(False)
            
            for idx, row in enumerate(paginated_rows):
                self.table.insertRow(idx)
                user_id = row[0]
                
                # Base User Fields (Columns 0-4)
                for col_idx, val in enumerate(row):
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    if col_idx in [0, 3, 4]:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        if col_idx == 0:
                            item.setForeground(QColor("#11224d"))
                    self.table.setItem(idx, col_idx, item)
                
                # Column 5: Status/Standing badge mapped to standard values (Overdue/Active/Returned)
                user_active = active_rentals.get(user_id, [])
                has_overdue = any(user_active)
                has_active = len(user_active) > 0
                
                if has_overdue:
                    standing_text = "Overdue"
                    standing_color = "#dc2626" # Red
                elif has_active:
                    standing_text = "Active"
                    standing_color = "#2563eb" # Blue
                else:
                    standing_text = "Returned"
                    standing_color = "#10b981" # Green
                    
                status_lbl = QLabel(standing_text)
                status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                status_lbl.setStyleSheet(f"""
                    QLabel {{
                        color: {standing_color};
                        font-weight: bold;
                        font-size: 11px;
                        background-color: transparent;
                    }}
                """)
                self.table.setCellWidget(idx, 5, status_lbl)
                
                # Column 6: Action buttons (Edit & Delete)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(6, 2, 6, 2)
                actions_layout.setSpacing(8)
                actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                edit_btn = QPushButton("✏ Edit")
                edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f0fdf4;
                        color: #15803d;
                        border: 1px solid #bbf7d0;
                        border-radius: 4px;
                        font-size: 10px;
                        padding: 3px 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #22c55e;
                        color: #ffffff;
                    }
                """)
                edit_btn.clicked.connect(lambda checked, u=user_id, fn=row[1], ln=row[2], mi=row[3], rfid=row[4]: self.edit_user(u, fn, ln, mi, rfid))
                actions_layout.addWidget(edit_btn)
                
                del_btn = QPushButton("🗑 Delete")
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #fef2f2;
                        color: #b91c1c;
                        border: 1px solid #fecaca;
                        border-radius: 4px;
                        font-size: 10px;
                        padding: 3px 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ef4444;
                        color: #ffffff;
                    }
                """)
                del_btn.clicked.connect(lambda checked, u=user_id: self.delete_user(u))
                actions_layout.addWidget(del_btn)
                
                self.table.setCellWidget(idx, 6, actions_widget)
                
            self.draw_pagination_controls(total_matches)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to retrieve user registry: {e}")

    def edit_user(self, user_id, first_name, last_name, m_i, rfid_uid):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Student Registry")
        dialog.setFixedWidth(460)
        dialog.setStyleSheet("background-color: #ffffff;")
        
        # Main layout with zero outer margins
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header Banner Container
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("background-color: #11224d; border: none;")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(20, 16, 20, 16)
        hdr_layout.setSpacing(14)
        
        avatar_lbl = QLabel("👤")
        avatar_lbl.setFixedSize(44, 44)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet("""
            QLabel {
                background-color: #f59e0b;
                color: #11224d;
                font-size: 24px;
                font-weight: bold;
                border-radius: 8px;
            }
        """)
        
        hdr_txt_layout = QVBoxLayout()
        hdr_txt_layout.setSpacing(2)
        hdr_txt_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel("Edit student details")
        title_lbl.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; font-family: 'Segoe UI', system-ui, sans-serif;")
        
        sub_title_lbl = QLabel("Raincheck | Umbrella Rental System")
        sub_title_lbl.setStyleSheet("color: #93c5fd; font-size: 11px; font-family: 'Segoe UI', system-ui, sans-serif;")
        
        hdr_txt_layout.addWidget(title_lbl)
        hdr_txt_layout.addWidget(sub_title_lbl)
        
        hdr_layout.addWidget(avatar_lbl)
        hdr_layout.addLayout(hdr_txt_layout)
        hdr_layout.addStretch()
        
        layout.addWidget(hdr_frame)
        
        # Form Body Container
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(24, 20, 24, 24)
        body_layout.setSpacing(16)
        
        # Student ID read-only field
        id_lbl = QLabel("STUDENT ID (READ-ONLY)")
        id_lbl.setStyleSheet("color: #4b5563; font-weight: bold; font-size: 10px; font-family: 'Segoe UI', sans-serif; letter-spacing: 0.5px;")
        id_input = QLineEdit(user_id)
        id_input.setEnabled(False)
        id_input.setStyleSheet("""
            QLineEdit {
                background-color: #f3f4f6;
                color: #9ca3af;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                font-family: monospace;
            }
        """)
        
        body_layout.addWidget(id_lbl)
        body_layout.addWidget(id_input)
        
        # Names row (First name, Last name, M.I.)
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        
        # First Name
        fn_col = QVBoxLayout()
        fn_col.setSpacing(4)
        fn_lbl = QLabel("FIRST NAME")
        fn_lbl.setStyleSheet("color: #4b5563; font-weight: bold; font-size: 10px; font-family: 'Segoe UI', sans-serif; letter-spacing: 0.5px;")
        fn_input = QLineEdit(first_name)
        fn_col.addWidget(fn_lbl)
        fn_col.addWidget(fn_input)
        
        # Last Name
        ln_col = QVBoxLayout()
        ln_col.setSpacing(4)
        ln_lbl = QLabel("LAST NAME")
        ln_lbl.setStyleSheet("color: #4b5563; font-weight: bold; font-size: 10px; font-family: 'Segoe UI', sans-serif; letter-spacing: 0.5px;")
        ln_input = QLineEdit(last_name)
        ln_col.addWidget(ln_lbl)
        ln_col.addWidget(ln_input)
        
        # Middle Initial
        mi_col = QVBoxLayout()
        mi_col.setSpacing(4)
        mi_lbl = QLabel("MIDDLE INITIAL")
        mi_lbl.setStyleSheet("color: #4b5563; font-weight: bold; font-size: 10px; font-family: 'Segoe UI', sans-serif; letter-spacing: 0.5px;")
        mi_input = QLineEdit(m_i)
        mi_input.setMaxLength(2)
        mi_col.addWidget(mi_lbl)
        mi_col.addWidget(mi_input)
        
        name_inputs = [fn_input, ln_input, mi_input]
        for nm_inp in name_inputs:
            nm_inp.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 13px;
                    color: #111827;
                    background-color: #ffffff;
                }
                QLineEdit:focus {
                    border: 2px solid #11224d;
                }
            """)
            
        name_row.addLayout(fn_col, 4)
        name_row.addLayout(ln_col, 4)
        name_row.addLayout(mi_col, 2)
        body_layout.addLayout(name_row)
        
        # RFID Card Enrollment dashed container
        rfid_box = QFrame()
        rfid_box.setStyleSheet("""
            QFrame {
                border: 2px dashed #3b82f6;
                border-radius: 8px;
                background-color: #f0f7ff;
            }
        """)
        rfid_box_layout = QVBoxLayout(rfid_box)
        rfid_box_layout.setContentsMargins(14, 12, 14, 12)
        rfid_box_layout.setSpacing(6)
        
        rfid_hdr = QLabel("📊 RFID CARD ENROLLMENT")
        rfid_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rfid_hdr.setStyleSheet("color: #2563eb; font-weight: bold; font-family: 'Segoe UI', sans-serif; font-size: 10px; letter-spacing: 0.5px; border: none; background: transparent;")
        
        rfid_body_layout = QHBoxLayout()
        rfid_body_layout.setSpacing(12)
        rfid_body_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        card_icon = QLabel("💳")
        card_icon.setStyleSheet("font-size: 26px; border: none; background: transparent;")
        
        rfid_txt_layout = QVBoxLayout()
        rfid_txt_layout.setSpacing(2)
        rfid_txt_layout.setContentsMargins(0, 0, 0, 0)
        
        tap_lbl = QLabel("Tap ID card on scanner now")
        tap_lbl.setStyleSheet("color: #1e40af; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        
        hold_lbl = QLabel("Hold card flat against the reader until confirmed")
        hold_lbl.setStyleSheet("color: #3b82f6; font-size: 11px; border: none; background: transparent;")
        
        rfid_txt_layout.addWidget(tap_lbl)
        rfid_txt_layout.addWidget(hold_lbl)
        
        # Real-time writing or reading input
        rfid_input = QLineEdit(rfid_uid)
        rfid_input.setPlaceholderText("Or enter RFID UID manually...")
        rfid_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bfdbfe;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                color: #1e40af;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 1.5px solid #2563eb;
            }
        """)
        rfid_txt_layout.addWidget(rfid_input)
        
        rfid_body_layout.addWidget(card_icon)
        rfid_body_layout.addLayout(rfid_txt_layout)
        
        rfid_box_layout.addWidget(rfid_hdr)
        rfid_box_layout.addLayout(rfid_body_layout)
        body_layout.addWidget(rfid_box)
        
        from PyQt6.QtGui import QRegularExpressionValidator
        from PyQt6.QtCore import QRegularExpression
        
        # Name validation: letters only
        name_regex = QRegularExpression("^[a-zA-Z\\s]*$")
        name_validator = QRegularExpressionValidator(name_regex, self)
        fn_input.setValidator(name_validator)
        ln_input.setValidator(name_validator)
        
        # M.I. restriction
        mi_regex = QRegularExpression("^[a-zA-Z\\s\\.]*$")
        mi_validator = QRegularExpressionValidator(mi_regex, self)
        mi_input.setValidator(mi_validator)
        
        # Buttons Row
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #11224d;
                border: 1px solid #11224d;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
        """)
        
        save_btn = QPushButton("💾 Update")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #11224d;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #1d3570;
            }
        """)
        
        btn_box.addWidget(cancel_btn, 1)
        btn_box.addWidget(save_btn, 1)
        body_layout.addLayout(btn_box)
        
        layout.addWidget(body_widget)
        
        cancel_btn.clicked.connect(dialog.reject)
        
        def save():
            fn = fn_input.text().strip()
            ln = ln_input.text().strip()
            mi = mi_input.text().strip().upper()
            rf = rfid_input.text().strip()
            
            if not fn or not ln:
                QMessageBox.warning(dialog, "Missing Fields", "First Name and Last Name are required.")
                return
                
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE USER 
                    SET first_name = ?, last_name = ?, m_i = ?, rfid_uid = ? 
                    WHERE user_id = ?
                """, (fn, ln, mi, rf, user_id))
                conn.commit()
                conn.close()
                dialog.accept()
                
                main_win = self.window()
                if main_win and hasattr(main_win, "refresh_stats"):
                    main_win.refresh_stats()
                self.load_users()
            except Exception as e:
                QMessageBox.critical(dialog, "Database Error", f"Failed to update user: {e}")
                
        save_btn.clicked.connect(save)
        dialog.exec()

    def delete_user(self, user_id):
        from datetime import datetime
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check active rental limit using RENTAL table
            cursor.execute("""
                SELECT COUNT(*) FROM RENTAL r
                WHERE r.user_id = ? AND (r.return_date IS NULL OR r.return_date = '')
            """, (user_id,))
            active_count = cursor.fetchone()[0]
            
            # Check outstanding unpaid penalties count
            cursor.execute("SELECT COUNT(*) FROM penalty WHERE user_id = ? AND paid_status = 'Unpaid'", (user_id,))
            penalty_count = cursor.fetchone()[0]
            
            overdue_count = 0
            if active_count > 0:
                cursor.execute("""
                    SELECT r.due_date FROM RENTAL r
                    WHERE r.user_id = ? AND (r.return_date IS NULL OR r.return_date = '')
                """, (user_id,))
                due_dates = [r[0] for r in cursor.fetchall()]
                now = datetime.now()
                for due_str in due_dates:
                    try:
                        parts = due_str.split(" ")
                        dt_parts = parts[0].split("-")
                        tm_parts = parts[1].split(":")
                        ampm = parts[2]
                        hr = int(tm_parts[0])
                        mn = int(tm_parts[1])
                        if ampm == "PM" and hr < 12:
                            hr += 12
                        elif ampm == "AM" and hr == 12:
                            hr = 0
                        due_dt = datetime(int(dt_parts[0]), int(dt_parts[1]), int(dt_parts[2]), hr, mn)
                        if now > due_dt:
                            overdue_count += 1
                    except Exception:
                        pass
            conn.close()
            
            if active_count > 0 or penalty_count > 0:
                reasons = []
                if overdue_count > 0:
                    reasons.append("has active overdue rental")
                elif active_count > 0:
                    reasons.append("has an active umbrella rental checked out")
                if penalty_count > 0:
                    reasons.append(f"has {penalty_count} outstanding unpaid penalty/fines")
                
                reason_text = "This student currently: " + " and ".join(reasons) + "."
                if len(reasons) == 1 and "has an active umbrella rental checked out" in reasons[0]:
                    reason_text = "This student currently has an active umbrella rental checked out."
                
                warning_dialog = CustomCannotDeleteWarningDialog(
                    "Cannot delete user",
                    user_id,
                    "User ID {} cannot be deleted.",
                    sub_text=reason_text,
                    parent=self
                )
                warning_dialog.exec()
                return
        except Exception as e:
            print(f"Error checking status for user deletion: {e}")

        # Show Delete User Dialog using Custom confirmation dialog
        confirm_dialog = CustomDeleteConfirmationDialog(
            "Delete user",
            user_id,
            "Are you sure you want to permanently delete User ID {} from the system database?<br>This action cannot be undone.",
            parent=self
        )
        if confirm_dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM USER WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                
                main_win = self.window()
                if main_win and hasattr(main_win, "refresh_stats"):
                    main_win.refresh_stats()
                    
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete user: {e}")

    def add_student(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register New Student")
        dialog.setFixedWidth(460)
        dialog.setStyleSheet("background-color: #ffffff;")
        
        # Main layout with zero outer margins
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header Banner Container
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("background-color: #11224d; border: none;")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(20, 16, 20, 16)
        hdr_layout.setSpacing(14)
        
        avatar_lbl = QLabel("👤")
        avatar_lbl.setFixedSize(44, 44)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet("""
            QLabel {
                background-color: #f59e0b;
                color: #11224d;
                font-size: 24px;
                font-weight: bold;
                border-radius: 8px;
            }
        """)
        
        hdr_txt_layout = QVBoxLayout()
        hdr_txt_layout.setSpacing(2)
        hdr_txt_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel("Register new student")
        title_lbl.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; font-family: 'Segoe UI', system-ui, sans-serif;")
        
        sub_title_lbl = QLabel("Raincheck | Umbrella Rental System")
        sub_title_lbl.setStyleSheet("color: #93c5fd; font-size: 11px; font-family: 'Segoe UI', system-ui, sans-serif;")
        
        hdr_txt_layout.addWidget(title_lbl)
        hdr_txt_layout.addWidget(sub_title_lbl)
        
        hdr_layout.addWidget(avatar_lbl)
        hdr_layout.addLayout(hdr_txt_layout)
        hdr_layout.addStretch()
        
        layout.addWidget(hdr_frame)
        
        # Form Body Container
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(24, 20, 24, 24)
        body_layout.setSpacing(16)
        
        # Student ID field styled as a distinct hero card
        id_lbl = QLabel("STUDENT ID")
        id_lbl.setStyleSheet("color: #4b5563; font-weight: bold; font-size: 10px; font-family: 'Segoe UI', sans-serif; letter-spacing: 0.5px;")
        id_input = QLineEdit()
        id_input.setInputMask("0000-0000;_")
        id_input.setPlaceholderText("e.g. 2021-0008")
        id_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #11224d;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                color: #111827;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #2563eb;
            }
        """)
        
        body_layout.addWidget(id_lbl)
        body_layout.addWidget(id_input)
        
        # Grid/Columns for Name fields side-by-side
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        
        # First Name
        fn_col = QVBoxLayout()
        fn_col.setSpacing(4)
        fn_lbl = QLabel("FIRST NAME")
        fn_lbl.setStyleSheet("color: #4b5563; font-weight: bold; font-size: 10px; font-family: 'Segoe UI', sans-serif; letter-spacing: 0.5px;")
        fn_input = QLineEdit()
        fn_input.setPlaceholderText("Maria")
        fn_col.addWidget(fn_lbl)
        fn_col.addWidget(fn_input)
        
        # Last Name
        ln_col = QVBoxLayout()
        ln_col.setSpacing(4)
        ln_lbl = QLabel("LAST NAME")
        ln_lbl.setStyleSheet("color: #4b5563; font-weight: bold; font-size: 10px; font-family: 'Segoe UI', sans-serif; letter-spacing: 0.5px;")
        ln_input = QLineEdit()
        ln_input.setPlaceholderText("Reyes")
        ln_col.addWidget(ln_lbl)
        ln_col.addWidget(ln_input)
        
        # Middle Initial
        mi_col = QVBoxLayout()
        mi_col.setSpacing(4)
        mi_lbl = QLabel("MIDDLE INITIAL")
        mi_lbl.setStyleSheet("color: #4b5563; font-weight: bold; font-size: 10px; font-family: 'Segoe UI', sans-serif; letter-spacing: 0.5px;")
        mi_input = QLineEdit()
        mi_input.setPlaceholderText("C.")
        mi_input.setMaxLength(2)
        mi_col.addWidget(mi_lbl)
        mi_col.addWidget(mi_input)
        
        # Style fn, ln, mi textboxes
        name_inputs = [fn_input, ln_input, mi_input]
        for nm_inp in name_inputs:
            nm_inp.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 13px;
                    color: #111827;
                    background-color: #ffffff;
                }
                QLineEdit:focus {
                    border: 2px solid #11224d;
                }
            """)
            
        name_row.addLayout(fn_col, 4)
        name_row.addLayout(ln_col, 4)
        name_row.addLayout(mi_col, 2)
        body_layout.addLayout(name_row)
        
        # RFID Card Enrollment dashed card
        rfid_box = QFrame()
        rfid_box.setStyleSheet("""
            QFrame {
                border: 2px dashed #3b82f6;
                border-radius: 8px;
                background-color: #f0f7ff;
            }
        """)
        rfid_box_layout = QVBoxLayout(rfid_box)
        rfid_box_layout.setContentsMargins(14, 12, 14, 12)
        rfid_box_layout.setSpacing(6)
        
        rfid_hdr = QLabel("📊 RFID CARD ENROLLMENT")
        rfid_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rfid_hdr.setStyleSheet("color: #2563eb; font-weight: bold; font-family: 'Segoe UI', sans-serif; font-size: 10px; letter-spacing: 0.5px; border: none; background: transparent;")
        
        rfid_body_layout = QHBoxLayout()
        rfid_body_layout.setSpacing(12)
        rfid_body_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        card_icon = QLabel("💳")
        card_icon.setStyleSheet("font-size: 26px; border: none; background: transparent;")
        
        rfid_txt_layout = QVBoxLayout()
        rfid_txt_layout.setSpacing(2)
        rfid_txt_layout.setContentsMargins(0, 0, 0, 0)
        
        tap_lbl = QLabel("Tap ID card on scanner now")
        tap_lbl.setStyleSheet("color: #1e40af; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        
        hold_lbl = QLabel("Hold card flat against the reader until confirmed")
        hold_lbl.setStyleSheet("color: #3b82f6; font-size: 11px; border: none; background: transparent;")
        
        rfid_txt_layout.addWidget(tap_lbl)
        rfid_txt_layout.addWidget(hold_lbl)
        
        # Let the RFID scanner write into field beautifully
        rfid_input = QLineEdit()
        rfid_input.setPlaceholderText("Or enter RFID UID manually...")
        rfid_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bfdbfe;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                color: #1e40af;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 1.5px solid #2563eb;
            }
        """)
        rfid_txt_layout.addWidget(rfid_input)
        
        rfid_body_layout.addWidget(card_icon)
        rfid_body_layout.addLayout(rfid_txt_layout)
        
        rfid_box_layout.addWidget(rfid_hdr)
        rfid_box_layout.addLayout(rfid_body_layout)
        body_layout.addWidget(rfid_box)
        
        from PyQt6.QtGui import QRegularExpressionValidator
        from PyQt6.QtCore import QRegularExpression
        
        # Name constraints (letters and space only to match clean standards)
        name_regex = QRegularExpression("^[a-zA-Z\\s]*$")
        name_validator = QRegularExpressionValidator(name_regex, self)
        fn_input.setValidator(name_validator)
        ln_input.setValidator(name_validator)
        
        # Middle Initial constraints
        mi_regex = QRegularExpression("^[a-zA-Z\\s\\.]*$")
        mi_validator = QRegularExpressionValidator(mi_regex, self)
        mi_input.setValidator(mi_validator)
        mi_input.setMaxLength(2)
        
        # Buttons Row
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #11224d;
                border: 1px solid #11224d;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
        """)
        
        save_btn = QPushButton("💾 Save")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #11224d;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #1d3570;
            }
        """)
        
        btn_box.addWidget(cancel_btn, 1)
        btn_box.addWidget(save_btn, 1)
        body_layout.addLayout(btn_box)
        
        layout.addWidget(body_widget)
        
        cancel_btn.clicked.connect(dialog.reject)
        
        def save():
            uid = id_input.text().strip()
            fn = fn_input.text().strip()
            ln = ln_input.text().strip()
            mi = mi_input.text().strip().upper()
            rf = rfid_input.text().strip()
            
            if not uid or not fn or not ln:
                QMessageBox.warning(dialog, "Missing Fields", "ID, First Name, and Last Name are required.")
                return
                
            # Check mask completion
            if len(uid) < 9 or "_" in uid or "-" not in uid:
                QMessageBox.warning(dialog, "Invalid Student ID", "Please enter a valid Student ID in the format YYYY-NNNN (e.g. 2026-1234).")
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
                
                # Refresh dashboard stats
                main_win = self.window()
                if main_win and hasattr(main_win, "refresh_stats"):
                    main_win.refresh_stats()
                    
                self.load_users()
            except Exception as e:
                QMessageBox.critical(dialog, "Database Error", f"Registration failed: {e}")
                
        save_btn.clicked.connect(save)
        dialog.exec()
