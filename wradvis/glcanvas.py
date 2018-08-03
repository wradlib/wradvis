#!/usr/bin/env python
# Copyright (c) 2016-2018, wradlib developers.
# Distributed under the MIT License. See LICENSE.txt for more info.

import numpy as np

from PyQt5 import QtCore
from PyQt5.QtWidgets import (QSplitter, QWidget, QHBoxLayout)

from vispy.scene import SceneCanvas
from vispy.util.event import EventEmitter
from vispy.visuals.transforms import STTransform, MatrixTransform, PolarTransform
from vispy.scene.cameras import PanZoomCamera
from vispy.scene.visuals import Image, ColorBar, Markers, Text, Line, InfiniteLine
from vispy.scene.widgets import Label, AxisWidget
from vispy.geometry import Rect
from vispy.color import Color

from wradvis import utils
from wradvis.config import conf


class GlCanvas(SceneCanvas):
    def __init__(self, vrow=0, vcol=0, **kwargs):
        super(GlCanvas, self).__init__(**kwargs)

        self.unfreeze()
        self.grid = self.central_widget.add_grid(margin=10)
        self.grid.spacing = 0
        self.view = self.grid.add_view(row=vrow, col=vcol,
                                       border_color='white')

        self.transitem = None
        self.cursor = None

        self._mouse_position = None
        self._mouse_press_position = (0, 0)
        self._cursor_position = None
        self._cursor_press_position = (0, 0)

        self.mouse_double_clicked = EventEmitter(source=self,
                                                 type="mouse_double_clicked")
        self.mouse_moved = EventEmitter(source=self, type="mouse_moved")
        self.mouse_pressed = EventEmitter(source=self, type="mouse_pressed")
        self.key_pressed = EventEmitter(source=self, type="key_pressed")

        self.freeze()

    def on_mouse_double_click(self, event):
        point = self.scene.node_transform(self.transitem).map(event.pos)[:2]
        self._mouse_position = point
        # emit signal
        self.mouse_double_clicked(event)

    def on_key_press(self, event):
        self.key_pressed(event)

    def on_mouse_move(self, event):
        point = self.scene.node_transform(self.transitem).map(event.pos)[:2]
        cursor = self.scene.node_transform(self.cursor).map(event.pos)[:2]
        self._mouse_position = point
        self._cursor_position = cursor
        self.update_cursor()
        self.mouse_moved(event)

    def on_mouse_press(self, event):
        point = self.scene.node_transform(self.transitem).map(event.pos)[:2]
        cursor = self.scene.node_transform(self.cursor).map(event.pos)[:2]
        self._mouse_press_position = point
        self._cursor_press_position = cursor
        self.update_select_cursor()
        self.mouse_pressed(event)

    def add_cursor(self):
        # cursor lines
        self.vline = InfiniteLine(parent=self.view.scene,
                                  color=Color("blue").RGBA)
        self.vline.transform = STTransform(
            translate=(0, 0, -10))
        self.hline = InfiniteLine(parent=self.view.scene,
                                  color=Color("blue").RGBA,
                                  vertical=False)
        self.hline.transform = STTransform(
            translate=(0, 0, -10))
        self.vline.visible = False
        self.hline.visible = False

        self.cursor = self.hline

        # pick lines
        self.vpline = InfiniteLine(parent=self.view.scene,
                                   color=Color("red").RGBA)
        self.vpline.transform = STTransform(
            translate=(0, 0, -5))
        self.hpline = InfiniteLine(parent=self.view.scene,
                                   color=Color("red").RGBA,
                                   vertical=False)
        self.hpline.transform = STTransform(
            translate=(0, 0, -5))
        self.vpline.visible = False
        self.hpline.visible = False

    def update_cursor(self):
        pos = self._cursor_position
        self.vline.set_data(pos=pos[0])
        self.hline.set_data(pos=pos[1])
        # needed to work, set_data doesn't update by itself
        self.update()

    def update_select_cursor(self):
        pos = self._cursor_press_position
        self.vpline.set_data(pos[0])
        self.hpline.set_data(pos[1])
        self.update()


