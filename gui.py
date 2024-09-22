import sys
import os
import pyperclip
import re
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QCheckBox, 
                             QTextEdit, QFileDialog, QStackedWidget, QListWidget, QListWidgetItem)
from PyQt5.QtGui import QPalette, QColor, QPainter, QBrush
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect, QTimer

from main import process_video
from download import download_playlist
from sponser import get_sponsor_segments  # Add this import

class CheckeredClickableArea(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setText("Click here to paste YouTube link")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)

        # Draw checkered pattern
        square_size = 20
        for i in range(0, self.width(), square_size):
            for j in range(0, self.height(), square_size):
                if (i // square_size + j // square_size) % 2 == 0:
                    painter.setBrush(QBrush(QColor(60, 60, 60)))
                else:
                    painter.setBrush(QBrush(QColor(80, 80, 80)))
                painter.drawRect(i, j, square_size, square_size)

        # Draw text
        painter.setPen(Qt.white)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)

    def setText(self, text):
        self.text = text
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class TextSpinner(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.spinner_chars = ['|', '/', '-', '\\']
        self.current_char = 0
        self.percentage = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_spinner)
        self.timer.start(100)  # Update every 100ms

    def update_spinner(self):
        self.setText(f"{self.spinner_chars[self.current_char]} {self.percentage}")
        self.current_char = (self.current_char + 1) % len(self.spinner_chars)

    def set_percentage(self, percentage):
        self.percentage = percentage
        self.update_spinner()

class DownloadThread(QThread):
    update_progress = pyqtSignal(str, float)  # url, percentage
    finished = pyqtSignal(str, str)  # url, result

    def __init__(self, url, output_path, format, use_sponsorblock, is_playlist=False, segment_types=None):
        QThread.__init__(self)
        self.url = url
        self.output_path = output_path
        self.format = format
        self.use_sponsorblock = use_sponsorblock
        self.is_playlist = is_playlist
        self.segment_types = segment_types or []

    def run(self):
        if self.is_playlist:
            try:
                results = download_playlist(self.url, self.output_path, self.format, self.progress_callback)
                successful_downloads = 0
                for result in results:
                    try:
                        process_video(result, self.output_path, self.format, self.use_sponsorblock, self.segment_types, self.progress_callback)
                        successful_downloads += 1
                    except Exception as e:
                        self.update_progress.emit(self.url, -1)
                self.finished.emit(self.url, f"Playlist download completed: {successful_downloads}/{len(results)} videos")
            except Exception as e:
                self.update_progress.emit(self.url, -1)
                self.finished.emit(self.url, "Failed")
        else:
            try:
                result = process_video(self.url, self.output_path, self.format, self.use_sponsorblock, self.segment_types, self.progress_callback)
                self.finished.emit(self.url, result)
            except Exception as e:
                self.update_progress.emit(self.url, -1)
                self.finished.emit(self.url, "Failed")

    def progress_callback(self, message):
        if "Downloading:" in message:
            try:
                percentage_match = re.search(r'\[0;94m\s*(\d+\.\d+)%\[0m', message)
                if percentage_match:
                    percentage = float(percentage_match.group(1))
                    self.update_progress.emit(self.url, percentage)
            except ValueError:
                pass

class YouTubeDownloaderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.config_file = 'config.json'
        self.load_config()
        self.initUI()
        self.download_threads = []
        self.active_downloads = set()
        self.active_playlist_ids = set()
        self.active_video_ids = set()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'mp3_output': os.path.join(os.path.expanduser("~"), "Downloads", "YouTube_MP3"),
                'mp4_output': os.path.join(os.path.expanduser("~"), "Downloads", "YouTube_MP4")
            }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def initUI(self):
        self.setWindowTitle('YouTube Downloader')
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")

        layout = QVBoxLayout()

        # URL input area
        self.url_input = CheckeredClickableArea()
        self.url_input.clicked.connect(self.paste_url)
        layout.addWidget(self.url_input)

        # Output paths
        mp3_layout = QHBoxLayout()
        mp3_layout.addWidget(QLabel("MP3 Output:"))
        self.mp3_output = QLineEdit(self.config['mp3_output'])
        self.mp3_output.setStyleSheet("background-color: #3b3b3b; border: 1px solid #555555; padding: 5px;")
        self.mp3_output.textChanged.connect(self.on_mp3_output_changed)
        mp3_layout.addWidget(self.mp3_output)
        mp3_browse = QPushButton("Browse")
        mp3_browse.clicked.connect(lambda: self.browse_folder(self.mp3_output))
        mp3_browse.setStyleSheet("background-color: #4b4b4b;")
        mp3_layout.addWidget(mp3_browse)
        layout.addLayout(mp3_layout)

        mp4_layout = QHBoxLayout()
        mp4_layout.addWidget(QLabel("MP4 Output:"))
        self.mp4_output = QLineEdit(self.config['mp4_output'])
        self.mp4_output.setStyleSheet("background-color: #3b3b3b; border: 1px solid #555555; padding: 5px;")
        self.mp4_output.textChanged.connect(self.on_mp4_output_changed)
        mp4_layout.addWidget(self.mp4_output)
        mp4_browse = QPushButton("Browse")
        mp4_browse.clicked.connect(lambda: self.browse_folder(self.mp4_output))
        mp4_browse.setStyleSheet("background-color: #4b4b4b;")
        mp4_layout.addWidget(mp4_browse)
        layout.addLayout(mp4_layout)

        # Format and SponsorBlock checkboxes
        checkbox_layout = QHBoxLayout()
        self.mp3_check = QCheckBox("MP3")
        self.mp3_check.setChecked(True)
        self.mp4_check = QCheckBox("MP4")
        self.sponsorblock_check = QCheckBox("Use SponsorBlock")
        self.sponsorblock_check.setChecked(True)
        checkbox_layout.addWidget(self.mp3_check)
        checkbox_layout.addWidget(self.mp4_check)
        checkbox_layout.addWidget(self.sponsorblock_check)
        layout.addLayout(checkbox_layout)

        # Connect checkbox signals
        self.mp3_check.stateChanged.connect(self.on_format_changed)
        self.mp4_check.stateChanged.connect(self.on_format_changed)
        self.sponsorblock_check.stateChanged.connect(self.on_sponsorblock_changed)

        # Segment types checkboxes
        self.segment_types = ['sponsor', 'selfpromo', 'interaction', 'intro', 'outro', 'preview', 'music_offtopic', 'filler']
        self.segment_checkboxes = {}
        self.segment_layout = QHBoxLayout()
        for segment_type in self.segment_types:
            checkbox = QCheckBox(segment_type.capitalize())
            checkbox.setChecked(True)  # Set all checkboxes to checked by default
            self.segment_checkboxes[segment_type] = checkbox
            self.segment_layout.addWidget(checkbox)
        layout.addLayout(self.segment_layout)

        # Initially show/hide segment checkboxes based on SponsorBlock checkbox
        self.on_sponsorblock_changed(self.sponsorblock_check.checkState())

        # Console toggle button
        self.console_button = QPushButton("Show Console")
        self.console_button.clicked.connect(self.toggle_console)
        self.console_button.setStyleSheet("background-color: #4b4b4b;")
        layout.addWidget(self.console_button)

        # Stacked widget for console output and download list
        self.stacked_widget = QStackedWidget()
        
        # Download list
        self.download_list = QListWidget()
        self.download_list.setStyleSheet("background-color: #3b3b3b; border: 1px solid #555555;")
        self.stacked_widget.addWidget(self.download_list)

        # Console output
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setStyleSheet("background-color: #3b3b3b; border: 1px solid #555555;")
        self.stacked_widget.addWidget(self.progress_text)

        layout.addWidget(self.stacked_widget)

        self.setLayout(layout)

        # Set default view to download list
        self.stacked_widget.setCurrentIndex(0)

    def toggle_console(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index == 0:
            self.stacked_widget.setCurrentIndex(1)
            self.console_button.setText("Collapse Console")
        else:
            self.stacked_widget.setCurrentIndex(0)
            self.console_button.setText("Show Console")

    def paste_url(self):
        url = pyperclip.paste()
        self.start_download(url)

    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            line_edit.setText(folder)

    def on_mp3_output_changed(self):
        self.config['mp3_output'] = self.mp3_output.text()
        self.save_config()

    def on_mp4_output_changed(self):
        self.config['mp4_output'] = self.mp4_output.text()
        self.save_config()

    def start_download(self, url):
        if not url:
            self.progress_text.append("Please paste a YouTube URL.")
            return

        is_playlist, playlist_id = self.is_playlist_url(url)
        video_id = self.extract_video_id(url)
        
        if is_playlist:
            if playlist_id in self.active_playlist_ids:
                self.progress_text.append(f"Already downloading playlist: {playlist_id}")
                return
            self.active_playlist_ids.add(playlist_id)
        elif video_id:
            if video_id in self.active_video_ids:
                self.progress_text.append(f"Already downloading video: {video_id}")
                return
            self.active_video_ids.add(video_id)
        else:
            self.progress_text.append("Invalid YouTube URL.")
            return

        format = "mp3" if self.mp3_check.isChecked() else "mp4"
        output_path = self.mp3_output.text() if format == "mp3" else self.mp4_output.text()

        use_sponsorblock = self.sponsorblock_check.isChecked()
        selected_segment_types = [segment_type for segment_type, checkbox in self.segment_checkboxes.items() if checkbox.isChecked()]

        thread = DownloadThread(url, output_path, format, use_sponsorblock, is_playlist, selected_segment_types)
        thread.update_progress.connect(self.update_progress)
        thread.finished.connect(lambda result, u=url, pid=playlist_id, vid=video_id: 
                                self.download_finished(result, u, pid, vid))
        thread.start()

        self.download_threads.append(thread)
        self.active_downloads.add(url)
        self.progress_text.append(f"Starting {'playlist' if is_playlist else 'video'} download: {url} ({format})")

        # Add item to download list with text spinner
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.addWidget(QLabel(f"{'Playlist' if is_playlist else 'Video'} {format.upper()} - {url}"))
        spinner = TextSpinner()
        item_layout.addWidget(spinner)
        item_widget.setLayout(item_layout)

        list_item = QListWidgetItem(self.download_list)
        list_item.setSizeHint(item_widget.sizeHint())
        self.download_list.addItem(list_item)
        self.download_list.setItemWidget(list_item, item_widget)

        # Store the spinner in a dictionary for easy access
        if not hasattr(self, 'spinners'):
            self.spinners = {}
        self.spinners[url] = spinner

    def is_playlist_url(self, url):
        playlist_patterns = [
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/playlist\?list=([^&]+)',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=[^&]+&list=([^&]+)',
            r'(?:https?:\/\/)?youtu\.be\/[^?]+\?list=([^&]+)'
        ]
        for pattern in playlist_patterns:
            match = re.match(pattern, url)
            if match:
                return True, match.group(1)
        return False, None

    def extract_video_id(self, url):
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/|v\/|youtu.be\/)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def update_progress(self, url, percentage):
        if url in self.spinners:
            spinner = self.spinners[url]
            if percentage != -1:
                spinner.set_percentage(f"{percentage:.1f}%")
            else:
                spinner.set_percentage("Error")

    def download_finished(self, url, result, playlist_id=None, video_id=None):
        self.progress_text.append(f"Download completed: {result}")
        self.progress_text.verticalScrollBar().setValue(self.progress_text.verticalScrollBar().maximum())
        if playlist_id:
            self.active_playlist_ids.discard(playlist_id)
        if video_id:
            self.active_video_ids.discard(video_id)
        self.active_downloads.discard(url)

        # Remove the completed download from the list
        for i in range(self.download_list.count()):
            item = self.download_list.item(i)
            widget = self.download_list.itemWidget(item)
            if widget.layout().itemAt(0).widget().text().endswith(url):
                self.download_list.takeItem(i)
                break

    def on_format_changed(self, state):
        sender = self.sender()
        if state == Qt.Checked:
            if sender == self.mp3_check:
                self.mp4_check.setChecked(False)
            else:
                self.mp3_check.setChecked(False)
        else:
            # Ensure at least one format is always checked
            if sender == self.mp3_check and not self.mp4_check.isChecked():
                self.mp4_check.setChecked(True)
            elif sender == self.mp4_check and not self.mp3_check.isChecked():
                self.mp3_check.setChecked(True)

    def on_sponsorblock_changed(self, state):
        use_sponsorblock = state == Qt.Checked
        for checkbox in self.segment_checkboxes.values():
            checkbox.setVisible(use_sponsorblock)
            checkbox.setChecked(use_sponsorblock)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set up dark palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    ex = YouTubeDownloaderGUI()
    ex.show()
    sys.exit(app.exec_())