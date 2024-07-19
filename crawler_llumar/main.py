from PyQt5 import QtCore, QtWidgets
import subprocess
import threading
import time
import os
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QMessageBox

class UiDialog(QtWidgets.QWidget):
    def setup_ui(self, dialog):
        dialog.setObjectName("Dialog")
        
        main_layout = QVBoxLayout(dialog)

        # 제목 레이블 설정
        self.title_label = QtWidgets.QLabel("Web Crawler")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        #라디오 버튼
        radio_group = QGroupBox()
        radio_layout = QVBoxLayout()
        self.radio_button_new = QtWidgets.QRadioButton("What's New")
        self.radio_button_faq = QtWidgets.QRadioButton("FAQ")
        self.radio_button_promotion = QtWidgets.QRadioButton("홍보자료")
        
        radio_layout.addWidget(self.radio_button_new)
        radio_layout.addWidget(self.radio_button_faq)
        radio_layout.addWidget(self.radio_button_promotion)
        radio_group.setLayout(radio_layout)
        main_layout.addWidget(radio_group)

        #이벤트 버튼
        button_layout = QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("실행")
        self.pause_button = QtWidgets.QPushButton("일시정지")
        self.stop_button = QtWidgets.QPushButton("중단")
        
        self.start_button.setStyleSheet("background-color: #00ff00;")
        self.pause_button.setStyleSheet("background-color: #ffc0cb;")
        self.stop_button.setStyleSheet("background-color: #ff0000;")
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)

        #이벤트 연결
        self.start_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause)
        self.stop_button.clicked.connect(self.stop)

        # 라디오 버튼을 이벤트 연결
        self.radio_button_new.toggled.connect(lambda: self.radio_button(self.radio_button_new))
        self.radio_button_promotion.toggled.connect(lambda: self.radio_button(self.radio_button_promotion))
        self.radio_button_faq.toggled.connect(lambda: self.radio_button(self.radio_button_faq))

        # 상태 변수 초기화
        self.process = None
        self.blinking = False
        self.pause_button.setEnabled(False)
        self.current_script = None
        self.paused_state_file = "paused_state.txt"
        self.completed_pages = []
        self.is_paused = False
        self.is_stopped = False
        self.start_time = None

    def start(self):
        if self.process:
            self.process.terminate()
            self.process = None

        if self.radio_button_new.isChecked():
            self.current_script = "whatsnew"
            script_path = "whatsnew/whatsnew.py"
            state_file = "whatsnew_state.txt"
        elif self.radio_button_promotion.isChecked():
            self.current_script = "promotion"
            script_path = "promotion/promotion.py"
            state_file = "promotion_state.txt"
        elif self.radio_button_faq.isChecked():
            self.current_script = "faq"
            script_path = "faq/faq.py"
            state_file = "faq_state.txt"
        else:
            print("버튼은 클릭되었으나 실행되지 않음")
            return

        if os.path.exists(self.paused_state_file):
            with open(self.paused_state_file, 'r') as file:
                pages = file.read().strip().split(',')
                self.completed_pages = pages
                last_page = pages[-1]
            self.process = subprocess.Popen(["python", script_path, last_page])
        else:
            self.process = subprocess.Popen(["python", script_path])

        print(f"Executing {self.current_script}.py...")

        self.start_time = time.time()
        self.blinking = True
        threading.Thread(target=self.blink_button).start()
        threading.Thread(target=self.completion, args=(state_file,)).start()
        self.pause_button.setEnabled(True)
        self.radio_button_new.setEnabled(False)
        self.radio_button_promotion.setEnabled(False)
        self.radio_button_faq.setEnabled(False)

    def radio_button(self, button):
        if button.isChecked():
            print(f"{button.text()} 선택됨")

    def blink_button(self):
        while self.blinking:
            self.start_button.setStyleSheet("background-color: #00ff00;")
            time.sleep(0.5)
            self.start_button.setStyleSheet("background-color: #00aa00;")
            time.sleep(0.5)

    def completion(self, state_file):
        self.process.wait()
        self.blinking = False
        self.start_button.setStyleSheet("background-color: #00ff00;")
        if os.path.exists(state_file):
            os.remove(state_file)
        print(f"{self.current_script}.py execution completed.")
        if not self.is_paused and not self.is_stopped: 
            QtCore.QTimer.singleShot(0, self.completion_message)
        self.is_paused = False

    def pause(self):
        if self.process:
            self.process.terminate()
            self.process = None
            with open(self.paused_state_file, 'w') as file:
                file.write(','.join(self.completed_pages))
            self.pause_button.setEnabled(False)
            self.radio_button_new.setEnabled(True)
            self.radio_button_promotion.setEnabled(True)
            self.radio_button_faq.setEnabled(True)
            self.blinking = False
            self.start_button.setStyleSheet("background-color: #00ff00;")
            self.is_paused = True

    def current_page(self, page_number):
        if page_number not in self.completed_pages:
            self.completed_pages.append(page_number)
        self.save_completed_pages()

    def save_completed_pages(self):
        with open(self.paused_state_file, 'w') as file:
            file.write(','.join(self.completed_pages))

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None
            state_file = f"{self.current_script}_state.txt"
        if os.path.exists(state_file):
            os.remove(state_file)
        self.pause_button.setEnabled(False)
        self.radio_button_new.setEnabled(True)
        self.radio_button_promotion.setEnabled(True)
        self.radio_button_faq.setEnabled(True)
        self.blinking = False
        self.start_button.setStyleSheet("background-color: #00ff00;")
        self.is_paused = False
        print(state_file)
        

    def completion_message(self):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("Process Completed")
        msg_box.setText(f"모든 작업 완료. 소요 시간: {elapsed_time:.3f} 초")
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()
        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()
    ui = UiDialog()
    ui.setup_ui(dialog)
    dialog.show()
    sys.exit(app.exec_())