class AxisCanvas(GlCanvas):
    def __init__(self, **kwargs):
        super(AxisCanvas, self).__init__(**kwargs)

        self.size = 450, 200
        self.unfreeze()

        self.pl_title = Label("Time Graph", color='white')
        self.pl_title.height_max = 25
        self.grid.add_widget(self.pl_title, row=0, col=0, col_span=3)

        self.yaxis = AxisWidget(orientation='left')
        self.yaxis.width_max = 25
        self.grid.add_widget(self.yaxis, row=1, col=1)

        self.ylabel = Label('Units', rotation=-90, color='white')
        self.ylabel.width_max = 25
        self.grid.add_widget(self.ylabel, row=1, col=0)

        self.xaxis = AxisWidget(orientation='bottom')
        self.xaxis.height_max = 25
        self.grid.add_widget(self.xaxis, row=2, col=2)

        self.xlabel = Label('Time', color='white')
        self.xlabel.height_max = 25
        self.grid.add_widget(self.xlabel, row=3, col=0, col_span=3)

        self.right_padding = self.grid.add_widget(row=0, col=3, row_span=3)
        self.right_padding.width_max = 30

        self.add_cursor()

        self.cam = PanZoomCamera(name="PanZoom",
                                 #rect=Rect(0, 0, 900, 900),
                                 #aspect=1,
                                 parent=self.view.scene)
        # data line
        self.plot = Line(parent=self.view.scene)
        self.plot.transform = STTransform(
            translate=(0, 0, -2.5))

        self.transitem = self.plot

        # cursors
        self.low_line = InfiniteLine(parent=self.view.scene, color=Color("blue").RGBA)
        self.low_line.transform = STTransform(
            translate=(0, 0, -2.5))
        self.high_line = InfiniteLine(parent=self.view.scene, color=Color("blue").RGBA)
        self.high_line.transform = STTransform(
            translate=(0, 0, -2.5))
        self.cur_line = InfiniteLine(parent=self.view.scene,
                                      color=Color("red").RGBA)
        self.cur_line.transform = STTransform(
            translate=(0, 0, -2.5))

        self.view.camera = self.cam

        self.xaxis.link_view(self.view)
        self.yaxis.link_view(self.view)

        self.freeze()


class ColorbarCanvas(GlCanvas):
    def __init__(self, **kwargs):
        super(ColorbarCanvas, self).__init__(keys='interactive', **kwargs)

        # set size ov Canvas
        self.size = 60, 450

        # unfreeze needed to add more elements
        self.unfreeze()

        self.events.mouse_move.block()
        self.events.mouse_press.block()
        self.events.mouse_double_click.block()

        self.view.border_color = (0.5, 0.5, 0.5, 1)

        # initialize colormap, we take cubehelix for now
        # this is the most nice colormap for radar in vispy
        cmap = 'cubehelix'

        # initialize ColorBar Visual, add to view
        self.cbar = ColorBar(center_pos=(0, 10),
                             size=np.array([400, 20]),
                             cmap=cmap,
                             clim=(conf["vis"]["cmin"], conf["vis"]["cmax"]),
                             label_str='measurement units',
                             orientation='right',
                             border_width=1,
                             border_color='white',
                             parent=self.view.scene)

        # add transform to Colorbar
        self.cbar.transform = STTransform(scale=(1, 1, 1),
                                          translate=(20, 225, 0.5))

        # whiten label and ticks
        self.cbar.label.color = 'white'
        for tick in self.cbar.ticks:
            tick.color = 'white'

        self.freeze()


class RadolanCanvas(GlCanvas):
    def __init__(self, **kwargs):
        super(RadolanCanvas, self).__init__(keys='interactive', **kwargs)

        # set size ov Canvas
        self.size = 450, 450

        # unfreeze needed to add more elements
        self.unfreeze()

        # block double clicks
        self.events.mouse_double_click.block()

        # initialize empty RADOLAN image
        img_data = np.zeros((900, 900))

        # initialize colormap, we take cubehelix for now
        # this is the most nice colormap for radar in vispy
        cmap = 'cubehelix'

        self.images = []
        # initialize Image Visual with img_data
        # add to view
        self.image = Image(img_data,
                           method='subdivide',
                           #interpolation='bicubic',
                           cmap=cmap,
                           clim=(0,50),
                           parent=self.view.scene)

        self.transitem = self.image

        self.images.append(self.image)

        # add transform to Image
        # (mostly positioning within canvas)
        self.image.transform = STTransform(translate=(0, 0, 0))

        # get radolan ll point coodinate into self.r0
        self.r0 = utils.get_radolan_origin()

        # create cities (Markers and Text Visuals
        self.create_cities()

        # cursor lines
        self.add_cursor()

        # create PanZoomCamera
        self.cam = PanZoomCamera(name="PanZoom",
                                 rect=Rect(0, 0, 900, 900),
                                 aspect=1,
                                 parent=self.view.scene)

        self.view.camera = self.cam

        self.freeze()
        # print FPS to console, vispy SceneCanvas internal function
        self.measure_fps()

    def create_marker(self, id, pos, name):
        marker = Markers(parent=self.view.scene)
        marker.transform = STTransform(translate=(0, 0, -10))
        marker.interactive = True

        # add id
        marker.unfreeze()
        marker.id = id
        marker.freeze()

        marker.set_data(pos=pos[np.newaxis],
                        symbol="disc",
                        edge_color="blue",
                        face_color='red',
                        size=10)

        # initialize Markertext
        text = Text(text=name,
                    pos=pos,
                    font_size=15,
                    anchor_x='right',
                    anchor_y='top',
                    parent=self.view.scene)

        return marker, text

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
        pos_scene = np.zeros((ccoord.shape[0], 2), dtype=np.float32)
        pos_scene[:] = ccoord - self.r0

        # initialize Markers
        self.markers = []
        self.text = []
        i = 0
        for p, n in zip(pos_scene, cnameList):
            m, t = self.create_marker(i, p, n)
            self.markers.append(m)
            self.text.append(t)
            i += 1

    def on_mouse_press(self, event):
        super(RadolanCanvas, self).on_mouse_press(event)

        self.view.interactive = False

        for v in self.visuals_at(event.pos, radius=30):
            if isinstance(v, Markers):
                if self.selected is None:
                    self.selected = v
                    self.selected.symbol = 'star'
                else:
                    self.selected.symbol = 'disc'
                    if self.selected.id == v.id:
                        self.selected = None
                    else:
                        self.selected = v
                        self.selected.symbol = 'star'

        self.view.interactive = True


