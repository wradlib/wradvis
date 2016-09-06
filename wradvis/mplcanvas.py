# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016, wradlib Development Team. All Rights Reserved.
# Distributed under the MIT License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
#!/usr/bin/env python


import numpy as np
import matplotlib
matplotlib.use('Qt4Agg')


from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.cm import get_cmap
from mpl_toolkits.axes_grid1 import make_axes_locatable

from wradvis import utils

class MplCanvas(FigureCanvas):

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
        # add colorbar and title
        # we use LogLocator for colorbar
        self.cbar = self.fig.colorbar(self.pm, cax=cax)
        self.ax.set_aspect('equal')
        self.ax.set_xlim([grid[..., 0].min(), grid[..., 0].max()])
        self.ax.set_ylim([grid[..., 1].min(), grid[..., 1].max()])


class MplWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.canvas = MplCanvas()
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)

    def set_data(self, data):
        self.canvas.pm.set_array(data[:-1, :-1].ravel())
        self.canvas.fig.canvas.draw()
