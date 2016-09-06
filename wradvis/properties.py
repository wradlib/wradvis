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


# Properties
class PropertiesWidget(QtGui.QWidget):
    """
    Widget for editing parameters
    """
    signal_slider_changed = QtCore.pyqtSignal(name='slidervalueChanged')
    signal_speed_changed = QtCore.pyqtSignal(name='speedChanged')
    signal_playpause_changed = QtCore.pyqtSignal(name='startstop')
    signal_data_changed = QtCore.pyqtSignal(name='data_changed')

    def __init__(self, parent=None):
        super(PropertiesWidget, self).__init__(parent)

        # Data Source Control
        self.sourcebox = QtGui.QGridLayout()
        # Horizontal line
        self.hline = QtGui.QFrame()
        self.hline.setFrameShape(QtGui.QFrame.HLine)
        self.hline.setFrameShadow(QtGui.QFrame.Sunken)
        self.dirname = conf["dirs"]["rw"]
        self.dirLabel = LongLabel(self.dirname)
        self.filelist = sorted(
            glob.glob(os.path.join(self.dirname, "raa01*.gz")))
        #self.frames = len(self.filelist)
        self.actualFrame = 0
        self.dirButton = self.createButton(QtGui.QStyle.SP_DirHomeIcon,
                                           QtCore.QSize(18, 18),
                                           "Load Directory",
                                           self.selectDir)
        self.sourcebox.addWidget(self.dirButton, 0, 0)
        self.sourcebox.addWidget(self.dirLabel, 1, 0)
        self.dirLabel.setFixedSize(250, 14)
        self.sourcebox.addWidget(self.hline, 2, 0, 1, 3)

        # Media Control
        self.mediabox = QtGui.QGridLayout()
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(self.get_frames())
        self.slider.setTickInterval(1)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(self.update_slider)
        self.speed = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.speed.setMinimum(0)
        self.speed.setMaximum(1000)
        self.speed.setTickInterval(10)
        self.speed.setSingleStep(10)
        self.speed.valueChanged.connect(self.speed_changed)
        self.dateLabel = QtGui.QLabel("Date", self)
        self.date = QtGui.QLabel("1900-01-01", self)
        self.timeLabel = QtGui.QLabel("Time", self)
        self.sliderLabel = QtGui.QLabel("00:00", self)
        self.createMediaButtons()
        self.hline1 = QtGui.QFrame()
        self.hline1.setFrameShape(QtGui.QFrame.HLine)
        self.hline1.setFrameShadow(QtGui.QFrame.Sunken)
        self.mediabox.addWidget(self.dateLabel, 0, 0)
        self.mediabox.addWidget(self.date, 0, 4)
        self.mediabox.addWidget(self.timeLabel, 1, 0)
        self.mediabox.addWidget(self.sliderLabel, 1, 4)
        self.mediabox.addWidget(self.playPauseButton, 2, 0)
        self.mediabox.addWidget(self.fwdButton, 2, 2)
        self.mediabox.addWidget(self.rewButton, 2, 1)
        self.mediabox.addWidget(self.slider, 2, 3, 1, 4)
        self.mediabox.addWidget(self.speed, 3, 0, 1, 7)
        self.mediabox.addWidget(self.hline1, 4, 0, 1, 7)

        # Mouse Properties
        self.mousebox = QtGui.QGridLayout()

        self.r0 = utils.get_radolan_origin()
        self.mousePointLabel = QtGui.QLabel("Mouse Position", self)
        self.mousePointXYLabel = QtGui.QLabel("XY", self)
        self.mousePointLLLabel = QtGui.QLabel("LL", self)
        self.mousePointXY = QtGui.QLabel("", self)
        self.mousePointLL = QtGui.QLabel("", self)
        self.hline2 = QtGui.QFrame()
        self.hline2.setFrameShape(QtGui.QFrame.HLine)
        self.hline2.setFrameShadow(QtGui.QFrame.Sunken)
        self.mousebox.addWidget(self.mousePointLabel, 0, 0)
        self.mousebox.addWidget(self.mousePointXYLabel, 0, 1)
        self.mousebox.addWidget(self.mousePointXY, 0, 2)
        self.mousebox.addWidget(self.mousePointLLLabel, 1, 1)
        self.mousebox.addWidget(self.mousePointLL, 1, 2)
        self.mousebox.addWidget(self.hline2, 2, 0, 1, 3)

        # initialize vertical boxgrid
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(self.sourcebox)
        vbox.addLayout(self.mediabox)
        vbox.addLayout(self.mousebox)
        vbox.addStretch(0)

        self.setLayout(vbox)

    def update_slider(self, position):
        self.actualFrame = position - 1
        self.signal_slider_changed.emit()

    def speed_changed(self, position):
        self.signal_speed_changed.emit()

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

    def selectDir(self):
        f = QtGui.QFileDialog.getExistingDirectory(self,
                                                   "Select a Folder",
                                                   "/automount/data/radar/dwd",
                                                   QtGui.QFileDialog.ShowDirsOnly)

        if os.path.isdir(f):
            self.dirLabel.setText(f)
            self.dirname = str(f)
            self.filelist = glob.glob(os.path.join(self.dirname, "raa01*"))
            self.slider.setMaximum(self.get_frames())
            self.signal_slider_changed.emit()

    def seekforward(self):
        if self.slider.value() == self.slider.maximum():
            self.slider.setValue(1)
        else:
            self.slider.setValue(self.slider.value() + 1)
        self.update_slider(self.slider.value())

    def seekbackward(self):
        #print(self.slider.value())
        if self.slider.value() == 1:
            self.slider.setValue(self.slider.maximum())
            self.update_slider(self.slider.maximum())
        else:
            self.slider.setValue(self.slider.value() - 1)
            self.update_slider(self.slider.value() - 1)

    def playpause(self):
        if self.playPauseButton.toolTip() == 'Play':
            self.playPauseButton.setToolTip("Pause")
            #self.timer.start()
            self.playPauseButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPause))
        else:
            self.playPauseButton.setToolTip("Play")
            #self.timer.stop()
            self.playPauseButton.setIcon(self.style().standardIcon(QtGui.QStyle.SP_MediaPlay))
        self.signal_playpause_changed.emit()

    def show_mouse(self, point):
        self.mousePointXY.setText("({0:d}, {1:d})".format(int(point[0]), int(point[1])))
        ll = utils.radolan_to_wgs84(point + self.r0)
        self.mousePointLL.setText("({0:.2f}, {1:.2f})".format(ll[0], ll[1]))

    def get_frames(self):
        return(len(self.filelist))
