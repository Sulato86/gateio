from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from control.worker import Worker

class LoginDialog(QDialog):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.setWindowTitle("Login")

        # Buat widget
        self.api_key_label = QLabel("API Key")
        self.api_key_input = QLineEdit()

        self.api_secret_label = QLabel("API Secret")
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.api_key_label)
        layout.addWidget(self.api_key_input)
        layout.addWidget(self.api_secret_label)
        layout.addWidget(self.api_secret_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def login(self):
        api_key = self.api_key_input.text()
        api_secret = self.api_secret_input.text()
        if self.worker.validate_credentials(api_key, api_secret):
            self.worker.initialize_api(api_key, api_secret)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Invalid API credentials")
