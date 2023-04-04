################################################################################
##
## BY: WANDERSON M.PIMENTA
## PROJECT MADE WITH: Qt Designer and PySide2
## V: 1.0.0
##
## This project can be used freely for all uses, as long as they maintain the
## respective credits only in the Python scripts, any information in the visual
## interface (GUI) can be modified without any implication.
##
## There are limitations on Qt licenses if you want to use your products
## commercially, I recommend reading them on the official website:
## https://doc.qt.io/qtforpython/licenses.html
##
################################################################################

import os
import sys
import platform

import numpy as np
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import (QCoreApplication, QPropertyAnimation, QDate, QDateTime, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, QEvent)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter, QPixmap, QRadialGradient)
from PySide2.QtWidgets import *
import PySide2
# GUI FILE
from app_modules import *

import matplotlib
# 声明使用qt5
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from model.data_process import *
from model.predict import predict_

from ui_main import Ui_MainWindow
from ui_analyze import Ui_Form

dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
QtCore.QCoreApplication.addLibraryPath(os.path.join(os.path.dirname(QtCore.__file__), "plugins"))

# matplotlib图形绘制类，继承FigureCanvas，既是一个QWidget，又是一个matplotlib的FigureCanvas
class MyFigure(FigureCanvas):
    def __init__(self, width, height, dpi):
        # 创建一个Figure，该figure为matplotlib之下，而非matplotlib.pyplot之下
        self.fig = plt.figure(figsize=(width, height), dpi=dpi, facecolor= '#2c313c')
        # 在父类中激活Figure窗口，此句必不可少，否则不能显示图形 but why？
        super(MyFigure, self).__init__(self.fig)
        # 调用Figure下面的add_subplot方法，类似于matplotlib.pyplot下面的subplot(1,1,1)方法
        # ax = plt.gca()
        # ax.axes.xaxis.set_visible(False)
        # ax.axes.yaxis.set_visible(False)

    def plot_flash(self, support, query):
        self.fig.clf()

        self.axe_support = self.fig.add_subplot(1, 2, 1)
        self.axe_query = self.fig.add_subplot(1, 2, 2)
        self.axe_query.tick_params(axis='x', color='white')
        # self.axe_support.cla()
        # self.axe_query.cla()
        # t = np.arange(0.0, 5.0, 0.01)
        # s = np.cos(2 * np.random.randn() * t)
        # self.axe_support.plot(t, s, 'o-r', linewidth='0.5')
        # self.axe_query.plot(s, t, 'o-r')
        self.axe_support.tick_params(colors='lightsteelblue', which='both')
        self.axe_query.tick_params(colors='lightsteelblue', which='both')
        self.axe_support.imshow(support.permute(1, 2, 0).numpy().astype(np.uint8))
        self.axe_query.imshow(query.permute(1, 2, 0).numpy().astype(np.uint8))

        self.axe_support.set_title("support set", color='lightsteelblue')
        self.axe_query.set_title("query set", color='lightsteelblue')

        print('sono masaka')
        # self.axe_support.draw()
        # self.axe_query.draw()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


