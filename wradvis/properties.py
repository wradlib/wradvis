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
from datetime import datetime as dt

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QLabel, QFontMetrics, QPainter

from wradvis import utils
from wradvis.config import conf


class TimeSlider(QtGui.QSlider):
    """
        This software is OSI Certified Open Source Software.
        OSI Certified is a certification mark of the Open Source Initiative.

        Copyright (c) 2006, Enthought, Inc.
        All rights reserved.

        Redistribution and use in source and binary forms, with or without
        modification, are permitted provided that the following conditions are met:

         * Redistributions of source code must retain the above copyright notice, this
           list of conditions and the following disclaimer.
         * Redistributions in binary form must reproduce the above copyright notice,
           this list of conditions and the following disclaimer in the documentation
           and/or other materials provided with the distribution.
         * Neither the name of Enthought, Inc. nor the names of its contributors may
           be used to endorse or promote products derived from this software without
           specific prior written permission.

        THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
        ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
        WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
        DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
        ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
        (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
        LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
        ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
        (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
        SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

        A slider for ranges.
        This class provides a dual-slider for ranges, where there is a defined
        maximum and minimum, as is a normal slider, but instead of having a
        single slider value, there are 2 slider values.
        This class emits the same signals as the QSlider base class, with the
        exception of valueChanged
    """
    def __init__(self, *args):
        super(TimeSlider, self).__init__(*args)

        self._low = self.minimum()
        self._high = self.maximum()

        self.pressed_control = QtGui.QStyle.SC_None
        self.hover_control = QtGui.QStyle.SC_None
        self.click_offset = 0

        # 0 for the low, 1 for the high, -1 for both
        self.active_slider = 0

    def low(self):
        return self._low

    def setLow(self, low):
        self._low = low
        self.update()

    def high(self):
        return self._high

    def setHigh(self, high):
        self._high = high
        self.update()


    def paintEvent(self, event):
        # based on
        # http://qt.gitorious.org/qt/qt/blobs/master/src/gui/widgets/qslider.cpp

        painter = QtGui.QPainter(self)
        style = QtGui.QApplication.style()

        for i, value in enumerate([self._low, self._high]):
            opt = QtGui.QStyleOptionSlider()
            self.initStyleOption(opt)

            # Only draw the groove for the first slider so it doesn't get drawn
            # on top of the existing ones every time
            if i == 0:
                opt.subControls = QtGui.QStyle.SC_SliderGroove | QtGui.QStyle.SC_SliderHandle
            else:
                opt.subControls = QtGui.QStyle.SC_SliderHandle

            if self.tickPosition() != self.NoTicks:
                opt.subControls |= QtGui.QStyle.SC_SliderTickmarks

            if self.pressed_control:
                opt.activeSubControls = self.pressed_control
                opt.state |= QtGui.QStyle.State_Sunken
            else:
                opt.activeSubControls = self.hover_control

            opt.sliderPosition = value
            opt.sliderValue = value
            style.drawComplexControl(QtGui.QStyle.CC_Slider, opt, painter, self)


    def mousePressEvent(self, event):
        event.accept()

        style = QtGui.QApplication.style()
        button = event.button()

        # In a normal slider control, when the user clicks on a point in the
        # slider's total range, but not on the slider part of the control the
        # control would jump the slider value to where the user clicked.
        # For this control, clicks which are not direct hits will slide both
        # slider parts

        if button:
            opt = QtGui.QStyleOptionSlider()
            self.initStyleOption(opt)

            self.active_slider = -1

            for i, value in enumerate([self._low, self._high]):
                opt.sliderPosition = value
                hit = style.hitTestComplexControl(style.CC_Slider, opt, event.pos(), self)
                if hit == style.SC_SliderHandle:
                    self.active_slider = i
                    self.pressed_control = hit

                    self.triggerAction(self.SliderMove)
                    self.setRepeatAction(self.SliderNoAction)
                    self.setSliderDown(True)
                    break

            if self.active_slider < 0:
                self.pressed_control = QtGui.QStyle.SC_SliderHandle
                self.click_offset = self.__pixelPosToRangeValue(self.__pick(event.pos()))
                self.triggerAction(self.SliderMove)
                self.setRepeatAction(self.SliderNoAction)
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.pressed_control != QtGui.QStyle.SC_SliderHandle:
            event.ignore()
            return

        event.accept()
        new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))
        opt = QtGui.QStyleOptionSlider()
        self.initStyleOption(opt)

        if self.active_slider < 0:
            offset = new_pos - self.click_offset
            self._high += offset
            self._low += offset
            if self._low < self.minimum():
                diff = self.minimum() - self._low
                self._low += diff
                self._high += diff
            if self._high > self.maximum():
                diff = self.maximum() - self._high
                self._low += diff
                self._high += diff
        elif self.active_slider == 0:
            if new_pos >= self._high:
                new_pos = self._high - 1
            self._low = new_pos
        else:
            if new_pos <= self._low:
                new_pos = self._low + 1
            self._high = new_pos

        self.click_offset = new_pos

        self.update()

        self.emit(QtCore.SIGNAL('sliderMoved(int)'), new_pos)

    def __pick(self, pt):
        if self.orientation() == QtCore.Qt.Horizontal:
            return pt.x()
        else:
            return pt.y()


    def __pixelPosToRangeValue(self, pos):
        opt = QtGui.QStyleOptionSlider()
        self.initStyleOption(opt)
        style = QtGui.QApplication.style()

        gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
        sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)

        if self.orientation() == QtCore.Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1

        return style.sliderValueFromPosition(self.minimum(), self.maximum(),
                                             pos-slider_min, slider_max-slider_min,
                                             opt.upsideDown)



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
        self.parent.rwidget.rcanvas.mouse_moved.connect(self.mouse_moved)
        self.parent.rwidget.pcanvas.mouse_moved.connect(self.mouse_moved)
        self.parent.mwidget.rcanvas.mouse_moved.connect(self.mouse_moved)

    def mouse_moved(self, event):
        # todo: check if originating from mpl and adapt self.r0 correctly
        point = self.parent.iwidget.canvas._mouse_position
        self.mousePointXY.setText(
            "({0:d}, {1:d})".format(int(point[0]), int(point[1])))

        # Todo: move this all to utils and use a generalized
        # ll-retrieving function
        if self.parent.props.product != 'DX':
            ll = utils.radolan_to_wgs84(point + self.r0)
        else:
            ll = utils.dx_to_wgs84(point)

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
        self.dirname = "None" #conf["dirs"]["data"]
        self.dirLabel = LongLabel(self.dirname)

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
        self.data.setTickInterval(1)
        self.data.setSingleStep(1)
        self.data.valueChanged.connect(self.update_slider)

        self.range = TimeSlider(QtCore.Qt.Horizontal)
        epoch = dt.utcfromtimestamp(0)
        now = int((dt.now() - epoch).total_seconds())
        self.range_min = QtGui.QLabel("01:01")
        self.range_max = QtGui.QLabel("01:01")
        self.range_start = QtGui.QLabel("01:01")
        self.range_end = QtGui.QLabel("01:01")
        # might also use valueChanged
        self.range.sliderMoved.connect(self.range_update)

        self.speed = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.speed.setMinimum(0)
        self.speed.setMaximum(1000)
        self.speed.setTickInterval(10)
        self.speed.setSingleStep(10)
        self.speed.valueChanged.connect(self.speed_changed)
        self.dateLabel = QtGui.QLabel("Date")
        self.date = QtGui.QLabel("1900-01-01")
        self.timeLabel = QtGui.QLabel("Time")
        self.sliderLabel = QtGui.QLabel("00:00")
        self.createMediaButtons()
        self.hline0 = QtGui.QFrame()
        self.hline0.setFrameShape(QtGui.QFrame.HLine)
        self.hline0.setFrameShadow(QtGui.QFrame.Sunken)
        self.hline1 = QtGui.QFrame()
        self.hline1.setFrameShape(QtGui.QFrame.HLine)
        self.hline1.setFrameShadow(QtGui.QFrame.Sunken)

        self.layout.addWidget(self.hline0, 0, 0, 1, 7)
        self.layout.addWidget(self.dateLabel, 1, 0, 1, 7)
        self.layout.addWidget(self.date, 1, 4, 1, 3)
        self.layout.addWidget(self.timeLabel, 2, 0, 1, 7)
        self.layout.addWidget(self.sliderLabel, 2, 4, 1, 3)
        self.layout.addWidget(self.playPauseButton, 3, 0)
        self.layout.addWidget(self.fwdButton, 3, 2)
        self.layout.addWidget(self.rewButton, 3, 1)
        self.layout.addWidget(self.data, 3, 3, 1, 4)
        self.layout.addWidget(self.range_start, 4, 0, 1, 1)
        self.layout.addWidget(self.range, 4, 1, 1, 5)
        self.layout.addWidget(self.range_end, 4, 6, 1, 1)
        self.layout.addWidget(self.speed, 5, 0, 1, 7)
        self.layout.addWidget(self.hline1, 6, 0, 1, 7)

        self.props.props_changed.connect(self.update_props)

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
        #if self.data.value() == self.data.maximum():
        if self.data.value() >= self.range.high():
            self.data.setValue(self.range.low())
        else:
            self.data.setValue(self.data.value() + 1)

    def seekbackward(self):
        if self.data.value() <= self.range.low():
            self.data.setValue(self.range.high())
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
        self.range.setMinimum(1)
        self.range.setMaximum(self.props.frames)
        self.range.setLow(1)
        self.range.setHigh(self.props.frames)
        self.range_update()

    def range_update(self):
        self.range_start.setText(self.props.cube[self.range.low() - 1]
                                 ['datetime'].strftime("%H:%M"))
        self.range_end.setText(self.props.cube[self.range.high() - 1]
                               ['datetime'].strftime("%H:%M"))


