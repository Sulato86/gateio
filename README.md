# trading-crypto
 untuk trading crypto dengan HTTP API

### Struktur
crypto-trading-app/
│
├── controller/
│   ├── csv_handler.py
│   ├── pandasa.py
│   └── workers.py
│
├── api/
│   └── api_gateio.py
│
├── ui/
│   └── ui_main_window.py
│
├── .env
├── main.py
├── requirements.txt
└── README.md



======================Designer=================
pyuic5 -o ui/ui_main_window.py ui/main_window.ui
pyuic5 -o server/server_control.py server/server_control.ui
===============================================
=================INSTALL=======================
pyinstaller --onedir --windowed --clean main_window.py
===============================================
==================FLOWCHART====================
pyreverse -o plantuml -p full -A .
