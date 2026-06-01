import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QLineEdit, QDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QCursor

def add_subtle_shadow(widget):
    import PyQt6.QtWidgets as QW
    shadow = QW.QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setXOffset(0)
    shadow.setYOffset(2)
    shadow.setColor(QColor(17, 24, 39, 15))
    widget.setGraphicsEffect(shadow)

class MiniStatCard(QFrame):
    """Mini stat card for umbrella counts."""
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
        
        icon_lbl = QLabel("🌂")
        icon_lbl.setStyleSheet("border: none; background: transparent; font-size: 16px; color: #9ca3af;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet("font-size: 34px; font-weight: bold; color: #111827; border: none; background: transparent;")
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.lbl_lbl = QLabel(label)
        self.lbl_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {text_color}; border: none; background: transparent;")
        self.lbl_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(icon_lbl)
        layout.addWidget(self.val_lbl)
        layout.addWidget(self.lbl_lbl)
        
        add_subtle_shadow(self)
        
    def set_value(self, value):
        self.val_lbl.setText(str(value))


class UmbrellasTab(QWidget):
    """The complete Umbrella Inventory Dashboard with live counts, search, status filters and operations."""
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.current_filter = "All"
        self.search_text = ""
        self.current_page = 0
        self.page_size = 7
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

        # 1. PAGE HEADER
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        title_lbl = QLabel("Umbrella Inventory")
        title_lbl.setStyleSheet("color: #111827; font-size: 18px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        
        sub_lbl = QLabel("Stock and condition tracking")
        sub_lbl.setStyleSheet("color: #6b7280; font-size: 11px; font-family: 'Segoe UI', sans-serif;")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()
        
        # Add new umbrella button
        add_umb_btn = QPushButton("+ Register Umbrella")
        add_umb_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_umb_btn.setStyleSheet("""
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
        add_umb_btn.clicked.connect(self.add_umbrella_dialog)
        header_layout.addWidget(add_umb_btn)
        
        layout.addLayout(header_layout)

        # 2. MINI STATS CARDS BAR
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        
        self.total_card = MiniStatCard("#3b82f6", "0", "Total Stock", "#2563eb", self)
        self.avail_card = MiniStatCard("#10b981", "0", "Available", "#059669", self)
        self.rented_card = MiniStatCard("#eab308", "0", "Rented out", "#ca8a04", self)
        self.maintenance_card = MiniStatCard("#ef4444", "0", "Maintenance", "#dc2626", self)
        
        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.avail_card)
        stats_layout.addWidget(self.rented_card)
        stats_layout.addWidget(self.maintenance_card)
        layout.addLayout(stats_layout)

        # 3. MAIN CONTAINER WINDOW CARD
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

        # Toolbar: Search box on left, status segment buttons on right
        toolbar_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search umbrella id...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11px;
                min-width: 200px;
                max-width: 300px;
            }
            QLineEdit:focus {
                border: 1px solid #11224d;
            }
        """)
        self.search_input.textChanged.connect(self.search_changed)
        toolbar_layout.addWidget(self.search_input)
        
        toolbar_layout.addStretch()
        
        # Segment filters layout
        self.filter_buttons = {}
        for text in ["All", "Available", "Rented", "Maintenance"]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #4b5563;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    padding: 6px 14px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f9fafb;
                    border: 1px solid #9ca3af;
                }
                QPushButton:checked {
                    background-color: #ffffff;
                    color: #11224d;
                    border: 1px solid #11224d;
                }
            """)
            btn.clicked.connect(lambda checked, t=text: self.filter_changed(t))
            toolbar_layout.addWidget(btn)
            self.filter_buttons[text] = btn
            
        self.filter_buttons["All"].setChecked(True)
        main_card_layout.addLayout(toolbar_layout)

        # Table widget
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["UMBRELLA ID", "CONDITION", "STATUS", "LAST RENTED BY", "ACTIONS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #111827;
                gridline-color: #f3f4f6;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #fefcf0; /* Light parchment gold header matching screenshot */
                color: #4b5563;
                padding: 10px;
                border: 1px solid #e5e7eb;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        main_card_layout.addWidget(self.table)
        
        # 4. PAGINATION FOOTER ROW
        pagination_layout = QHBoxLayout()
        self.stats_lbl = QLabel("Showing 1 to 7 of 60 umbrellas")
        self.stats_lbl.setStyleSheet("color: #6b7280; font-size: 11px; font-family: 'Segoe UI';")
        pagination_layout.addWidget(self.stats_lbl)
        pagination_layout.addStretch()
        
        self.pages_layout = QHBoxLayout()
        self.pages_layout.setSpacing(4)
        pagination_layout.addLayout(self.pages_layout)
        
        main_card_layout.addLayout(pagination_layout)
        
        add_subtle_shadow(main_card)
        layout.addWidget(main_card)
        
        self.load_umbrellas()

    def search_changed(self, text):
        self.search_text = text.strip()
        self.current_page = 0
        self.load_umbrellas()

    def filter_changed(self, category):
        self.current_filter = category
        self.current_page = 0
        for name, btn in self.filter_buttons.items():
            btn.setChecked(name == category)
        self.load_umbrellas()

    def update_stats_cards(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM Umbrella")
            tot = cursor.fetchone()[0]
            
            cursor.add_cb = True # temporary anchor
            cursor.execute("SELECT COUNT(*) FROM Umbrella WHERE current_status = 'Available'")
            avail = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM Umbrella WHERE current_status = 'Rented'")
            rent = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM Umbrella WHERE current_status = 'Maintenance'")
            maint = cursor.fetchone()[0]
            conn.close()
            
            self.total_card.set_value(tot)
            self.avail_card.set_value(avail)
            self.rented_card.set_value(rent)
            self.maintenance_card.set_value(maint)
        except Exception as e:
            print(f"Error reading umbrella stats: {e}")

    def load_umbrellas(self):
        self.update_stats_cards()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Form query with filter logic
            where_clauses = []
            params = []
            
            if self.current_filter != "All":
                where_clauses.append("current_status = ?")
                params.append(self.current_filter)
                
            if self.search_text:
                where_clauses.append("umbrella_id LIKE ?")
                params.append(f"%{self.search_text}%")
                
            where_sql = f"WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Count matching
            cursor.execute(f"SELECT COUNT(*) FROM Umbrella {where_sql}", params)
            total_matches = cursor.fetchone()[0]
            
            # Fetch all matching to paginate manually or with OFFSET LIMIT
            cursor.execute(f"""
                SELECT umbrella_id, condition, current_status 
                FROM Umbrella 
                {where_sql} 
                ORDER BY umbrella_id ASC
            """, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            # Update matching text
            start_num = self.current_page * self.page_size + 1 if total_matches > 0 else 0
            end_num = min(start_num + self.page_size - 1, total_matches)
            self.stats_lbl.setText(f"Showing {start_num} to {end_num} of {total_matches} umbrellas")
            
            # Paginate
            paginated_rows = rows[self.current_page * self.page_size : (self.current_page + 1) * self.page_size]
            
            self.table.setRowCount(0)
            self.table.verticalHeader().setVisible(False)
            
            for idx, r in enumerate(paginated_rows):
                self.table.insertRow(idx)
                umb_id, condition, status = r
                
                # UMBRELLA ID Item
                id_itm = QTableWidgetItem(umb_id)
                id_itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                id_itm.setForeground(QColor("#11224d"))
                id_itm.setFlags(id_itm.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(idx, 0, id_itm)
                
                # CONDITION Item
                cond_itm = QTableWidgetItem(condition.upper())
                cond_itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cond_font = QFont()
                cond_font.setBold(True)
                cond_itm.setFont(cond_font)
                if condition.upper() == "GOOD":
                    cond_itm.setForeground(QColor("#0284c7")) # Sky
                elif condition.upper() in ["DAMAGED", "MAINTENANCE"]:
                    cond_itm.setForeground(QColor("#d97706")) # Yellow/Gold
                else: # Dysfunctional
                    cond_itm.setForeground(QColor("#dc2626")) # Red
                cond_itm.setFlags(cond_itm.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(idx, 1, cond_itm)
                
                # STATUS Item
                stat_itm = QTableWidgetItem(status.upper())
                stat_itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                stat_font = QFont()
                stat_font.setBold(True)
                stat_itm.setFont(stat_font)
                if status.upper() == "AVAILABLE":
                    stat_itm.setForeground(QColor("#047857")) # Green
                elif status.upper() == "RENTED":
                    stat_itm.setForeground(QColor("#b45309")) # Gold
                else: # Maintenance
                    stat_itm.setForeground(QColor("#dc2626")) # Red
                stat_itm.setFlags(stat_itm.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(idx, 2, stat_itm)
                
                # LAST RENTED BY
                last_renter = self.get_last_renter(umb_id)
                ren_itm = QTableWidgetItem(last_renter)
                ren_itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                ren_itm.setFlags(ren_itm.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(idx, 3, ren_itm)
                
                # ACTIONS Widget (Edit/Delete buttons nicely grouped)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(6, 2, 6, 2)
                actions_layout.setSpacing(10)
                actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                edit_btn = QPushButton("✏ Edit")
                edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ecfdf5;
                        color: #047857;
                        border: 1px solid #a7f3d0;
                        border-radius: 4px;
                        font-size: 10px;
                        padding: 3px 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #34d399;
                        color: #ffffff;
                    }
                """)
                edit_btn.clicked.connect(lambda checked, u=umb_id, c=condition, s=status: self.edit_umbrella(u, c, s))
                
                del_btn = QPushButton("🗑 Delete")
                del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
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
                del_btn.clicked.connect(lambda checked, u=umb_id: self.delete_umbrella(u))
                
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(del_btn)
                
                self.table.setCellWidget(idx, 4, actions_widget)
                
            self.columns_layout_adjust()
            self.draw_pagination_controls(total_matches)
        except Exception as e:
            print(f"Error drawing umbrella table: {e}")

    def columns_layout_adjust(self):
        # Center column sizing
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 150)
        self.table.setRowHeight(0, 42)

    def get_last_renter(self, umb_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.first_name || ' ' || u.last_name 
                FROM rents r 
                JOIN USER u ON r.user_id = u.user_id 
                WHERE r.umbrella_id = ? 
                ORDER BY r.rent_date DESC 
                LIMIT 1
            """, (umb_id,))
            res = cursor.fetchone()
            conn.close()
            return res[0] if res else "-"
        except Exception:
            return "-"

    def draw_pagination_controls(self, total_matches):
        # Clear child layout
        for i in reversed(range(self.pages_layout.count())): 
            self.pages_layout.itemAt(i).widget().setParent(None)
            
        import math
        total_pages = math.ceil(total_matches / self.page_size)
        if total_pages <= 1:
            return
            
        def create_page_btn(text, target_page, active=False):
            btn = QPushButton(text)
            btn.setFixedSize(QSize(28, 28))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if active:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #11224d;
                        color: #ffffff;
                        border: none;
                        border-radius: 4px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #4b5563;
                        border: 1px solid #d1d5db;
                        border-radius: 4px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #f3f4f6;
                    }
                """)
            btn.clicked.connect(lambda: self.switch_page(target_page))
            return btn

        # Left arrow
        prev_page = max(0, self.current_page - 1)
        self.pages_layout.addWidget(create_page_btn("<", prev_page))
        
        # Display page labels (e.g. 1, 2, 3 ... 8)
        max_visible = 3
        for i in range(total_pages):
            if i < max_visible or i == total_pages - 1:
                self.pages_layout.addWidget(create_page_btn(str(i+1), i, active=(i == self.current_page)))
            elif i == max_visible:
                dots = QLabel("...")
                dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
                dots.setStyleSheet("color: #6b7280; font-size: 11px;")
                self.pages_layout.addWidget(dots)
                
        # Right arrow
        next_page = min(total_pages - 1, self.current_page + 1)
        self.pages_layout.addWidget(create_page_btn(">", next_page))

    def switch_page(self, page):
        self.current_page = page
        self.load_umbrellas()

    def add_umbrella_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Register New Umbrella")
        dialog.setFixedWidth(300)
        dialog.setStyleSheet("background-color: #ffffff;")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        id_lbl = QLabel("Umbrella ID (e.g. U-061):")
        id_input = QLineEdit()
        id_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }
        """)

        cond_lbl = QLabel("Condition:")
        cond_cmb = QComboBox()
        cond_cmb.addItems(["Good", "Damaged", "Dysfunctional"])
        cond_cmb.setStyleSheet("""
            QComboBox {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }
        """)

        layout.addWidget(id_lbl)
        layout.addWidget(id_input)
        layout.addWidget(cond_lbl)
        layout.addWidget(cond_cmb)

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
            cond = cond_cmb.currentText()

            if not uid:
                QMessageBox.warning(dialog, "Missing Fields", "Umbrella ID is required.")
                return

            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Umbrella (umbrella_id, current_status, condition) 
                    VALUES (?, 'Available', ?)
                """, (uid, cond))
                conn.commit()
                conn.close()
                dialog.accept()
                
                # Refresh dashboard stats
                main_win = self.window()
                if main_win and hasattr(main_win, "refresh_stats"):
                    main_win.refresh_stats()
                    
                self.load_umbrellas()
            except Exception as e:
                QMessageBox.critical(dialog, "Database Error", f"Registration failed: {e}")

        save_btn.clicked.connect(save)
        dialog.exec()

    def edit_umbrella(self, umb_id, condition, status):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Umbrella - {umb_id}")
        dialog.setFixedWidth(300)
        dialog.setStyleSheet("background-color: #ffffff;")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Condition
        cond_lbl = QLabel("Update Condition:")
        cond_cmb = QComboBox()
        cond_cmb.addItems(["Good", "Damaged", "Dysfunctional"])
        cond_cmb.setCurrentText(condition)
        
        # Status
        stat_lbl = QLabel("Update Status:")
        stat_cmb = QComboBox()
        stat_cmb.addItems(["Available", "Rented", "Maintenance"])
        stat_cmb.setCurrentText(status)

        combos = [cond_cmb, stat_cmb]
        for combo in combos:
            combo.setStyleSheet("""
                QComboBox {
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 12px;
                }
            """)

        layout.addWidget(cond_lbl)
        layout.addWidget(cond_cmb)
        layout.addWidget(stat_lbl)
        layout.addWidget(stat_cmb)

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
            new_cond = cond_cmb.currentText()
            new_stat = stat_cmb.currentText()
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Umbrella 
                    SET condition = ?, current_status = ? 
                    WHERE umbrella_id = ?
                """, (new_cond, new_stat, umb_id))
                conn.commit()
                conn.close()
                dialog.accept()
                
                # Refresh dashboard stats when inventory changes
                main_win = self.window()
                if main_win and hasattr(main_win, "refresh_stats"):
                    main_win.refresh_stats()
                    
                self.load_umbrellas()
            except Exception as e:
                QMessageBox.critical(dialog, "Database Error", f"Updating failed: {e}")

        save_btn.clicked.connect(save)
        dialog.exec()

    def delete_umbrella(self, umb_id):
        rep = QMessageBox.question(
            self, "Delete Umbrella", 
            f"Are you sure you want to delete umbrella {umb_id}?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if rep == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Umbrella WHERE umbrella_id = ?", (umb_id,))
                conn.commit()
                conn.close()
                
                # Refresh dashboard stats when inventory changes
                main_win = self.window()
                if main_win and hasattr(main_win, "refresh_stats"):
                    main_win.refresh_stats()
                    
                self.load_umbrellas()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete umbrella: {e}")
