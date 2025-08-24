import sys
import os
import asyncio
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QFileDialog, QProgressBar, QTextEdit, QMessageBox,
                             QGroupBox, QGridLayout)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon

# Import các module crawl
from crawl_tiktok import open_tiktok_search
from crawl_youtube import YouTubeViewCrawler
from crawl_aliexpress import capture_aliexpress_api
from crawl_instagram import open_instagram_search
from crawl_temu import open_temu


class CrawlThread(QThread):
    """Thread riêng để chạy crawl không block UI"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, crawl_type, keyword, save_path):
        super().__init__()
        self.crawl_type = crawl_type
        self.keyword = keyword
        self.save_path = save_path
        
    def run(self):
        try:
            if self.crawl_type == "tiktok":
                self.progress_signal.emit("Đang khởi tạo TikTok crawler...")
                # Chạy TikTok crawler
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(open_tiktok_search(self.keyword))
                loop.close()
                
                # Di chuyển file CSV đến thư mục đã chọn
                csv_file = f'tiktok_videos_{self.keyword}.csv'
                if os.path.exists(csv_file):
                    new_path = os.path.join(self.save_path, csv_file)
                    os.rename(csv_file, new_path)
                    self.progress_signal.emit(f"Đã lưu file CSV tại: {new_path}")
                    self.finished_signal.emit(True, f"Hoàn thành crawl TikTok! File: {new_path}")
                else:
                    self.finished_signal.emit(False, "Không tìm thấy file CSV được tạo")
                    
            elif self.crawl_type == "youtube":
                self.progress_signal.emit("Đang khởi tạo YouTube crawler...")
                # Chạy YouTube crawler
                crawler = YouTubeViewCrawler()
                
                self.progress_signal.emit("Đang tìm kiếm videos...")
                result = crawler.crawl_videos(query=self.keyword, max_results=50)
                
                if result and result.get('total_videos', 0) > 0:
                    # Di chuyển file CSV đến thư mục đã chọn
                    csv_file = f'youtube_videos_{self.keyword}.csv'
                    if os.path.exists(csv_file):
                        new_path = os.path.join(self.save_path, csv_file)
                        os.rename(csv_file, new_path)
                        self.progress_signal.emit(f"Đã lưu file CSV tại: {new_path}")
                        self.finished_signal.emit(True, f"Hoàn thành crawl YouTube! Tìm thấy {result['total_videos']} videos. File: {new_path}")
                    else:
                        self.finished_signal.emit(False, "Không tìm thấy file CSV được tạo")
                else:
                    self.finished_signal.emit(False, "Không tìm thấy videos nào")
                    
            elif self.crawl_type == "aliexpress":
                self.progress_signal.emit("Đang khởi tạo AliExpress crawler...")
                # Chạy AliExpress crawler (không cần keyword)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(capture_aliexpress_api())
                loop.close()
                
                self.progress_signal.emit("AliExpress crawler đã hoàn thành!")
                self.finished_signal.emit(True, "Hoàn thành crawl AliExpress! Kiểm tra console để xem kết quả.")
                
            elif self.crawl_type == "instagram":
                self.progress_signal.emit("Đang khởi tạo Instagram crawler...")
                # Chạy Instagram crawler (cần keyword)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(open_instagram_search(self.keyword))
                loop.close()
                
                # Kiểm tra file CSV được tạo
                csv_files = [f for f in os.listdir('.') if f.startswith('instagram_search_') and f.endswith('.csv')]
                if csv_files:
                    # Di chuyển file CSV đến thư mục đã chọn
                    csv_file = csv_files[0]
                    new_path = os.path.join(self.save_path, csv_file)
                    os.rename(csv_file, new_path)
                    self.progress_signal.emit(f"Đã lưu file CSV tại: {new_path}")
                    self.finished_signal.emit(True, f"Hoàn thành crawl Instagram! File: {new_path}")
                else:
                    self.finished_signal.emit(False, "Không tìm thấy file CSV được tạo")
                    
            elif self.crawl_type == "temu":
                self.progress_signal.emit("Đang khởi tạo Temu crawler...")
                # Chạy Temu crawler
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(open_temu())
                loop.close()
                
                # Kiểm tra file CSV được tạo
                csv_files = [f for f in os.listdir('.') if f.startswith('temu_') and f.endswith('.csv')]
                if csv_files:
                    # Di chuyển file CSV đến thư mục đã chọn
                    csv_file = csv_files[0]
                    new_path = os.path.join(self.save_path, csv_file)
                    os.rename(csv_file, new_path)
                    self.progress_signal.emit(f"Đã lưu file CSV tại: {new_path}")
                    self.finished_signal.emit(True, f"Hoàn thành crawl Temu! File: {new_path}")
                else:
                    self.finished_signal.emit(False, "Không tìm thấy file CSV được tạo")
                    
        except Exception as e:
            self.finished_signal.emit(False, f"Lỗi: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Social Media Crawler - TikTok, YouTube, AliExpress, Instagram, Temu")
        self.setGeometry(100, 100, 800, 600)
        
        # Biến lưu trữ
        self.save_path = ""
        self.current_crawl_type = ""
        
        # Khởi tạo UI
        self.init_ui()
        
    def init_ui(self):
        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Tiêu đề
        title_label = QLabel("Social Media Crawler")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("TikTok • YouTube • AliExpress • Instagram • Temu")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 20px;")
        main_layout.addWidget(subtitle_label)
        
        # Group chọn loại crawl
        crawl_group = QGroupBox("Chọn loại crawl")
        crawl_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        crawl_layout = QVBoxLayout(crawl_group)
        
        # Layout cho các button - sử dụng GridLayout để sắp xếp 5 button
        button_grid = QGridLayout()
        button_grid.setSpacing(15)
        
        # Button TikTok
        self.tiktok_btn = QPushButton("TikTok\nCrawler")
        self.tiktok_btn.setFont(QFont("Arial", 12))
        self.tiktok_btn.setMinimumHeight(80)
        self.tiktok_btn.setMinimumWidth(150)
        self.tiktok_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0050;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e6004c;
            }
            QPushButton:pressed {
                background-color: #cc0047;
            }
        """)
        self.tiktok_btn.clicked.connect(lambda: self.select_crawl_type("tiktok"))
        
        # Button YouTube
        self.youtube_btn = QPushButton("YouTube\nCrawler")
        self.youtube_btn.setFont(QFont("Arial", 12))
        self.youtube_btn.setMinimumHeight(80)
        self.youtube_btn.setMinimumWidth(150)
        self.youtube_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e60000;
            }
            QPushButton:pressed {
                background-color: #cc0000;
            }
        """)
        self.youtube_btn.clicked.connect(lambda: self.select_crawl_type("youtube"))
        
        # Button AliExpress
        self.aliexpress_btn = QPushButton("AliExpress\nCrawler")
        self.aliexpress_btn.setFont(QFont("Arial", 12))
        self.aliexpress_btn.setMinimumHeight(80)
        self.aliexpress_btn.setMinimumWidth(150)
        self.aliexpress_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6600;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e65c00;
            }
            QPushButton:pressed {
                background-color: #cc5200;
            }
        """)
        self.aliexpress_btn.clicked.connect(lambda: self.select_crawl_type("aliexpress"))
        
        # Button Instagram
        self.instagram_btn = QPushButton("Instagram\nCrawler")
        self.instagram_btn.setFont(QFont("Arial", 12))
        self.instagram_btn.setMinimumHeight(80)
        self.instagram_btn.setMinimumWidth(150)
        self.instagram_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f09433, stop:1 #e6683c, stop:2 #dc2743, stop:3 #cc2366, stop:4 #bc1888);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e0852a, stop:1 #d55f33, stop:2 #cb1e3a, stop:3 #bb1a5d, stop:4 #ab177f);
            }
        """)
        self.instagram_btn.clicked.connect(lambda: self.select_crawl_type("instagram"))
        
        # Button Temu
        self.temu_btn = QPushButton("Temu\nCrawler")
        self.temu_btn.setFont(QFont("Arial", 12))
        self.temu_btn.setMinimumHeight(80)
        self.temu_btn.setMinimumWidth(150)
        self.temu_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b35;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e65a2a;
            }
            QPushButton:pressed {
                background-color: #cc4f25;
            }
        """)
        self.temu_btn.clicked.connect(lambda: self.select_crawl_type("temu"))
        
        # Sắp xếp các button vào grid (2 hàng, 3 cột)
        button_grid.addWidget(self.tiktok_btn, 0, 0)
        button_grid.addWidget(self.youtube_btn, 0, 1)
        button_grid.addWidget(self.aliexpress_btn, 0, 2)
        button_grid.addWidget(self.instagram_btn, 1, 0)
        button_grid.addWidget(self.temu_btn, 1, 1)
        
        crawl_layout.addLayout(button_grid)
        
        # Label hiển thị chế độ đang chọn
        self.mode_label = QLabel("Chưa chọn chế độ crawl")
        self.mode_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label.setMinimumHeight(40)
        self.mode_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 8px;
                font-style: italic;
            }
        """)
        crawl_layout.addWidget(self.mode_label)
        
        main_layout.addWidget(crawl_group)
        
        # Group nhập keyword (chỉ hiển thị cho TikTok, YouTube và Temu)
        self.keyword_group = QGroupBox("Nhập keyword")
        self.keyword_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        keyword_layout = QVBoxLayout(self.keyword_group)
        
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Nhập từ khóa tìm kiếm...")
        self.keyword_input.setFont(QFont("Arial", 12))
        self.keyword_input.setMinimumHeight(40)
        self.keyword_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        keyword_layout.addWidget(self.keyword_input)
        main_layout.addWidget(self.keyword_group)
        
        # Ẩn keyword group ban đầu
        self.keyword_group.setVisible(False)
        
        # Group chọn nơi lưu
        save_group = QGroupBox("Chọn nơi lưu file CSV")
        save_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        save_layout = QHBoxLayout(save_group)
        
        self.save_path_label = QLabel("Chưa chọn thư mục")
        self.save_path_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.save_path_label.setMinimumHeight(40)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setFont(QFont("Arial", 10))
        self.browse_btn.setMinimumHeight(40)
        self.browse_btn.clicked.connect(self.browse_save_location)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        save_layout.addWidget(self.save_path_label, 1)
        save_layout.addWidget(self.browse_btn)
        main_layout.addWidget(save_group)
        
        # Button crawl
        self.crawl_btn = QPushButton("Bắt đầu Crawl")
        self.crawl_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.crawl_btn.setMinimumHeight(50)
        self.crawl_btn.setEnabled(False)
        self.crawl_btn.clicked.connect(self.start_crawl)
        self.crawl_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        main_layout.addWidget(self.crawl_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 6px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Log area
        log_group = QGroupBox("Log hoạt động")
        log_group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #2c3e50;
            }
        """)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)
        
        # Status bar
        self.statusBar().showMessage("Sẵn sàng")
        
    def select_crawl_type(self, crawl_type):
        """Chọn loại crawl (TikTok, YouTube, AliExpress, Instagram, Temu)"""
        self.current_crawl_type = crawl_type
        
        # Reset style cho tất cả button
        self.tiktok_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0050;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e6004c;
            }
        """)
        
        self.youtube_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff0000;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e60000;
            }
        """)
        
        self.aliexpress_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6600;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e65c00;
            }
        """)
        
        self.instagram_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f09433, stop:1 #e6683c, stop:2 #dc2743, stop:3 #cc2366, stop:4 #bc1888);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e0852a, stop:1 #d55f33, stop:2 #cb1e3a, stop:3 #bb1a5d, stop:4 #ab177f);
            }
        """)
        
        self.temu_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b35;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e65a2a;
            }
        """)
        
        # Highlight button được chọn và xử lý logic
        if crawl_type == "tiktok":
            self.tiktok_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e6004c;
                    color: white;
                    border: 3px solid #ff0050;
                    border-radius: 10px;
                    font-weight: bold;
                }
            """)
            self.mode_label.setText("🎯 Chế độ crawl: TikTok")
            self.mode_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    background-color: #ff0050;
                    border: 2px solid #ff0050;
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                    font-style: normal;
                }
            """)
            self.log_text.append(f"🎯 Đã chọn chế độ: TikTok Crawler")
            self.statusBar().showMessage("Chế độ TikTok - Sẵn sàng nhập keyword")
            self.keyword_group.setVisible(True)  # Hiển thị keyword group
            
        elif crawl_type == "youtube":
            self.youtube_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e60000;
                    color: white;
                    border: 3px solid #ff0000;
                    border-radius: 10px;
                    font-weight: bold;
                }
            """)
            self.mode_label.setText("🎯 Chế độ crawl: YouTube")
            self.mode_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    background-color: #ff0000;
                    border: 2px solid #ff0000;
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                    font-style: normal;
                }
            """)
            self.log_text.append(f"🎯 Đã chọn chế độ: YouTube Crawler")
            self.statusBar().showMessage("Chế độ YouTube - Sẵn sàng nhập keyword")
            self.keyword_group.setVisible(True)  # Hiển thị keyword group
            
        elif crawl_type == "temu":
            self.temu_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e65a2a;
                    color: white;
                    border: 3px solid #ff6b35;
                    border-radius: 10px;
                    font-weight: bold;
                }
            """)
            self.mode_label.setText("🎯 Chế độ crawl: Temu")
            self.mode_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    background-color: #ff6b35;
                    border: 2px solid #ff6b35;
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                    font-style: normal;
                }
            """)
            self.log_text.append(f"🎯 Đã chọn chế độ: Temu Crawler")
            self.statusBar().showMessage("Chế độ Temu - Không cần keyword")
            self.keyword_group.setVisible(False)  # Ẩn keyword group
            
        elif crawl_type == "aliexpress":
            self.aliexpress_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e65c00;
                    color: white;
                    border: 3px solid #ff6600;
                    border-radius: 10px;
                    font-weight: bold;
                }
            """)
            self.mode_label.setText("🎯 Chế độ crawl: AliExpress")
            self.mode_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    background-color: #ff6600;
                    border: 2px solid #ff6600;
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                    font-style: normal;
                }
            """)
            self.log_text.append(f"🎯 Đã chọn chế độ: AliExpress Crawler")
            self.statusBar().showMessage("Chế độ AliExpress - Không cần keyword")
            self.keyword_group.setVisible(False)  # Ẩn keyword group
            
        elif crawl_type == "instagram":
            self.instagram_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #d55f33, stop:1 #cb1e3a, stop:2 #bb1a5d, stop:3 #ab177f);
                    color: white;
                    border: 3px solid #e0852a;
                    border-radius: 10px;
                    font-weight: bold;
                }
            """)
            self.mode_label.setText("🎯 Chế độ crawl: Instagram")
            self.mode_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #d55f33, stop:1 #cb1e3a, stop:2 #bb1a5d, stop:3 #ab177f);
                    border: 2px solid #d55f33;
                    border-radius: 8px;
                    padding: 8px;
                    font-weight: bold;
                    font-style: normal;
                }
            """)
            self.log_text.append(f"🎯 Đã chọn chế độ: Instagram Crawler")
            self.statusBar().showMessage("Chế độ Instagram - Sẵn sàng nhập keyword")
            self.keyword_group.setVisible(True)  # Hiển thị keyword group
        
        # Kiểm tra trạng thái sẵn sàng
        self.check_ready_state()
        
    def browse_save_location(self):
        """Chọn nơi lưu file CSV"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file CSV")
        if folder:
            self.save_path = folder
            self.save_path_label.setText(folder)
            self.save_path_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.log_text.append(f"Đã chọn thư mục lưu: {folder}")
            self.check_ready_state()
            
    def check_ready_state(self):
        """Kiểm tra xem có thể bắt đầu crawl không"""
        # AliExpress và Temu không cần keyword
        if self.current_crawl_type in ["aliexpress", "temu"]:
            can_start = (bool(self.current_crawl_type) and bool(self.save_path))
        else:
            # TikTok, YouTube, Instagram cần keyword
            can_start = (bool(self.current_crawl_type) and 
                        bool(self.keyword_input.text().strip()) and 
                        bool(self.save_path))
        
        self.crawl_btn.setEnabled(can_start)
        
        if can_start:
            self.statusBar().showMessage("Sẵn sàng crawl")
        else:
            if self.current_crawl_type in ["aliexpress", "temu"]:
                self.statusBar().showMessage("Vui lòng chọn nơi lưu file")
            else:
                self.statusBar().showMessage("Vui lòng hoàn thành tất cả bước")
            
    def start_crawl(self):
        """Bắt đầu crawl"""
        # Kiểm tra keyword chỉ cho TikTok, YouTube, Instagram
        if self.current_crawl_type in ["tiktok", "youtube", "instagram"]:
            keyword = self.keyword_input.text().strip()
            if not keyword:
                QMessageBox.warning(self, "Lỗi", "Vui lòng nhập keyword!")
                return
            
        if not self.save_path:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn nơi lưu file!")
            return
            
        if not self.current_crawl_type:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn loại crawl!")
            return
            
        # Disable UI
        self.crawl_btn.setEnabled(False)
        self.tiktok_btn.setEnabled(False)
        self.youtube_btn.setEnabled(False)
        self.aliexpress_btn.setEnabled(False)
        self.instagram_btn.setEnabled(False)
        self.temu_btn.setEnabled(False)
        self.keyword_input.setEnabled(False)
        self.browse_btn.setEnabled(False)
        
        # Hiển thị progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Log
        crawl_type_name = self.current_crawl_type.upper()
        self.log_text.append(f"\n=== Bắt đầu crawl {crawl_type_name} ===")
        self.log_text.append(f"Chế độ: {crawl_type_name}")
        if self.current_crawl_type in ["tiktok", "youtube", "instagram"]:
            self.log_text.append(f"Keyword: {self.keyword_input.text().strip()}")
        else:
            self.log_text.append("Không cần keyword")
        self.log_text.append(f"Nơi lưu: {self.save_path}")
        self.log_text.append("Đang xử lý...")
        
        # Tạo và chạy thread crawl
        keyword = self.keyword_input.text().strip() if self.current_crawl_type in ["tiktok", "youtube", "instagram"] else ""
        self.crawl_thread = CrawlThread(self.current_crawl_type, keyword, self.save_path)
        self.crawl_thread.progress_signal.connect(self.update_progress)
        self.crawl_thread.finished_signal.connect(self.crawl_finished)
        self.crawl_thread.start()
        
    def update_progress(self, message):
        """Cập nhật progress và log"""
        self.log_text.append(message)
        self.statusBar().showMessage(message)
        
    def crawl_finished(self, success, message):
        """Xử lý khi crawl hoàn thành"""
        # Ẩn progress
        self.progress_bar.setVisible(False)
        
        # Log kết quả
        if success:
            self.log_text.append(f"✅ {message}")
            QMessageBox.information(self, "Thành công", message)
        else:
            self.log_text.append(f"❌ {message}")
            QMessageBox.critical(self, "Lỗi", message)
            
        # Re-enable UI
        self.crawl_btn.setEnabled(True)
        self.tiktok_btn.setEnabled(True)
        self.youtube_btn.setEnabled(True)
        self.aliexpress_btn.setEnabled(True)
        self.instagram_btn.setEnabled(True)
        self.temu_btn.setEnabled(True)
        self.keyword_input.setEnabled(True)
        self.browse_btn.setEnabled(True)
        
        # Kiểm tra trạng thái sẵn sàng
        self.check_ready_state()
        
        # Status
        if success:
            self.statusBar().showMessage("Crawl hoàn thành thành công!")
        else:
            self.statusBar().showMessage("Crawl thất bại")


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
