#!/usr/bin/python3
# -*- coding: utf-8 -*-
### based on https://github.com/rootVIII/git_clones by James
#########################################################################
from PyQt5.QtCore import (QDir, QSettings, Qt, QMetaObject, QSize, QProcess)
from PyQt5.QtGui import QIcon, QKeySequence, QFont, QCursor
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QMainWindow, QHBoxLayout, QMenu, 
                                                    QMessageBox, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QCheckBox, 
                                                    QTableWidget, QTableWidgetItem, QToolBar, QStatusBar, QMessageBox )
from sys import exit, version_info
from re import findall
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import Request, urlopen
##########################################################################
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setObjectName("myGitClone")
        self.setGeometry(0, 0, 800, 600)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumSize(400, 300)
        self.setDocumentMode(True)
        self.settings = QSettings('Axel Schneider', self.objectName())
        self.createStatusbar()
        self.createActions()
        self.createWidgets()
        QMetaObject.connectSlotsByName(self)
        self.readSettings()
        self.statusbar.showMessage("Ready")
        self.setWindowTitle("myGitClone")

    ### process
        ### shell settings
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
#        self.process.readyRead.connect(self.dataReady)
        self.process.readyReadStandardError.connect(lambda: self.msg("Error"))
        self.process.started.connect(lambda: self.msg("starting shell"))
        self.process.finished.connect(lambda: self.msg("shell ended"))

    ### widgets ###
    def createWidgets(self):
        self.username = ""
        self.url = "https://github.com/%s?tab=repositories" % self.username
        self.repoList = []
        self.gitList = []
        self.dlFolder = QDir.homePath() + "/Downloads"

        ### table ###
        self.lb = QTableWidget()
        self.lb.setColumnCount(2)
        self.lb.setColumnWidth(0, 60)
        self.lb.horizontalHeader().setStretchLastSection(True)
        self.lb.setHorizontalHeaderItem(0, QTableWidgetItem("Select"))
        self.lb.setHorizontalHeaderItem(1, QTableWidgetItem("Repository Name"))
#        self.lb.cellChanged.connect(self.listChanged)

        ### username field ###
        self.uname = QLineEdit("Axel-Erfurt")
        self.uname.setFixedWidth(180)
        self.uname.setPlaceholderText("insert user name")
        self.uname.returnPressed.connect(self.listRepos)

        ### get repos button ###
        self.uBtn = QPushButton("get Repos List")
        self.uBtn.setFixedWidth(120)
        self.uBtn.setToolTip("get all repos from user")
        self.uBtn.clicked.connect(self.listRepos)

        ### get repos button ###
        self.dlBtn = QPushButton("download selected Repos")
        self.dlBtn.setFixedWidth(160)
        self.dlBtn.setToolTip("download selected repos from user")
        self.dlBtn.clicked.connect(self.create_dl_list)

        ### Layout
        self.ubox = QHBoxLayout()
        self.ubox.addWidget(self.uname)
        self.ubox.insertStretch(1)
        self.ubox.addWidget(self.uBtn)
        self.ubox.addStretch()

    
        self.layout = QVBoxLayout()
        self.wid = QWidget()

        self.layout.addLayout(self.ubox)
        self.layout.addWidget(self.lb)
        self.layout.addWidget(self.dlBtn)
        self.wid.setLayout(self.layout)

        self.setCentralWidget(self.wid)
    
    ### actions ###
    def createActions(self):
        self.tbar = QToolBar()
        self.tbar.setIconSize(QSize(16, 16))
        self.tbar.setMovable(False)
        self.tbar.setToolButtonStyle(0)
        self.tbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.tbar.setObjectName("tbar")
        self.addToolBar(self.tbar)

        self.actionSettings = QAction(self, triggered = self.appSettings, toolTip = "set output directory")
        icon = QIcon.fromTheme("preferences-system")
        self.actionSettings.setIcon(icon)
        self.actionSettings.setObjectName("actionSettings")

        self.actionAbout = QAction(self, triggered = self.aboutApp)
        icon = QIcon.fromTheme("help-about")
        self.actionAbout.setIcon(icon)

        self.tbar.addAction(self.actionSettings)
        self.tbar.addAction(self.actionAbout)

        ### statusbar###
    def createStatusbar(self):
        self.statusbar = QStatusBar(self)
        font = QFont()
        font.setPointSize(7)
        self.statusbar.setFont(font)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

    ### get username from textfield
    def changeUsername(self):
        self.username = self.uname.text()
        self.url = "https://github.com/%s?tab=repositories" % self.username

    ### get user repos ##
    def listRepos(self):
        self.changeUsername()
        self.lb.setRowCount(0)
        self.repoList = []
        repositories = self.get_repositories()
        print("%s %s" % ("get repos from", self.username))
        self.repoList = list(repositories)
        self.fillTable()
        self.msg("repos loaded")

    ### fill table with user repos
    def fillTable(self):
        self.lb.setRowCount(len(self.repoList))
        if self.lb.rowCount() > 0:
            for x in range(len(self.repoList)):
                rep = QTableWidgetItem(self.repoList[x])
                checkbox = QCheckBox(self.lb)
                checkbox.setStyleSheet("margin-left:20%; margin-right:10%;")
                checkbox.setCheckState(0)
                self.lb.setCellWidget(x, 0, checkbox)
                self.lb.setItem(x, 1, rep)

    ### table context menu
    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        if self.lb.selectionModel().hasSelection():
            # copy
            downloadAction = QAction(QIcon.fromTheme("download"), 'download Repo', self)
            downloadAction.triggered.connect(lambda: self.downloadRepoFromList())
            ###
            self.menu.addAction(downloadAction)
            self.menu.popup(QCursor.pos())

    def listChanged(self):
        self.create_dl_list()
