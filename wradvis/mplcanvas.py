# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016, wradlib Development Team. All Rights Reserved.
# Distributed under the MIT License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
#!/usr/bin/env python


import numpy as np
import matplotlib
matplotlib.use('Qt4Agg')


from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.cm import get_cmap
from mpl_toolkits.axes_grid1 import make_axes_locatable

from wradvis import utils
from wradvis import config


class MplCanvas(FigureCanvas):

    mouse_moved = QtCore.pyqtSignal(matplotlib.backend_bases.MouseEvent, name='mouse_moved')

    def __init__(self):#, parent, props):
        # plot definition
        self.fig = Figure()

        # initialization of the canvas
        FigureCanvas.__init__(self, self.fig)

        # we define the widget as expandable
        FigureCanvas.setSizePolicy(self,
        QtGui.QSizePolicy.Expanding,
        QtGui.QSizePolicy.Expanding)
        # notify the system of updated policy
        FigureCanvas.updateGeometry(self)

        cmap = get_cmap('cubehelix_r')

        self.ax = self.fig.add_subplot(111)
        grid = utils.get_radolan_grid()
        self.pm = self.ax.pcolormesh(grid[..., 0], grid[..., 1],
                                     np.zeros((900,900)),
                                     cmap=cmap,
                                     vmin=0, vmax=50)
        div = make_axes_locatable(self.ax)
        cax = div.append_axes("right", size="5%", pad=0.1)
        # add colorbar
        self.cbar = self.fig.colorbar(self.pm, cax=cax)
        self.ax.set_aspect('equal')
        self.ax.set_xlim([grid[..., 0].min(), grid[..., 0].max()])
        self.ax.set_ylim([grid[..., 1].min(), grid[..., 1].max()])
        self._mouse_position = None

        self.create_cities()

    def create_cities(self):
        self.selected = None
        cities = utils.get_cities_coords()
        cnameList = []
        ccoordList = []
        for k, v in cities.items():
            cnameList.append(k)
            ccoordList.append(v)
        ccoord = np.vstack(ccoordList)
        ccoord = utils.wgs84_to_radolan(ccoord)
        x = ccoord[..., 0]
        y = ccoord[..., 1]
        self.ax.scatter(x, y, s=100, c=['r']*len(x), picker=30)
        for i, txt in enumerate(cnameList):
            self.ax.annotate(txt, (x[i], y[i]),
                             horizontalalignment='right',
                             verticalalignment='top')
        self.mpl_connect('pick_event', self.onpick_cities)
        self.mpl_connect('motion_notify_event', self.on_move)

    def onpick_cities(self, event):
        artist = event.artist
        cid = event.ind[0]

        if self.selected is None:
            artist._facecolors[cid, :] = (0, 1, 0, 1)  # green
            self.selected = cid
        else:
            artist._facecolors[self.selected, :] = (1, 0, 0, 1)  # red
            if self.selected == cid:
                self.selected = None
            else:
                self.selected = cid
                artist._facecolors[self.selected, :] = (0, 1, 0, 1)  # green

        self.fig.canvas.draw()

    def on_key_press(self, event):
        self.key_pressed(event)

    def on_move(self, event):
        if event.inaxes:
            ax = event.inaxes  # the axes instance
            #print('data coords %f %f' % (event.xdata, event.ydata))
            self._mouse_position = np.array([event.xdata, event.ydata])
            self.mouse_moved.emit(event)


class MplWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.rcanvas = MplCanvas()
        self.pcanvas = MplCanvas()

        self.canvas = self.rcanvas

        # canvas swapper
        self.swapper = {}
        self.swapper['R'] = self.rcanvas
        self.swapper['P'] = self.pcanvas

        #self.splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        #self.splitter.addWidget(self.swapper['R'])
        #self.splitter.addWidget(self.swapper['P'])
        #self.swapper['P'].hide()

        # stretchfactors for correct splitter behaviour
        #self.splitter.setStretchFactor(0, 1)
        #self.splitter.setStretchFactor(1, 1)
        #self.splitter.setStretchFactor(2, 0)
        self.hbl = QtGui.QHBoxLayout()
        self.hbl.addWidget(self.swapper['R'])
        self.hbl.addWidget(self.swapper['P'])
        self.setLayout(self.hbl)
        self.swapper['P'].hide()
        #self.vbl = QtGui.QVBoxLayout()
        #self.vbl.addWidget(self.canvas)
        #self.setLayout(self.vbl)

    def set_data(self, data):
        self.canvas.pm.set_array(data[:-1, :-1].ravel())
        self.canvas.fig.canvas.draw()
