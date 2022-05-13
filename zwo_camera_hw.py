from ScopeFoundry import HardwareComponent
from qtpy import QtCore
import os

class ZWOCameraHW(HardwareComponent):
    
    name ='zwo_camera'
    

    def setup(self):    
        S = self.settings
        S.New('cam_id', dtype=int, initial=0)
        S.New('name', dtype=str, ro=True)
        S.New('img_type', dtype=str, choices=self.img_types.keys())
        S.New('live_update', dtype=bool, initial=True)
        S.New('live_update_period', dtype=int, unit='ms', initial=100)
        
        for c in self.possible_controls.values():
            S.New(c['Name'],
                  dtype=int,
                  initial = c['DefaultValue'],
                  vmin = c['MinValue'],
                  vmax = c['MaxValue'],
                  description=c['Description'],
                  ro = not c['IsWritable'])
            if c['IsAutoSupported']:
                S.New(c['Name']+"_auto", dtype=bool)
        
        self.live_update_timer = QtCore.QTimer(self)
        self.live_update_timer.timeout.connect(self.on_live_update_timer)        
        self.live_update_timer.start(100)
        S.live_update_period.add_listener(self.on_new_live_update_period)

    def on_new_live_update_period(self):
        #print("asdf")
        self.live_update_timer.setInterval(
            self.settings['live_update_period'])
        
    def on_live_update_timer(self):
        S = self.settings
        if S['connected'] and S['live_update']:
            self.read_from_hardware()
    
    def connect(self):
        import zwoasi
        
        if zwoasi.zwolib is None:
            zwoasi.init(os.path.dirname(__file__) + "/ASI_linux_mac_SDK_V1.22/lib/mac/libASICamera2.dylib")
        
        S = self.settings


        print(zwoasi.get_num_cameras())
        
        print(zwoasi.list_cameras())
        
        self.camera = cam = zwoasi.Camera(S['cam_id'])
        
        self.cam_props = cam.get_camera_property()
        print(self.cam_props)
        
        S['name'] = self.cam_props['Name']
        
        
        S.img_type.connect_to_hardware(
            write_func = self.set_img_type)
        
        
        self.controls = cam.get_controls()
        
        for c in self.controls.values():
            
            lq = S.get_lq(c['Name'])
            lq.change_readonly(not c['IsWritable'])
            lq.change_min_max(
                vmin = c['MinValue'],
                vmax = c['MaxValue'])
            
            def read_func(c=c):
                value,auto = self.camera.get_control_value(c['ControlType'])
                #print("read", c['Name'], value,auto)
                return value
            def write_func(x, c=c):
                #print("write", c['Name'], x)
                self.camera.set_control_value(c['ControlType'], x)
            lq.connect_to_hardware(
                read_func = read_func,
                write_func = write_func
                )
            if c['IsAutoSupported']:
                #print(c['Name'], "auto supported")
                lq_auto = S.get_lq(c['Name']+"_auto")
                def read_func(c=c):
                    value,auto = self.camera.get_control_value(c['ControlType'])
                    return auto
                def write_func(auto,c=c):
                    self.camera.set_control_value(c['ControlType'], self.settings[c['Name']], auto)
                lq_auto.connect_to_hardware(
                    read_func = read_func,
                    write_func = write_func
                    )
                
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'camera'):
            self.camera.close()
    
    
    
    
    def set_img_type(self,imtype):
        type_id = self.img_types[imtype]
        self.camera.set_image_type(type_id)
    
    img_types = {
        'RAW8' : 0,
        'RGB24' : 1,
        'RAW16' : 2,
        'Y8' : 3,
        }    

    possible_controls = {
         'Gain': {'Name': 'Gain',
          'Description': 'Gain',
          'MaxValue': 600,
          'MinValue': 0,
          'DefaultValue': 0,
          'IsAutoSupported': True,
          'IsWritable': True,
          'ControlType': 0},
         'Exposure': {'Name': 'Exposure',
          'Description': 'Exposure Time(us)',
          'MaxValue': 2000000000,
          'MinValue': 32,
          'DefaultValue': 10000,
          'IsAutoSupported': True,
          'IsWritable': True,
          'ControlType': 1},
         'WB_R': {'Name': 'WB_R',
          'Description': 'White balance: Red component',
          'MaxValue': 99,
          'MinValue': 1,
          'DefaultValue': 60,
          'IsAutoSupported': True,
          'IsWritable': True,
          'ControlType': 3},
         'WB_B': {'Name': 'WB_B',
          'Description': 'White balance: Blue component',
          'MaxValue': 99,
          'MinValue': 1,
          'DefaultValue': 99,
          'IsAutoSupported': True,
          'IsWritable': True,
          'ControlType': 4},
         'Offset': {'Name': 'Offset',
          'Description': 'offset',
          'MaxValue': 80,
          'MinValue': 0,
          'DefaultValue': 8,
          'IsAutoSupported': False,
          'IsWritable': True,
          'ControlType': 5},
         'BandWidth': {'Name': 'BandWidth',
          'Description': 'The total data transfer rate percentage',
          'MaxValue': 100,
          'MinValue': 40,
          'DefaultValue': 50,
          'IsAutoSupported': True,
          'IsWritable': True,
          'ControlType': 6},
         'Flip': {'Name': 'Flip',
          'Description': 'Flip: 0->None 1->Horiz 2->Vert 3->Both',
          'MaxValue': 3,
          'MinValue': 0,
          'DefaultValue': 0,
          'IsAutoSupported': False,
          'IsWritable': True,
          'ControlType': 9},
         'AutoExpMaxGain': {'Name': 'AutoExpMaxGain',
          'Description': 'Auto exposure maximum gain value',
          'MaxValue': 600,
          'MinValue': 0,
          'DefaultValue': 300,
          'IsAutoSupported': False,
          'IsWritable': True,
          'ControlType': 10},
         'AutoExpMaxExpMS': {'Name': 'AutoExpMaxExpMS',
          'Description': 'Auto exposure maximum exposure value(unit ms)',
          'MaxValue': 60000,
          'MinValue': 1,
          'DefaultValue': 100,
          'IsAutoSupported': False,
          'IsWritable': True,
          'ControlType': 11},
         'AutoExpTargetBrightness': {'Name': 'AutoExpTargetBrightness',
          'Description': 'Auto exposure target brightness value',
          'MaxValue': 160,
          'MinValue': 50,
          'DefaultValue': 100,
          'IsAutoSupported': False,
          'IsWritable': True,
          'ControlType': 12},
         'HardwareBin': {'Name': 'HardwareBin',
          'Description': 'Is hardware bin2:0->No 1->Yes',
          'MaxValue': 1,
          'MinValue': 0,
          'DefaultValue': 0,
          'IsAutoSupported': False,
          'IsWritable': True,
          'ControlType': 13},
         'MonoBin': {'Name': 'MonoBin',
          'Description': 'bin R G G B to one pixel for color camera, color will loss',
          'MaxValue': 1,
          'MinValue': 0,
          'DefaultValue': 0,
          'IsAutoSupported': False,
          'IsWritable': True,
          'ControlType': 18},
         'Temperature': {'Name': 'Temperature',
          'Description': 'Sensor temperature(degrees Celsius)',
          'MaxValue': 1000,
          'MinValue': -500,
          'DefaultValue': 20,
          'IsAutoSupported': False,
          'IsWritable': False,
          'ControlType': 8},
         'CoolPowerPerc': {'Name': 'CoolPowerPerc',
          'Description': 'Cooler power percent',
          'MaxValue': 100,
          'MinValue': 0,
          'DefaultValue': 0,
          'IsAutoSupported': False,
          'IsWritable': False,
          'ControlType': 15},
         'TargetTemp': {'Name': 'TargetTemp',
          'Description': 'Target temperature(cool camera only)',
          'MaxValue': 30,
          'MinValue': -40,
          'DefaultValue': 0,
          'IsAutoSupported': False,
          'IsWritable': True,
          'ControlType': 16},
         'CoolerOn': {'Name': 'CoolerOn',
          'Description': 'turn on/off cooler(cool camera only)',
          'MaxValue': 1,
          'MinValue': 0,
          'DefaultValue': 0,
          'IsAutoSupported': False,
          'IsWritable': True,
          'ControlType': 17},
         'AntiDewHeater': {'Name': 'AntiDewHeater',
          'Description': 'turn on/off anti dew heater(cool camera only)',
          'MaxValue': 1,
          'MinValue': 0,
          'DefaultValue': 0,
          'IsAutoSupported': False,
          'IsWritable': True,
          'ControlType': 21}}