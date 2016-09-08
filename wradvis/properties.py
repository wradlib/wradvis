# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016, wradlib Development Team. All Rights Reserved.
# Distributed under the MIT License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
#!/usr/bin/env python

"""
"""

import os
import glob

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QLabel, QFontMetrics, QPainter

from wradvis import utils
from wradvis.config import conf


class LongLabel(QLabel):
    def paintEvent( self, event ):
        painter = QPainter(self)

        metrics = QFontMetrics(self.font())
        elided  = metrics.elidedText(self.text(),
                                     QtCore.Qt.ElideLeft,
                                     self.width())

        painter.drawText(self.rect(), self.alignment(), elided)


class DockBox(QtGui.QWidget):
    def __init__(self, parent=None):
        super(DockBox, self).__init__(parent)

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        self.props = parent.props


class MouseBox(DockBox):
    def __init__(self, parent=None):
        super(MouseBox, self).__init__(parent)

        self.parent = parent
        self.r0 = utils.get_radolan_origin()
        self.mousePointLabel = QtGui.QLabel("Mouse Position", self)
        self.mousePointXYLabel = QtGui.QLabel("XY", self)
        self.mousePointLLLabel = QtGui.QLabel("LL", self)
        self.mousePointXY = QtGui.QLabel("", self)
        self.mousePointLL = QtGui.QLabel("", self)
        self.hline2 = QtGui.QFrame()
        self.hline2.setFrameShape(QtGui.QFrame.HLine)
        self.hline2.setFrameShadow(QtGui.QFrame.Sunken)
        self.layout.addWidget(self.mousePointLabel, 0, 0)
        self.layout.addWidget(self.mousePointXYLabel, 0, 1)
        self.layout.addWidget(self.mousePointXY, 0, 2)
        self.layout.addWidget(self.mousePointLLLabel, 1, 1)
        self.layout.addWidget(self.mousePointLL, 1, 2)
        self.layout.addWidget(self.hline2, 2, 0, 1, 3)

        # connect to signal
        self.parent.rwidget.canvas.mouse_moved.connect(self.mouse_moved)

    def mouse_moved(self, event):
        point = self.parent.rwidget.canvas._mouse_position
        self.mousePointXY.setText(
            "({0:d}, {1:d})".format(int(point[0]), int(point[1])))
        ll = utils.radolan_to_wgs84(point + self.r0)
        self.mousePointLL.setText(
            "({0:.2f}, {1:.2f})".format(ll[0], ll[1]))


class SourceBox(DockBox):
    def __init__(self, parent=None):
        super(SourceBox, self).__init__(parent)

        palette = QtGui.QPalette()
        self.setStyleSheet(""" QMenuBar {
                font-size:13px;
            }""")

        # Horizontal line
        self.hline = QtGui.QFrame()
        self.hline.setFrameShape(QtGui.QFrame.HLine)
        self.hline.setFrameShadow(QtGui.QFrame.Sunken)
        self.dirname = conf["dirs"]["data"]
        self.dirLabel = LongLabel(self.dirname)
        self.props.filelist = sorted(
            glob.glob(os.path.join(self.dirname, "raa01*.gz")))
        self.props.frames = len(self.props.filelist)
        self.props.actualFrame = 0

        # Data source box (control via File menu bar)
        #self.layout.setContentsMargins(1, 7, 1, 1)
        self.layout.addWidget(LongLabel("Current data directory"), 0, 0, 1, 7)
        self.layout.addWidget(self.dirLabel, 1, 0, 1, 7)
        self.dirLabel.setFixedWidth(200)
        palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.darkGreen)
        self.dirLabel.setPalette(palette)

        self.props.props_changed.connect(self.update_label)

    def update_label(self):
        self.dirLabel.setText(self.props.dir)
        self.dirname = str(self.props.dir)


