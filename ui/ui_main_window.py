# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/main_window.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1202, 858)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.lineEdit_addpair = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_addpair.setGeometry(QtCore.QRect(140, 720, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.lineEdit_addpair.setFont(font)
        self.lineEdit_addpair.setObjectName("lineEdit_addpair")
        self.pushButton_importmarketdata = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_importmarketdata.setGeometry(QtCore.QRect(140, 760, 121, 41))
        self.pushButton_importmarketdata.setObjectName("pushButton_importmarketdata")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(30, 730, 101, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 1141, 461))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_marketdata = QtWidgets.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.label_marketdata.setFont(font)
        self.label_marketdata.setAlignment(QtCore.Qt.AlignCenter)
        self.label_marketdata.setObjectName("label_marketdata")
        self.verticalLayout.addWidget(self.label_marketdata)
        self.tableView_marketdata = QtWidgets.QTableView(self.verticalLayoutWidget)
        self.tableView_marketdata.setObjectName("tableView_marketdata")
        self.verticalLayout.addWidget(self.tableView_marketdata)
        self.pushButton_exportmarketdata = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_exportmarketdata.setGeometry(QtCore.QRect(10, 760, 121, 41))
        self.pushButton_exportmarketdata.setObjectName("pushButton_exportmarketdata")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(10, 480, 441, 191))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.tabWidget.setFont(font)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_saldo = QtWidgets.QWidget()
        self.tab_saldo.setObjectName("tab_saldo")
        self.tableView_accountdata = QtWidgets.QTableView(self.tab_saldo)
        self.tableView_accountdata.setGeometry(QtCore.QRect(-2, -4, 441, 171))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableView_accountdata.sizePolicy().hasHeightForWidth())
        self.tableView_accountdata.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.tableView_accountdata.setFont(font)
        self.tableView_accountdata.setObjectName("tableView_accountdata")
        self.tabWidget.addTab(self.tab_saldo, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1202, 26))
        self.menubar.setObjectName("menubar")
        self.menuMenu = QtWidgets.QMenu(self.menubar)
        self.menuMenu.setObjectName("menuMenu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionImpor_API = QtWidgets.QAction(MainWindow)
        self.actionImpor_API.setObjectName("actionImpor_API")
        self.menuMenu.addAction(self.actionImpor_API)
        self.menubar.addAction(self.menuMenu.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton_importmarketdata.setText(_translate("MainWindow", "IMPORT CSV"))
        self.label.setText(_translate("MainWindow", "ADD PAIR >"))
        self.label_marketdata.setText(_translate("MainWindow", "Market Data"))
        self.pushButton_exportmarketdata.setText(_translate("MainWindow", "EXPORT CSV"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_saldo), _translate("MainWindow", "Saldo"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Tab 2"))
        self.menuMenu.setTitle(_translate("MainWindow", "Menu"))
        self.actionImpor_API.setText(_translate("MainWindow", "Impor API"))