class MyFigureAnalyze(FigureCanvas):
    def __init__(self, width, height, dpi):
        # 创建一个Figure，该figure为matplotlib之下，而非matplotlib.pyplot之下
        self.fig = plt.figure(figsize=(width, height), dpi=dpi, facecolor='#2c313c')
        # 在父类中激活Figure窗口，此句必不可少，否则不能显示图形 but why？
        super(MyFigureAnalyze, self).__init__(self.fig)
        # 调用Figure下面的add_subplot方法，类似于matplotlib.pyplot下面的subplot(1,1,1)方法

    def plot_analyze(self, acc, name):
        self.axes = self.fig.add_subplot(1, 1, 1)
        # colors = ["red", "yellow", 'blue', 'black', 'purple']
        sname = []
        if(dataset == 'omniglot/'):
            for string in name:
                if (len(string) >= 9):
                    sname.append(string[:9])
                else:
                    sname.append(string)
            sname = np.array(sname, dtype='U15')
        else:
            sname = name

        print(sname)
        self.axes.bar(sname, acc, width = 0.4, color='lightsteelblue')
        self.axes.set_xlabel('names of different classes')
        self.axes.set_ylabel('accuracy')
        self.axes.tick_params(color='white', labelcolor='white', which='both')
        self.axes.xaxis.label.set_color('lightsteelblue')
        self.axes.yaxis.label.set_color('lightsteelblue')
        # plt.xlabel('各class名称')
        # plt.ylabel('各class准确率')
        self.fig.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.gridLayout_set = QGridLayout(self.ui.setsGroupBox)

        ## PRINT ==> SYSTEM
        print('System: ' + platform.system())
        print('Version: ' +platform.release())

        ########################################################################
        ## START - WINDOW ATTRIBUTES
        ########################################################################

        ## REMOVE ==> STANDARD TITLE BAR
        UIFunctions.removeTitleBar(True)
        ## ==> END ##

        ## SET ==> WINDOW TITLE
        self.setWindowTitle('Few-shot Learning Classifier')
        UIFunctions.labelTitle(self, 'Few-shot Learning Classifier')
        UIFunctions.labelDescription(self, 'Based on Metric-Learning')
        ## ==> END ##

        ## WINDOW SIZE ==> DEFAULT SIZE
        startSize = QSize(1550, 1200)
        self.resize(startSize)
        self.setMinimumSize(startSize)
        # UIFunctions.enableMaximumSize(self, 500, 720)
        ## ==> END ##

        ## ==> CREATE MENUS
        ########################################################################

        ## ==> TOGGLE MENU SIZE
        self.ui.btn_toggle_menu.clicked.connect(lambda: UIFunctions.toggleMenu(self, 220, True))
        ## ==> END ##

        ## ==> ADD CUSTOM MENUS
        self.ui.stackedWidget.setMinimumWidth(20)
        # UIFunctions.addNewMenu(self, "Main", "btn_home", "url(:/16x16/icons/16x16/cil-home.png)", True)
        UIFunctions.addNewMenu(self, "HOME", "btn_home", "url(:/16x16/icons/16x16/cil-home.png)", True)
        UIFunctions.addNewMenu(self, "Add User", "btn_new_user", "url(:/16x16/icons/16x16/cil-user-follow.png)", True)
        UIFunctions.addNewMenu(self, "Custom Widgets", "btn_widgets", "url(:/16x16/icons/16x16/cil-equalizer.png)", False)
        ## ==> END ##

        # START MENU => SELECTION
        UIFunctions.selectStandardMenu(self, "btn_home")

        ## ==> END ##

        ## ==> START PAGE
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_main)
        ## ==> END ##

        ## USER ICON ==> SHOW HIDE
        UIFunctions.userIcon(self, "WM", "", True)
        ## ==> END ##


        ## ==> MOVE WINDOW / MAXIMIZE / RESTORE
        ########################################################################
        def moveWindow(event):
            # IF MAXIMIZED CHANGE TO NORMAL
            if UIFunctions.returStatus() == 1:
                UIFunctions.maximize_restore(self)

            # MOVE WINDOW
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.globalPos() - self.dragPos)
                self.dragPos = event.globalPos()
                event.accept()

        # WIDGET TO MOVE
        self.ui.frame_label_top_btns.mouseMoveEvent = moveWindow
        ## ==> END ##

        ## ==> LOAD DEFINITIONS
        ########################################################################
        UIFunctions.uiDefinitions(self)
        ## ==> QTableWidget RARAMETERS
        ########################################################################
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        ## ==> END ##

        ## SHOW ==> MAIN WINDOW
        ########################################################################
        self.show()
        ## ==> END ##


        self.ui.sampleButton.clicked.connect(self.randomSample)
        self.ui.runButton.clicked.connect(self.run)
        self.ui.analyzeButton.clicked.connect(self.analyzeOutcome)
        # self.ui.testButton.clicked.connect(self.test)

        self.ui.datasetComboBox.currentIndexChanged.connect(self.datasetChange)
        self.ui.modelComboBox.currentIndexChanged.connect(self.modelChange)


    def randomSample(self):
        global sample
        global dataset

        global n_way
        global n_support
        global n_query

        trainx, trainy, testx, testy = select_dataset(dataset)
        sample = extract_sample(n_way, n_support, n_query, testx, testy)
        print("sample extracted")
        support, query = display_support_query(sample)
        count = self.ui.gridLayout_set.count()

        print(count)
        if count:
            item = self.ui.gridLayout_set.itemAt(count - 1)
            widget = item.widget()
            self.ui.gridLayout_set.removeWidget(widget)
            print("delete seikou")
            widget.deleteLater()
            while self.ui.gridLayout_set.count():
                item = self.ui.gridLayout_set.takeAt(0)
                widget = item.widget()
                widget.deleteLater()

        self.ui.F = MyFigure(width=3, height=2, dpi=100)
        self.ui.F.plot_flash(support, query)
        self.ui.gridLayout_set.addWidget(self.ui.F)
        None

    def run(self):
        global pre_acc
        global pre_class_acc
        global pre_class_name
        _, output = predict_(sample, present_model)

        loss = output['loss']
        accuracy = output['acc']
        loss_str = str(round(loss, 4))
        accuracy_str = str(round(accuracy, 4))
        predict_labels = label_predicted_transfer(output, sample)
        true_labels = label_transfer(sample)
        self.ui.accLineEdit.setText(accuracy_str)
        self.ui.lossLineEdit.setText(loss_str)
        # 将真实标签放在最前方
        items = np.insert(predict_labels, 0, true_labels, axis=1)
        # 计算每类准确率
        acc_class = []
        for i_class in items:
            true_num = -1.0
            for index in i_class:
                if i_class[0] == index:
                    true_num += 1
            acc_this = true_num / n_query
            acc_class.append(acc_this)
        # 将准确率插在最后面
        items = np.insert(items, n_query + 1, acc_class, axis=1)
        # items = np.insert()

        for i in range(len(items)):
            for j in range(len(items[i])):
                item = QTableWidgetItem(items[i][j])
                self.ui.outputTableWidget.setItem(i, j, item)

        pre_acc = accuracy_str
        pre_class_name = items[:, 0]
        pre_class_acc = items[:, -1].astype(float)



    def datasetChange(self):
        global dataset
        dataset_name = self.ui.datasetComboBox.currentText()
        dataset = dataset_name + '/'
        print(dataset)
        None

    def modelChange(self):
        global present_model
        model_name = self.ui.modelComboBox.currentText()
        present_model = 'models/' + model_name + '.pkl'
        print(present_model)
        None

    def test(self):
        print(111)

    def analyzeOutcome(self):
        self.newWin = analyzeForm()
        self.newWin.show()
        # self.newWin.exec_()
        # sys.exit(self.newWin.exec_())
        None
    ########################################################################
    ## MENUS ==> DYNAMIC MENUS FUNCTIONS
    ########################################################################
    def Button(self):
        # GET BT CLICKED
        btnWidget = self.sender()

        # PAGE HOME
        if btnWidget.objectName() == "btn_home":
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_main)
            UIFunctions.resetStyle(self, "btn_home")
            UIFunctions.labelPage(self, "Home")
            btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

        # PAGE NEW USER
        if btnWidget.objectName() == "btn_new_user":
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)
            UIFunctions.resetStyle(self, "btn_new_user")
            UIFunctions.labelPage(self, "New User")
            btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))

        # PAGE WIDGETS
        if btnWidget.objectName() == "btn_widgets":
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_widgets)
            UIFunctions.resetStyle(self, "btn_widgets")
            UIFunctions.labelPage(self, "Custom Widgets")
            btnWidget.setStyleSheet(UIFunctions.selectMenu(btnWidget.styleSheet()))


    ## ==> END ##

    ########################################################################
    ## START ==> APP EVENTS
    ########################################################################

    ## EVENT ==> MOUSE DOUBLE CLICK
    ########################################################################
    def eventFilter(self, watched, event):
        if watched == self.le and event.type() == QtCore.QEvent.MouseButtonDblClick:
            print("pos: ", event.pos())
    ## ==> END ##

    ## EVENT ==> MOUSE CLICK
    ########################################################################
    def mousePressEvent(self, event):
        self.dragPos = event.globalPos()
        if event.buttons() == Qt.LeftButton:
            print('Mouse click: LEFT CLICK')
        if event.buttons() == Qt.RightButton:
            print('Mouse click: RIGHT CLICK')
        if event.buttons() == Qt.MidButton:
            print('Mouse click: MIDDLE BUTTON')
    ## ==> END ##

    ## EVENT ==> KEY PRESSED
    ########################################################################
    def keyPressEvent(self, event):
        print('Key: ' + str(event.key()) + ' | Text Press: ' + str(event.text()))
    ## ==> END ##

    ## EVENT ==> RESIZE EVENT
    ########################################################################
    def resizeEvent(self, event):
        self.resizeFunction()
        return super(MainWindow, self).resizeEvent(event)

    def resizeFunction(self):
        print('Height: ' + str(self.height()) + ' | Width: ' + str(self.width()))
    ## ==> END ##

    ########################################################################
    ## END ==> APP EVENTS
    ############################## ---/--/--- ##############################

