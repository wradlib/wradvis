# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016, wradlib Development Team. All Rights Reserved.
# Distributed under the MIT License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
#!/usr/bin/env python

import numpy as np

from vispy.scene import SceneCanvas
from vispy.util.event import EventEmitter
from vispy.visuals.transforms import STTransform
from vispy.scene.cameras import PanZoomCamera
from vispy.scene.visuals import Image, ColorBar, Markers, Text
from vispy.geometry import Rect

from wradvis import utils
from wradvis.config import conf


class ColorbarCanvas(SceneCanvas):

    def __init__(self, **kwargs):
        super(ColorbarCanvas, self).__init__(keys='interactive', **kwargs)

        # set size ov Canvas
        self.size = 50, 450

        # unfreeze needed to add more elements
        self.unfreeze()

        # add grid central widget
        self.grid = self.central_widget.add_grid()

        # add view to grid
        self.view = self.grid.add_view(row=0, col=0)
        self.view.border_color = (0.5, 0.5, 0.5, 1)

        # initialize colormap, we take cubehelix for now
        # this is the most nice colormap for radar in vispy
        cmap = 'cubehelix'

        # initialize ColorBar Visual, add to view
        self.cbar = ColorBar(center_pos=(0, 10),
                             size=np.array([400, 20]),
                             cmap=cmap,
                             clim=(0, 255),
                             label_str='measurement units',
                             orientation='right',
                             border_width=1,
                             border_color='white',
                             parent=self.view.scene)

        # add transform to Colorbar
        self.cbar.transform = STTransform(scale=(1, 1, 1),
                                          translate=(20, 250, 0.5))

        # whiten label and ticks
        self.cbar.label.color = 'white'
        for tick in self.cbar.ticks:
            tick.color = 'white'

        self.freeze()


class RadolanCanvas(SceneCanvas):

    def __init__(self, **kwargs):
        super(RadolanCanvas, self).__init__(keys='interactive', **kwargs)

        # set size ov Canvas
        self.size = 450, 450

        # unfreeze needed to add more elements
        self.unfreeze()

        # add grid central widget
        self.grid = self.central_widget.add_grid()

        # add view to grid
        self.view = self.grid.add_view(row=0, col=0)
        self.view.border_color = (0.5, 0.5, 0.5, 1)

        # add signal emitters
        self.mouse_moved = EventEmitter(source=self, type="mouse_moved")

        # block double clicks
        self.events.mouse_double_click.block()

        # initialize empty RADOLAN image
        img_data = np.zeros((900, 900))

        # initialize colormap, we take cubehelix for now
        # this is the most nice colormap for radar in vispy
        cmap = 'cubehelix'

        # initialize Image Visual with img_data
        # add to view
        self.image = Image(img_data,
                           method='subdivide',
                           #interpolation='bicubic',
                           cmap=cmap,
                           clim=(0,50),
                           parent=self.view.scene)

        # add transform to Image
        # (mostly positioning within canvas)
        self.image.transform = STTransform(translate=(0, 0, 0))

        # get radolan ll point coodinate into self.r0
        self.r0 = utils.get_radolan_origin()

        # create cities (Markers and Text Visuals
        self.create_cities()

        # create PanZoomCamera
        self.cam = PanZoomCamera(name="PanZoom",
                                 rect=Rect(0, 0, 900, 900),
                                 aspect=1,
                                 parent=self.view.scene)

        self.view.camera = self.cam

        self._mouse_position = None
        self.freeze()
        # print FPS to console, vispy SceneCanvas internal function
        self.measure_fps()

    def create_cities(self):
        # initialize city markers
        self.markers = Markers(parent=self.view.scene)
        # move z-direction a bit negative (means nearer to the viewer)
        self.markers.transform = STTransform(translate=(0, 0, -10))

        cities = utils.get_cities_coords()
        cnameList = []
        ccoordList = []
        for k, v in cities.items():
            cnameList.append(k)
            ccoordList.append(v)
        ccoord = np.vstack(ccoordList)
        ccoord = utils.wgs84_to_radolan(ccoord)
        pos_scene = np.zeros((ccoord.shape[0], 2), dtype=np.float32)
        pos_scene[:] = ccoord - self.r0

        # initialize Markers
        self.markers.set_data(pos=pos_scene,
                              symbol="disc",
                              edge_color="blue",
                              face_color='red',
                              size=10)

        # initialize Markertext
        self.text = Text(text=cnameList,
                         pos=pos_scene,
                         font_size=15,
                         anchor_x = 'right',
                         anchor_y = 'top',
                         parent=self.view.scene)

    def on_mouse_move(self, event):
        point = self.scene.node_transform(self.image).map(event.pos)[:2]
        self._mouse_position = point
        # emit signal
        self.mouse_moved()




