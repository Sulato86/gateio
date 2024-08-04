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
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(10, 480, 211, 211))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_accountdata = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.label_accountdata.setFont(font)
        self.label_accountdata.setAlignment(QtCore.Qt.AlignCenter)
        self.label_accountdata.setObjectName("label_accountdata")
        self.verticalLayout_2.addWidget(self.label_accountdata)
        self.tableView_accountdata = QtWidgets.QTableView(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableView_accountdata.sizePolicy().hasHeightForWidth())
        self.tableView_accountdata.setSizePolicy(sizePolicy)
        self.tableView_accountdata.setObjectName("tableView_accountdata")
        self.verticalLayout_2.addWidget(self.tableView_accountdata)
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
        self.label_accountdata.setText(_translate("MainWindow", "Account Data"))
        self.menuMenu.setTitle(_translate("MainWindow", "Menu"))
        self.actionImpor_API.setText(_translate("MainWindow", "Impor API"))