class PTransform(PolarTransform):
    glsl_imap = """
        vec4 polar_transform_map(vec4 pos) {
            float theta = atan(radians(pos.x), radians(pos.y));
            theta = degrees(theta + 3.14159265358979323846);
            float r = length(pos.xy);
            return vec4(r, theta, pos.z, 1);
        }
        """

    def imap(self, coords):
        coords = np.array(coords)
        ret = np.empty(coords.shape, coords.dtype)
        ret[..., 0] = np.rad2deg(np.arctan2(coords[..., 0],
                                            coords[..., 1]) + np.pi)
        ret[..., 1] = (coords[..., 0] ** 2 + coords[..., 1] ** 2) ** 0.5
        for i in range(2, coords.shape[-1]):
            ret[..., i] = coords[..., i]
        return ret


class PolarImage(Image):
    def __init__(self, source=None, **kwargs):
        super(PolarImage, self).__init__(**kwargs)

        self.unfreeze()

        # source should be an object, which contains information about
        # a specific radar source
        self.source = source

        # source should contain the radar coordinates in some usable format
        # here I assume offset from lower left (0,0)
        if source is not None:
            xoff = source['X']
            yoff = source['Y']
        else:
            xoff = 0
            yoff = 0

        # this takes the image sizes and uses it for transformation
        self.theta = self._data.shape[0]
        self.range = self._data.shape[1]

        # PTransform takes care of making PPI from data array
        # rot rotates the ppi 180 deg (image origin is upper left)
        # the translation moves the image to centere the ppi
        rot = MatrixTransform()
        rot.rotate(180, (0, 0, 1))
        self.transform = (STTransform(translate=(self.range+xoff,
                                                 self.range+yoff, 0)) *
                          rot *
                          PTransform())
        self.freeze()


class DXCanvas(GlCanvas):
    def __init__(self, **kwargs):
        super(DXCanvas, self).__init__(keys='interactive', **kwargs)

        self.size = 450, 450
        self.unfreeze()

        # This is hardcoded now, but maybe handled as the data source changes
        self.img_data = np.zeros((360, 128))

        # initialize colormap, we take cubehelix for now
        # this is the most nice colormap for radar in vispy
        cmap = 'cubehelix'

        # this way we can hold several images on the same scene
        # usable for radar mosaic
        self.images = []
        self.image = PolarImage(source=None,
                                data=self.img_data,
                                method='impostor',
                                # interpolation='bicubic',
                                cmap=cmap,
                                clim=(-32.5, 95),
                                parent=self.view.scene)

        self.transitem = self.image

        self.images.append(self.image)

        # cursor lines
        self.add_cursor()

        # block double clicks
        self.events.mouse_double_click.block()

        # create PanZoomCamera
        # the camera should zoom to the ppi "bounding box"
        self.cam = PanZoomCamera(name="PanZoom",
                                 rect=Rect(0, 0, 256, 256),
                                 aspect=1,
                                 parent=self.view.scene)

        self.view.camera = self.cam

        self.freeze()
        self.measure_fps()

    def add_image(self, radar):
        # this adds an image to the images list
        image = PolarImage(source=radar,
                           data=self.img_data,
                           method='impostor',
                           # interpolation='bicubic',
                           cmap='cubehelix',
                           clim=(-32.5, 95),
                           parent=self.view.scene)
        self.images.append(image)