class analyzeForm(QWidget):
    def __init__(self):
        super(analyzeForm, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        startSize = QSize(1200, 1000)
        self.resize(startSize)
        self.setMinimumSize(startSize)
        self.ui.gridLayout_acc = QGridLayout(self.ui.canvasWidget)
        global pre_acc
        global pre_class_acc
        global pre_class_name

        print(pre_acc)
        self.ui.allaccLineEdit.setText(pre_acc)

        # x = np.arange(0, 6, 0.1)
        # y = np.sin(x)
        # 绘图部分
        acc = pre_class_acc
        name = pre_class_name
        self.ui.F = MyFigureAnalyze(width=3, height=2, dpi=100)
        self.ui.F.plot_analyze(acc, name)
        self.ui.gridLayout_acc.addWidget(self.ui.F)

        # 结果分析部分
        if(dataset == 'omniglot/'):
            dir = 'dataset/omniglot/images_evaluation/'
        if(dataset == 'mini-imagenet/'):
            dir = 'dataset/mini-imagenet/test/'
        dir_list = []
        i = 0
        for n in name:
            imgList = dir + n + '/'
            first_file = os.listdir(imgList)[0]
            dir_file = imgList + first_file
            pic = QtGui.QPixmap(dir_file)
            self.label_pic = QtWidgets.QLabel(self.ui.analyzeWidget)
            self.label_pic.setPixmap(pic)
            self.label_name = QtWidgets.QLabel(self.ui.analyzeWidget)
            self.label_name.setText(n)
            self.label_name.setStyleSheet("QLabel { color : white; }")

            self.ui.outputTableWidget.setCellWidget(i, 0, self.label_pic)
            self.ui.outputTableWidget.setCellWidget(i, 1, self.label_name)
            print(dir_file)
            dir_list.append(dir_file)
            i += 1

        i = 0
        acc = acc.astype(str)
        for a in acc:
            self.label_acc = QtWidgets.QLabel(self.ui.analyzeWidget)
            self.label_acc.setText(a)
            self.label_acc.setStyleSheet("QLabel { color : white; }")
            a = float(a)
            self.label_warn = QtWidgets.QLabel(self.ui.analyzeWidget)
            if(a < 0.5):
                self.label_warn.setText("warning:\n the accuracy \n of this class\n is to low", )
                self.label_warn.setStyleSheet("QLabel { color : red; }")
            else:
                self.label_warn.setText("no warning")
                self.label_warn.setStyleSheet("QLabel { color : white; }")
            self.ui.outputTableWidget.setCellWidget(i, 2, self.label_acc)
            self.ui.outputTableWidget.setCellWidget(i, 3, self.label_warn)

            i += 1

        print(type(dir_list[0]))

        # self.ui.imgaLabel.setPixmap(QPixmap(dir_list[0]))
        # self.ui.imgbLabel.setPixmap(QPixmap(dir_list[1]))
        # self.ui.imgcLabel.setPixmap(QPixmap(dir_list[2]))
        # self.ui.imgdLabel.setPixmap(QPixmap(dir_list[3]))
        # self.ui.imgeLabel.setPixmap(QPixmap(dir_list[4]))
        #
        # self.ui.imgaLabel.setScaledContents(True)
        # self.ui.imgbLabel.setScaledContents(True)
        # self.ui.imgcLabel.setScaledContents(True)
        # self.ui.imgdLabel.setScaledContents(True)
        # self.ui.imgeLabel.setScaledContents(True)
        #



def select_dataset(dataset_name):
    if dataset_name == 'omniglot/':
        # trainx, trainy = read_images('dataset/ ' + dataset + 'images_background')
        # testx, testy = read_images('dataset/' + dataset + 'images_evaluation')
        trainx = np.load('data_processed/omni_trainx.npy')
        trainy = np.load('data_processed/omni_trainy.npy')
        testx = np.load('data_processed/omni_testx.npy')
        testy = np.load('data_processed/omni_testy.npy')
    if dataset_name == 'mini-imagenet/':
        # trainx, trainy = read_mini_images('dataset/' + dataset + 'train/')
        # testx, testy = read_mini_images('dataset/' + dataset + 'test/')
        trainx = np.load('data_processed/mini_trainx.npy')
        trainy = np.load('data_processed/mini_trainy.npy')
        testx = np.load('data_processed/mini_testx.npy')
        testy = np.load('data_processed/mini_testy.npy')
    if dataset_name == 'CUB/':
        # trainx, trainy = read_mini_images('dataset/' + dataset + 'train/')
        # testx, testy = read_mini_images('dataset/' + dataset + 'test/')
        trainx = np.load('data_processed/mini_trainx.npy')
        trainy = np.load('data_processed/mini_trainy.npy')
        testx = np.load('data_processed/mini_testx.npy')
        testy = np.load('data_processed/mini_testy.npy')

    return trainx, trainy, testx, testy


if __name__ == "__main__":
    print(torch.cuda.is_available())
    dataset = 'omniglot/'

    trainx, trainy, testx, testy = select_dataset(dataset)
    present_model = 'models/proto_1.pkl'
    print(trainx.shape, trainy.shape, testx.shape, testy.shape)
    n_way = 5
    n_support = 5
    n_query = 5
    # 用于取出数据做分析
    pre_acc = ''
    pre_class_name = np.arange(5)
    pre_class_acc = np.arange(5)
    app = QApplication(sys.argv)
    QtGui.QFontDatabase.addApplicationFont('fonts/segoeui.ttf')
    QtGui.QFontDatabase.addApplicationFont('fonts/segoeuib.ttf')
    window = MainWindow()
    sys.exit(app.exec_())
