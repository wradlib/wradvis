#!/usr/bin/env python
# Copyright (c) 2016-2018, wradlib developers.
# Distributed under the MIT License. See LICENSE.txt for more info.

import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QApplication, QSplitter, QAction,
                             QDockWidget, QSizePolicy)
import vispy

import matplotlib
matplotlib.use('Qt5Agg')
# other wradvis imports
from wradvis.glcanvas import RadolanWidget
from wradvis.mplcanvas import MplWidget
from wradvis.properties import Properties, MediaBox, SourceBox, \
    MouseBox, GraphBox
from wradvis import utils
from wradvis.config import conf


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        print(vispy.sys_info())

        self.resize(825, 500)
        self.setWindowTitle('RADOLAN Viewer')
        self._need_canvas_refresh = False

        self.timer = QtCore.QTimer()

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
        self.splitter = QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.swapper[0])
        self.splitter.addWidget(self.swapper[1])
        self.swapper[1].hide()
        self.setCentralWidget(self.splitter)

        self.createActions()
        self.createMenus()
        self.createDockWindows()

        self.connect_signals()

        self.props.update_props()

    def connect_signals(self):
        self.mediabox.signal_playpause_changed.connect(self.start_stop)
        self.mediabox.signal_speed_changed.connect(self.speed)
        self.mediabox.connect_signals()
        self.rwidget.connect_signals()
        self.graphbox.connect_signals()

    def createActions(self):
        # Set  directory
        self.setDataDir = QAction("&Set  directory", self,
                                  statusTip='Set  directory',
                                  triggered=self.props.set_datadir)
        # Open project (configuration)
        self.openConf = QAction("&Open project", self)
        self.openConf.setShortcut("Ctrl+O")
        self.openConf.setStatusTip('Open project')
        self.openConf.triggered.connect(self.props.open_conf)

        # Save project (configuration)
        self.saveConf = QAction("&Save project", self,
                                      shortcut="Ctrl+S",
                                      statusTip='Save project',
                                      triggered=self.props.save_conf)

        # Load netcdf (data file)
        self.loadNC = QAction("&Load NetCDF", self,
                                    shortcut="Ctrl+L",
                                    statusTip='Load netCDF data file',
                                    triggered=self.props.load_data)

        # Save netcdf (data file)
        self.saveNC = QAction("Save &NetCDF", self,
                                      shortcut="Ctrl+N",
                                      statusTip='Save data file as netCDF',
                                      triggered=self.props.save_data)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.setDataDir)
        self.fileMenu.addAction(self.openConf)
        self.fileMenu.addAction(self.saveConf)
        self.fileMenu.addAction(self.loadNC)
        self.fileMenu.addAction(self.saveNC)

        self.toolsMenu = self.menuBar().addMenu('&Tools')

        self.helpMenu = self.menuBar().addMenu('&Help')

    def createDockWindows(self):
        dock = QDockWidget("Radar Source Data", self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.sourcebox = SourceBox(self)
        dock.setWidget(self.sourcebox)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.toolsMenu.addAction(dock.toggleViewAction())

        dock = QDockWidget("Media Handling", self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.mediabox = MediaBox(self)
        dock.setWidget(self.mediabox)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.toolsMenu.addAction(dock.toggleViewAction())

        dock = QDockWidget("Mouse Interaction", self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.mousebox = MouseBox(self)
        dock.setWidget(self.mousebox)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.toolsMenu.addAction(dock.toggleViewAction())

        dock = QDockWidget("Time Graphs", self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        size_pol = (QSizePolicy.MinimumExpanding,
                    QSizePolicy.MinimumExpanding)
        self.graphbox = GraphBox(self, size_pol=size_pol)
        dock.setWidget(self.graphbox)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        self.toolsMenu.addAction(dock.toggleViewAction())

    def start_stop(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start()

    def speed(self, value):
        self.timer.setInterval(value)

    def keyPressEvent(self, event):
        if isinstance(event, QtGui.QKeyEvent):
            text = event.text()
        else:
            text = event.text
        print(event)
        # Todo: fully implement MPLCanvas
        #if text == 'c':
        #    self.swapper = self.swapper[::-1]
        #    self.iwidget = self.swapper[0]
        #    self.swapper[0].show()
        #    self.swapper[0].setFocus()
        #    self.swapper[1].hide()


def start(args=None):
    if args is None:
        args = sys.argv[1:]
    appQt = QApplication(args)
    win = MainWindow()
    win.show()
    appQt.exec_()


if __name__ == '__main__':
   start()
