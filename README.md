
======================Designer=================
pyuic5 -o ui/ui_main_window.py ui/main_window.ui
pyuic5 -o server/server_control.py server/server_control.ui
===============================================
=================INSTALL=======================
pyinstaller --onedir --windowed --clean main_window.py
===============================================
==================FLOWCHART====================
pyreverse -o plantuml -p full -A .