class MediaBox(DockBox):

    signal_playpause_changed = QtCore.pyqtSignal(name='startstop')
    signal_slider_changed = QtCore.pyqtSignal(name='slidervalueChanged')
    signal_speed_changed = QtCore.pyqtSignal(name='speedChanged')

    def __init__(self, parent=None):
        super(MediaBox, self).__init__(parent)
        # Media Control
        self.data = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.data.setMinimum(1)
        self.data.setMaximum(self.props.frames)
        self.data.setTickInterval(1)
        self.data.setSingleStep(1)
        self.data.valueChanged.connect(self.update_slider)
        self.speed = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.speed.setMinimum(0)
        self.speed.setMaximum(1000)
        self.speed.setTickInterval(10)
        self.speed.setSingleStep(10)
        self.speed.valueChanged.connect(self.speed_changed)
        self.dateLabel = QtGui.QLabel("Date")#, self)
        self.dateLabel.setMaximumHeight(10)
        self.date = QtGui.QLabel("1900-01-01")#, self)
        self.date.setMaximumHeight(10)
        self.timeLabel = QtGui.QLabel("Time")#, self)
        self.timeLabel.setMaximumHeight(10)
        self.sliderLabel = QtGui.QLabel("00:00")#, self)
        self.sliderLabel.setMaximumHeight(10)
        self.createMediaButtons()
        self.hline0 = QtGui.QFrame()
        self.hline0.setFrameShape(QtGui.QFrame.HLine)
        self.hline0.setFrameShadow(QtGui.QFrame.Sunken)
        self.hline1 = QtGui.QFrame()
        self.hline1.setFrameShape(QtGui.QFrame.HLine)
        self.hline1.setFrameShadow(QtGui.QFrame.Sunken)
        # self.mediabox.setContentsMargins(1, 20, 1, 1)

        self.layout.addWidget(self.hline0, 0, 0, 1, 7)
        self.layout.addWidget(self.dateLabel, 1, 0, 1, 7)
        self.layout.addWidget(self.date, 1, 4, 1, 3)
        self.layout.addWidget(self.timeLabel, 2, 0, 1, 7)
        self.layout.addWidget(self.sliderLabel, 2, 4, 1, 3)
        self.layout.addWidget(self.playPauseButton, 3, 0)
        self.layout.addWidget(self.fwdButton, 3, 2)
        self.layout.addWidget(self.rewButton, 3, 1)
        self.layout.addWidget(self.data, 3, 3, 1, 4)
        self.layout.addWidget(self.speed, 4, 0, 1, 7)
        self.layout.addWidget(self.hline1, 5, 0, 1, 7)

        self.props.props_changed.connect(self.update_props)

        print("MediaBox")


    def createMediaButtons(self):
        iconSize = QtCore.QSize(18, 18)

        self.playPauseButton = self.createButton(QtGui.QStyle.SP_MediaPlay,
                                                 iconSize,
                                                 "Play",
                                                 self.playpause)
        self.fwdButton = self.createButton(QtGui.QStyle.SP_MediaSeekForward,
                                           iconSize,
                                           "SeekForward",
                                           self.seekforward)

        self.rewButton = self.createButton(QtGui.QStyle.SP_MediaSeekBackward,
                                           iconSize,
                                           "SeekBackward",
                                           self.seekbackward)

    def createButton(self, style, size, tip, cfunc):
        button = QtGui.QToolButton()
        button.setIcon(self.style().standardIcon(style))
        button.setIconSize(size)
        button.setToolTip(tip)
        button.clicked.connect(cfunc)
        return button

    def speed_changed(self, position):
        self.signal_speed_changed.emit()

    def update_slider(self, position):
        self.props.actualFrame = position - 1
        self.signal_slider_changed.emit()

    def seekforward(self):
        if self.data.value() == self.data.maximum():
            self.data.setValue(1)
        else:
            self.data.setValue(self.data.value() + 1)

    def seekbackward(self):
        if self.data.value() == 1:
            self.data.setValue(self.data.maximum())
        else:
            self.data.setValue(self.data.value() - 1)

    def playpause(self):
        if self.playPauseButton.toolTip() == 'Play':
            self.playPauseButton.setToolTip("Pause")
            self.playPauseButton.setIcon(
                self.style().standardIcon(QtGui.QStyle.SP_MediaPause))
        else:
            self.playPauseButton.setToolTip("Play")
            self.playPauseButton.setIcon(
                self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
        self.signal_playpause_changed.emit()

    def update_props(self):
        self.data.setMaximum(self.props.frames)
        self.data.setValue(1)


# Properties
class Properties(QtCore.QObject):
    """
    Object for storing parameters
    """
    signal_props_changed = QtCore.pyqtSignal(name='props_changed')

    def __init__(self, parent=None):
        super(Properties, self).__init__(parent)

        self.parent = parent

    def set_datadir(self):
        f = QtGui.QFileDialog.getExistingDirectory(self.parent,
                                                   "Select a Folder",
                                                   "/automount/data/radar/dwd",
                                                   QtGui.QFileDialog.ShowDirsOnly)

        if os.path.isdir(f):
            conf["dirs"]["data"] = str(f)
            self.update_props()

    def save_conf(self):
        name = QtGui.QFileDialog.getSaveFileName(self.parent, 'Save File')
        with open(name, "w") as f:
            conf.write(f)

    def open_conf(self):
        name = QtGui.QFileDialog.getOpenFileName(self.parent, 'Open project')
        with open(name, "r") as f:
            conf.read_file(f)
        self.update_props()

    def update_props(self):
        self.dir = conf["dirs"]["data"]
        self.filelist = glob.glob(os.path.join(self.dir, "raa01*"))
        self.frames = len(self.filelist)
        self.signal_props_changed.emit()
