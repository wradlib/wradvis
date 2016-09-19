# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016, wradlib Development Team. All Rights Reserved.
# Distributed under the MIT License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
#!/usr/bin/env python

import sys
from PyQt4 import QtGui, QtCore
import vispy

# other wradvis imports
from wradvis.glcanvas import RadolanWidget
from wradvis.mplcanvas import MplWidget
from wradvis.properties import Properties, MediaBox, SourceBox, MouseBox
from wradvis import utils
from wradvis.config import conf


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        print(vispy.sys_info())

        self.resize(825, 500)
        self.setWindowTitle('RADOLAN Viewer')
        self._need_canvas_refresh = False

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.reload)

        # initialize RadolanCanvas
        self.rwidget = RadolanWidget(self)
        self.iwidget = self.rwidget

        # initialize MplWidget
        self.mwidget = MplWidget()

        # canvas swapper
        self.swapper = []
        self.swapper.append(self.rwidget)
        self.swapper.append(self.mwidget)

        # need some tracer for the mouse position
        self.iwidget.canvas.key_pressed.connect(self.keyPressEvent)

        # add PropertiesWidget
        self.props = Properties(self)

        # add Horizontal Splitter and the three widgets
        self.splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.swapper[0])
        self.splitter.addWidget(self.swapper[1])
        self.swapper[1].hide()
        self.setCentralWidget(self.splitter)

        self.createActions()
        self.createMenus()
        self.createDockWindows()

        self.connect_signals()

        # finish init
        self.props.update_props()

    def connect_signals(self):
        self.mediabox.signal_playpause_changed.connect(self.start_stop)
        self.mediabox.signal_time_slider_changed.connect(self.slider_changed)
        self.mediabox.signal_speed_changed.connect(self.speed)
        self.props.signal_props_changed.connect(self.slider_changed)

    def createActions(self):
        # Set  directory
        self.setDataDir = QtGui.QAction("&Set  directory", self,
                                        statusTip='Set  directory',
                                        triggered=self.props.set_datadir)
        # Open project (configuration)
        self.openConf = QtGui.QAction("&Open project", self,
                                      shortcut="Ctrl+O",
                                      statusTip='Open project',
                                      triggered=self.props.open_conf)

        # Save project (configuration)
        self.saveConf = QtGui.QAction("&Save project", self,
                                      shortcut="Ctrl+S",
                                      statusTip='Save project',
                                      triggered=self.props.save_conf)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.setDataDir)
        self.fileMenu.addAction(self.openConf)
        self.fileMenu.addAction(self.saveConf)

        self.toolsMenu = self.menuBar().addMenu('&Tools')

        self.helpMenu = self.menuBar().addMenu('&Help')

    def createDockWindows(self):
        dock = QtGui.QDockWidget("Radar Source Data", self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.sourcebox = SourceBox(self)
        dock.setWidget(self.sourcebox)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.toolsMenu.addAction(dock.toggleViewAction())

        dock = QtGui.QDockWidget("Media Handling", self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.mediabox = MediaBox(self)
        dock.setWidget(self.mediabox)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.toolsMenu.addAction(dock.toggleViewAction())

        dock = QtGui.QDockWidget("Mouse Interaction", self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.mousebox = MouseBox(self)
        dock.setWidget(self.mousebox)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.toolsMenu.addAction(dock.toggleViewAction())

    def reload(self):
        if self.mediabox.time_slider.value() >= self.mediabox.range.high():
            self.mediabox.time_slider.setValue(self.mediabox.range.low())
        else:
            self.mediabox.time_slider.setValue(self.mediabox.time_slider.value() + 1)

    def start_stop(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start()

    def speed(self):
        self.timer.setInterval(self.mediabox.speed.value())

    def slider_changed(self, pos):
        try:
            # Todo: switching happens here,
            # but we should just use a common reading function, where the
            # underlying wradlib function is exchanged on switching
            # format
            if self.props.product == 'DX':
                self.data, _ = utils.read_dx(
                    self.props.filelist[pos])

            else:
                self.data, _ = utils.read_radolan(self.props.filelist[pos])
                if self.props.product == 'RX':
                    self.data = (self.data / 2) - 32.5
        except IndexError:
            print("Could not read any data.")
        else:
            self.iwidget.set_data(self.data)

    def keyPressEvent(self, event):
        if isinstance(event, QtGui.QKeyEvent):
            text = event.text()
        else:
            text = event.text
        if text == 'c':
            self.swapper = self.swapper[::-1]
            self.iwidget = self.swapper[0]
            self.swapper[0].show()
            self.swapper[0].setFocus()
            self.swapper[1].hide()


def start(args=None):
    if args is None:
        args = sys.argv[1:]
    appQt = QtGui.QApplication(args)
    win = MainWindow()
    win.show()
    appQt.exec_()

if __name__ == '__main__':
    start()