# Properties
class Properties(QtCore.QObject):
    """
    Object for storing parameters
    """
    signal_props_changed = QtCore.pyqtSignal(name='props_changed')

    def __init__(self, parent=None):
        super(Properties, self).__init__(parent)

        self.parent = parent
        self.update_props()

    def set_datadir(self):
        f = QtGui.QFileDialog.getExistingDirectory(self.parent,
                                                   "Select a Folder",
                                                   "/automount/data/radar/dwd",
                                                   QtGui.QFileDialog.ShowDirsOnly)

        if os.path.isdir(f):
            conf["dirs"]["data"] = str(f)
            try:
                _ , meta = utils.read_dx(glob.glob(os.path.join(self.dir, "raa0*"))[0])
            except ValueError:
                _, meta = utils.read_radolan(glob.glob(os.path.join(self.dir, "raa0*"))[0])
            conf["source"]["product"] = meta['producttype']
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
        self.product = conf["source"]["product"]
        self.parent.iwidget.set_canvas(self.product)
        self.clim = (conf.get("vis", "cmin"), conf.get("vis", "cmax"))
        self.parent.iwidget.set_clim(self.clim)
        self.loc = conf.get("source", "loc")
        self.filelist = glob.glob(os.path.join(self.dir, "raa0*{0}*".format(self.loc)))
        self.frames = len(self.filelist)
        self.actualFrame = 0
        self.cube = self.create_data_cube()
        self.signal_props_changed.emit()

    def create_data_cube(self):
        '''
            First attempt to create some data layer

            Here we just add the metadata dictionaries
        '''
        cube = []
        for name in self.filelist:
            _, meta = utils.read_radolan(name)
            cube.append(meta)
        return cube
