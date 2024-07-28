from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from control.worker import Worker

class LoginDialog(QDialog):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.setWindowTitle("Login")

        # Set ukuran dialog
        self.setMinimumSize(400, 200)

        # Buat font
        font = QFont()
        font.setPointSize(12)  # Mengatur ukuran huruf
        font.setBold(True)     # Mengatur huruf tebal

        # Buat widget
        self.api_key_label = QLabel("API Key")
        self.api_key_input = QLineEdit()
        self.api_secret_label = QLabel("Secret Key")
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)

        # Set font untuk widget
        self.api_key_label.setFont(font)
        self.api_key_input.setFont(font)
        self.api_secret_label.setFont(font)
        self.api_secret_input.setFont(font)
        self.login_button.setFont(font)

        # Set alignment ke center untuk label dan input
        self.api_key_label.setAlignment(Qt.AlignCenter)
        self.api_key_input.setAlignment(Qt.AlignCenter)
        self.api_secret_label.setAlignment(Qt.AlignCenter)
        self.api_secret_input.setAlignment(Qt.AlignCenter)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(self.api_secret_label)
        layout.addWidget(self.api_secret_input)

        # Tambahkan login button ke layout horizontal agar berada di tengah
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def login(self):
        api_key = self.api_key_input.text()
        api_secret = self.api_secret_input.text()
        if self.worker.validate_credentials(api_key, api_secret):
            self.worker.initialize_api(api_key, api_secret)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Invalid API credentials")