#        print(self.gitList)

    ### get download list from selected repos
    def create_dl_list(self):
        r =  ""
        self.gitList = []
        for x in range(self.lb.rowCount()):
            if self.lb.cellWidget(x, 0).checkState() == 2:
                r = self.lb.item(x, 1).text()
                self.gitList.append(r)
                print("%s %s" % (r, "is selected"))
                self.downloadRepo(r)

    ### download repo
    def downloadRepo(self, gitrepo):
        merror = ""
        cmd =  "git clone --progress --verbose https://github.com/" + str(self.username) + "/" +  str(gitrepo) + " " + str(self.dlFolder) + "/" +  str(gitrepo)                                                   
        print("%s %s" % ("username is:", self.username))
        print(cmd)
        try:
            self.process.execute(cmd)
        except Exception as e:
            s = str(e)
            self.errorBox(s)

    ### download selected repo (context menu)
    def downloadRepoFromList(self):
        row =  self.lb.selectionModel().selectedIndexes()[0].row()
        gitrepo = self.lb.item(row, 1).text()
        cmd =  "git clone --progress --verbose https://github.com/" + str(self.username) + "/" +  str(gitrepo) + " " + str(self.dlFolder) + "/" +  str(gitrepo) 
        print(cmd)
        self.process.execute(cmd)

    ### preferences
    def appSettings(self):
        if self.dlFolder == "":
            self.dlFolder = QDir.homePath()
        self.msg("settings called")
        path = QFileDialog.getExistingDirectory(self, "select Folder", self.dlFolder)
        if path:
            self.dlFolder = path
            print("%s %s" %("download folder changed to",self.dlFolder ))

    def closeEvent(self, e):
        self.writeSettings()
        e.accept()

    ### read settings from config file
    def readSettings(self):
        print("reading settings")
        if self.settings.contains('geometry'):
            self.setGeometry(self.settings.value('geometry'))
        if self.settings.contains('downloadFolder'):
            self.dlFolder = self.settings.value('downloadFolder')
            self.msg(self.dlFolder)
            print("%s %s" % ("download folder:", self.dlFolder))

    ### write settings to config file
    def writeSettings(self):
        print("writing settings")
        self.settings.setValue('geometry', self.geometry())
        self.settings.setValue('downloadFolder', self.dlFolder)

    ### about window
    def aboutApp(self):
        title = "about myGitClone"
        message = """
                    <span style='color: #3465a4; font-size: 18pt;font-weight: bold;'
                    >myGitClone</strong></span></p>
                    <h3>based on <a title='git_clones' href='https://github.com/rootVIII/git_clones' target='_blank'> git_clones</a> by James</h3>
                    <h4>created by  <a title='Axel Schneider' href='http://goodoldsongs.jimdo.com' target='_blank'>Axel Schneider</a> with PyQt5</h3>
                    <br>
                    <span style='color: #555753; font-size: 9pt;'>©2019 Axel Schneider, James</strong></span></p>
                        """
        self.infobox(title, message)

    ### error messagebox
    def errorBox(self, message):
       QMessageBox.warning(self, "Error", message).show()

    ### messagebox
    def infobox(self,title, message):
        QMessageBox.about(self, title, message).show()       

    ### set statusbar text
    def msg(self, message):
        self.statusbar.showMessage(message)

    ### begin from git_clones ###
    def http_get(self):
        if version_info[0] != 2:
            req = urlopen(self.url)
            return req.read().decode('utf-8')
        req = Request(self.url)
        request = urlopen(req)
        return request.read()
    
    def get_repo_data(self):
        try:
            response = self.http_get()
        except Exception as e:
            s = str(e)
            self.errorBox(s)
            print("Unable to make request to %s's Github page" % self.username)
            exit(1)
        else:
            pattern = r"<a\s?href\W+%s/(.*)\"\s+" % self.username
            for line in findall(pattern, response):
                yield line.split('\"')[0]

    def get_repositories(self):
        return set([repo for repo in self.get_repo_data()])
    ### end from git_clones ###

##############################################
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