class RadolanWidget(QWidget):
    def __init__(self, parent=None):
        super(RadolanWidget, self).__init__(parent)
        self.parent = parent
        self.rcanvas = RadolanCanvas()
        self.rcanvas.create_native()
        self.rcanvas.native.setParent(self)
        self.pcanvas = DXCanvas()
        self.pcanvas.create_native()
        self.pcanvas.native.setParent(self)
        self.cbar = ColorbarCanvas()
        self.cbar.create_native()
        self.cbar.native.setParent(self)

        self.canvas = self.rcanvas

        # canvas swapper
        self.swapper = {}
        self.swapper['R'] = self.rcanvas.native
        self.swapper['P'] = self.pcanvas.native

        self.splitter = QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.swapper['R'])
        self.splitter.addWidget(self.swapper['P'])
        self.swapper['P'].hide()
        self.splitter.addWidget(self.cbar.native)

        # stretchfactors for correct splitter behaviour
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        self.hbl = QHBoxLayout()
        self.hbl.addWidget(self.splitter)
        self.setLayout(self.hbl)

    def connect_signals(self):
        self.parent.mediabox.signal_time_slider_changed.connect(self.set_time)
        self.parent.mousebox.signal_toggle_Cursor.connect(self.toggle_cursor)

    def set_canvas(self, type):
        if type == 'DX':
            self.canvas = self.pcanvas
            self.swapper['P'].show()
            self.swapper['R'].hide()
        else:
            self.canvas = self.rcanvas
            self.swapper['R'].show()
            self.swapper['P'].hide()

    def set_time(self, pos):
        # now this sets same data to all images
        # we would need to do the data loading
        # via objects (maybe radar-object from above)
        # and use
        for im in self.canvas.images:
            im.set_data(self.parent.props.mem.variables['data'][pos][:])
        self.canvas.update()

    def set_data(self, data):
        # now this sets same data to all images
        # we would need to do the data loading
        # via objects (maybe radar-object from above)
        # and use
        for im in self.canvas.images:
            im.set_data(data)
        self.canvas.update()

    def set_clim(self, clim):
        self.canvas.image.clim = clim
        self.cbar.cbar.clim = clim

    def toggle_cursor(self, state):
        self.canvas.hline.visible = state
        self.canvas.vline.visible = state
        self.canvas.hpline.visible = state
        self.canvas.vpline.visible = state
        self.canvas.update()


class RadolanLineWidget(QWidget):

    #signal_mouse_double_clicked = QtCore.pyqtSignal(int, name='mouseDblClicked')

    def __init__(self, parent=None):
        super(RadolanLineWidget, self).__init__(parent)
        self.parent = parent
        self.canvas = AxisCanvas(vrow=1, vcol=2)
        self.canvas.create_native()
        self.canvas.native.setParent(self)
        self.hbl = QHBoxLayout()
        self.hbl.addWidget(self.canvas.native)
        self.setLayout(self.hbl)

    def sizeHint(self):
        return QtCore.QSize(650, 200)

    def connect_signals(self):
        self.parent.parent.iwidget.rcanvas.mouse_pressed.connect(self.set_line)
        self.parent.parent.iwidget.pcanvas.mouse_pressed.connect(self.set_line)
        self.parent.parent.mediabox.signal_time_properties_changed.connect(self.set_time_limits)
        #self.canvas.mouse_double_clicked(self.mouse_double_clicked)

    def set_line(self, event):
        pos = self.parent.parent.iwidget.canvas._mouse_press_position

        if self.parent.props.mem.variables['data'].source in ['DX']:
            y = self.parent.props.mem.variables['data'][:, int(pos[0]), int(pos[1])]
        else:
            y = self.parent.props.mem.variables['data'][:, int(pos[1]), int(pos[0])]
        x = np.arange(len(y))
        try:
            self.plot.parent = None
        except:
            pass
        self.plot = Line(np.squeeze(np.dstack((x, y))), parent=self.canvas.view.scene)
        self.plot.transform = STTransform(
            translate=(0, 0, -2.5))
        self.set_time_limits()

    def set_time_limits(self):
        low = self.parent.parent.mediabox.range.low()
        high = self.parent.parent.mediabox.range.high()
        cur = self.parent.parent.mediabox.time_slider.value()

        self.canvas.low_line.set_data(low)
        self.canvas.high_line.set_data(high)
        self.canvas.cur_line.set_data(cur)
        self.canvas.cam.set_range(margin=0.)

    #def mouse_double_clicked(self):
    #    self.signal_mouse_double_clicked.emit(self.canvas._mouse_position)

