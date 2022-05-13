from ScopeFoundry.measurement import Measurement
from qtpy import QtCore, QtWidgets
import pyqtgraph as pg


class ZWOCameraCaptureMeasure(Measurement):    

    name = 'zwo_camera_capture'

    def setup(self):
        self.settings.New('live_img', dtype=bool)
        self.settings.New('rotate', dtype=bool)
        
        self.add_operation('clear_and_plot', self.clear_and_plot)
        
        self.settings.live_img.add_listener(self.on_toggle_live_img)



    def setup_figure(self):
        
        self.ui = QtWidgets.QWidget()
        self.ui_layout = QtWidgets.QGridLayout()
        self.ui.setLayout(self.ui_layout)
        
        self.ui_settings = self.settings.New_UI()
        self.ui_layout.addWidget(self.ui_settings, 0,0)
        self.ui_cam_settings= self.app.hardware['zwo_camera'].settings.New_UI()
        self.ui_layout.addWidget(self.ui_cam_settings,1,0)
    
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.graph_layout.clear()
        self.ui_layout.addWidget(self.graph_layout, 0,1,2,1)
        
        self.live_img_update_timer = QtCore.QTimer(self)
        self.live_img_update_timer.timeout.connect(self._on_live_img_timer)        
        self.live_img_update_timer.start(100)
        
        self.ui_layout.setColumnStretch(1, 1)
        self.clear_and_plot()
        
    def on_toggle_live_img(self):
        cam = self.app.hardware['zwo_camera']
        if self.settings['live_img']:
            cam.camera.start_video_capture()
        else:
            cam.camera.stop_video_capture()
        
    def _on_live_img_timer(self):
        if self.settings['live_img']:
            cam = self.app.hardware['zwo_camera']
            im  = cam.camera.capture_video_frame()
            if self.settings['rotate']:
                im = im.swapaxes(0,1)
            self.live_img_item.setImage(image=im, 
                                        autoLevels=False)
            scale = 1
            center_x = 50
            center_y = 50
            im_aspect = im.shape[1]/im.shape[0]
            self.img_rect = pg.QtCore.QRectF(0 - center_x * scale / 100,
                                0 - center_y * scale * im_aspect / 100,
                                scale,
                                scale * im_aspect)
            self.live_img_item.setRect(self.img_rect)

            #print(cam.camera.get_dropped_frames())
                # # get rectangle
                # im_aspect = im.shape[1]/im.shape[0]
                # stageS = self.app.hardware["mcl_xyz_stage"].settings
                # x,y,z =  stageS["x_position"]*1e-6, stageS["y_position"]*1e-6, stageS["z_position"]*1e-6
                #
                # scale = self.settings['img_scale']
                # S = self.settings
                # rect= pg.QtCore.QRectF(x - S['img_center_x'] * scale / 100,
                #                         y - S['img_center_y'] * scale * im_aspect / 100,
                #                         scale,
                #                         scale * im_aspect)
                # self.live_img_item.setRect(rect)


    def clear_and_plot(self):
        #scale = self.settings['scale'] # m/V
        
        self.graph_layout.clear()

        self.xy_plot = self.graph_layout.addPlot(0,0)
        self.xy_plot.setAspectLocked(lock=True, ratio=1)
        self.xy_plot.setLabels(left=('mcl y', 'm'), bottom=('mcl x', 'm'))
        self.live_img_item = pg.ImageItem()
        self.xy_plot.addItem(self.live_img_item)
        
        self.xy_plot.addItem(pg.InfiniteLine(angle=0))
        self.xy_plot.addItem(pg.InfiniteLine(angle=90))
       