"""
This recipe is used for the MOL experiment

V02 has standarized the camera trigger functions and added label iterator class
V03 has 
    -- moved the Waveform and Label_iterator to separate modules and now imports
       them.
    -- organized the methods and added documentation
V04 -- change Li AOM methods for the new setup using the TA's
    -- change mot coil on/off methods to enabled/disabled
    -- add limit to mot coil amps
V05 -- added set_Rb85_pump_ramped_dF method + support(Will)
       and added Li pump/repump modulation functions for loading (bruce)
"""
from UTBus1 import AnalogOutput, DigitalOutput, DDS
from UTBus1 import Recipe
from UTBus1.Globals import lock_DDS_params,Hz,MHz,GHz,kHz,COMPCOIL_COVERSION_V_PER_A,zeeman_coil_current_calib
from Database import experiment_devices
import numpy 
from waveform import Waveform
from label_iterator import Label_iterator
import serial
from struct import pack
from scipy.special import erf,erfinv
from numpy import isinf,clip
import os
import sys
sys.path.insert(0, 'C:\UTBus_Recipesb\public_scripts')
from debugger import debug
D = dict(
    Li_pump_DP_ampl_max = 0.24,#sets double pass AOM amp for max value
    Li_repump_DP_ampl_max = 0.15,#same for repump AOM
    Default_MOT_Coil_ON_Current_A = 4.0,
    Default_MOT_Coil_OFF_Current_A = 0.0,
    phaseDetectorSetting_xN = 5,    #something for the microwave methods but unclear what.
    )

class MOLExperimentRecipe(Recipe):
    """
    Modified recipe class specific to the Molecule experiment: organized by
    -- initialization methods or properties
    -- general misc methods or properties
    -- camera methods or properties
    -- Li  methods or properties
    -- general Rb methods or properties (same for both isotopes)
    -- Rb85 methods or properties
    -- Rb87 methods or properties
    -- coil methods or properties
    -- IPG methods or properties
    -- SPI methods or properties
    -- PA methods or properties
    -- Rb state selection (SS) methods or properties
    -- RF methods or properties
    """

    ###################################################################################
    ## initialization methods or properties
    ###################################################################################
    def __init__(self,recipe_name,**kw):
        print '================================================'
        print 'MOL Experiment Recipe: ',os.path.basename(__file__)
        print '================================================'
        _D = experiment_devices['MOL']
        self.__devices = {}
        for (name,addr) in _D['DDS'].items():
            self.__devices[addr] = d = DDS(address=addr)
            setattr(self,name,d)
        
        for (name,addr) in _D['AO'].items():
            self.__devices[addr] = d = AnalogOutput(address=addr)
            setattr(self,name,d)
        
        for (name,data) in _D['DO'].items():
            (addr,port) = data
            if not addr in self.__devices:
                self.__devices[addr] = d = DigitalOutput(address=addr)
            setattr(self,name,self.__build_DO_method(name,addr,port))

        for (name,parms) in _D['MC'].items():
            parms = parms.copy()
            cls_name = parms.pop('cls')
            _temp = __import__('UTBus1.MC',globals(),locals(),[cls_name],-1)
            cls = getattr(_temp,cls_name)
            obj = cls(**parms)
            setattr(self,'MC_' + name,obj)

        Recipe.__init__(self,recipe_name,**kw)
        self.__Li_pump_dF = None
        self.__Li_repump_dF = None
        
    def __build_DO_method(self,name,addr,port):
        def DO_method(v):
            self.__devices[addr].set_bit(port,v)
        DO_method.func_name = name
        return DO_method

    def start(self):
        '''
        initializes certain parameters (labels and counters) and starts collecting 
        recipe commands until the end command.
        '''
        self.labels = Label_iterator()
        self.pixelinkLabels = Label_iterator('pixelink_image')
        self.apogeeLabels = Label_iterator('apogee_image')
        self.pointgreyLabels = Label_iterator('pointgrey_image')
        self.__pixelink_triggers = 0
        self.__apogee_triggers = 0
        self.__pointgrey_triggers = 0
        Recipe.start(self)
  

    ###################################################################################
    ## general misc methods or properties and shutters
    ###################################################################################
        
    def atom_shutter_open(self):
        self.atom_shutter(1)

    def atom_shutter_close(self):
        self.atom_shutter(0)
        
    def reset_all_DDS(self):
        self.Li_pump.reset()
        self.Li_repump.reset()
        self.LiSS.reset()
        self.Rb_pump.reset()
        self.Rb_repump.reset()
        self.Rb_zeeman_slower.reset()
        self.Li_imaging.reset()
        self.ipg_AOM_driver_input.reset()
        self.SPI_AOM.reset()
        self.TiSapph1_comb_lock_AOM.reset()
        self.TS1_main_AOM.reset()
        self.TS2_main_AOM.reset()

    def util_voltage(self,voltage):
        self.Utility_voltage.set_scaled_value(voltage)    
        
    def util_voltage_mod(self,time,freq,ampl,offset,phase=0,t0=0,limit=10):
        #voltage mod requires a duration,freq,ampl,and offset 
        #optional t0,phase, and limit
        S = Waveform('Sinewave',frequency=freq,amplitude=ampl,offset=offset)
        while S.t < time:
            V = S.current_value(self)
            if V < -limit:
                V = -limit
            if V > limit:
                V = limit
            self.util_voltage(V)
           
    def util_trig_high(self):
        self.Utility_trigger(1)
        
    def util_trig_low(self):
        self.Utility_trigger(0)
    
    def fb_coils_supply_output_on(self):
        self.fb_coil_output_control(1)
        
    def fb_coils_supply_output_off(self):
        self.fb_coil_output_control(0)
     
    # def fb_coils_supply_output_on(self):
        # self.fb_coil_output_control.set_scaled_value(4)
    
    # def fb_coils_supply_output_off(self):
        # self.fb_coil_output_control.set_scaled_value(0)
        
    def util_trig_pulse_us(self,dur):
        self.Utility_trigger(1)
        self.wait_us(dur)
        self.Utility_trigger(0)
        
        
    def __modulate_function(self,func,time,limits=(-10,10),dtmin_s=1000, **modkw):
        #modkw includes: frequency,amplitude,offset,phase,t0
        S = Waveform('Sinewave',**modkw)
        while S.t <= time:
            #dtmin ensures that points are spaced by at least this amount
            V0 = S.currentValue(self,dtmin_s=dtmin_s) 
            V = numpy.clip(V0,limits[0],limits[1])
            #print V
            func(V)
            
    def __ramp_function(self,func,time,limits=(-10,10),dtmin_s=0, **rampkw):
        #rampkw includes: T,V1,V2
        S = Waveform('Ramp',**rampkw)
        while S.t <= time:
            #dtmin ensures that points are spaced by at least this amount
            V0 = S.currentValue(self,dtmin_s=dtmin_s) 
            V = numpy.clip(V0,limits[0],limits[1])
            func(V)
            
    # def mot_shutter_on(self):
        # self.mot_shutter(0)

    # def mot_shutter_off(self):
        # self.mot_shutter(1)
       
    def LiRb_mot_shutter_on(self):
        self.LiRb_mot_shutter(0)
        
    def LiRb_mot_shutter_off(self):
        self.LiRb_mot_shutter(1)
        
    def LiRb_mot_shutter_off_nobounce_25000us(self):
        self.LiRb_mot_shutter(1)
        self.wait_ms(23)
        self.LiRb_mot_shutter(0)
        self.wait_ms(2)
        self.LiRb_mot_shutter(1)
  
    # def mot_shutter_off_nobounce_9ms(self):
        # self.mot_shutter_off()
        # self.wait_ms(4.7)
        # self.mot_shutter_on()
        # self.wait_ms(4.3)
        # self.mot_shutter_off()
        
    # def mot_shutter_on_nobounce7ms(self):
        # self.mot_shutter_on()
        # self.wait_ms(5)
        # self.mot_shutter_off()
        # self.wait_ms(2)
        # self.mot_shutter_on()

    def mot_shutter_off_nobounce7ms(self):
        self.mot_shutter_off()
        self.wait_ms(5)
        self.mot_shutter_on()
        self.wait_ms(2)
        self.mot_shutter_off()
    
    def mot_shutter_off_nobounce_9_5ms(self):   # Newest OFF nobounce as off 07/24/2010!
        # NOTE: the extra wait at the end is to ensure light is off exactly when the command
        # finishes running.
        self.mot_shutter_off()
        self.wait_ms(4)
        self.mot_shutter_on()
        self.wait_ms(4)
        self.mot_shutter_off()
        self.wait_ms(1.5)
    
    def Li_slowing_beam_shutter_open(self):
        ## NOTE: Shutter wired backwards, so needed to change commands!!
        # THIS COMMAND SHOULD BE REMOVED. REFERENCES TO THE SLOWING BEAM SHUTTER ARE NOW DONE WITH: Zeeman_Slower_shutter
        self.Li_slowing_beam_shutter(0)
        
    def Li_slowing_beam_shutter_closed(self):
        ## NOTE: Shutter wired backwards, so needed to change commands!!
        # THIS COMMAND SHOULD BE REMOVED. REFERENCES TO THE SLOWING BEAM SHUTTER ARE NOW DONE WITH: Zeeman_Slower_shutter
        self.Li_slowing_beam_shutter(1)
        
    def optical_pump_shutter_on_nobounce7ms(self):
        self.optical_pump_shutter(1)
        self.wait_ms(5)
        self.optical_pump_shutter(0)
        self.wait_ms(2)
        self.optical_pump_shutter(1)

    def optical_pump_shutter_off_nobounce7ms(self):
        self.optical_pump_shutter(0)
        self.wait_ms(5)
        self.optical_pump_shutter(1)
        self.wait_ms(2)
        self.optical_pump_shutter(0)
    
    def main_optical_pump_srs_shutter_closed(self):
        self.srs_main_optical_pump_shutter(0)
        
    def main_optical_pump_srs_shutter_open(self):
        self.srs_main_optical_pump_shutter(1)
    
    def optical_depump_srs_shutter_closed(self):
        self.srs_optical_depump_shutter(0)
        
    def optical_depump_srs_shutter_open(self):
        self.srs_optical_depump_shutter(1)

    def Rb_optical_pumping_shutter_open(self):
        ## NOTE: Shutter wired backwards, so needed to change commands!!
        self.optical_pumping_shutter(0)
        #self.optical_pumping_shutter(1)

    def Rb_optical_pumping_shutter_closed(self):
        ## NOTE: Shutter wired backwards, so needed to change commands!!
        self.optical_pumping_shutter(1)
        #self.optical_pumping_shutter(0)
     
    def Rb_repump_AOM_shutter_open(self):
        self.Rb_repump_shutter(1)
        
    def Rb_repump_AOM_shutter_closed(self):
        self.Rb_repump_shutter(0)

    def Rb_pump_shutter_on(self):
        self.Rb_pump_shutter(0)

    def Rb_pump_shutter_off(self):
        self.Rb_pump_shutter(1)
    
    def Rb_repump_mot_shutter_open(self):
        self.Rb_MOT_repump_shutter(0)
        
    def Rb_repump_mot_shutter_closed(self):
        self.Rb_MOT_repump_shutter(1)
    
    def repump_shadow_only(self,value = 0):
        self.Rb_MOT_repump_shutter(value)

    def Rb_abs_shutter_on(self):
        self.Rb_abs_shutter(1)

    def Rb_abs_shutter_off(self):
        self.Rb_abs_shutter(0)
    
    def MOL_TiSapph_srs_shutter_open(self):
        self.mol_tisapph_srs_shutter(1)

    def MOL_TiSapph_srs_shutter_closed(self):
        self.mol_tisapph_srs_shutter(0)
    
    def Rb_abs_shutter_on_nobounce7ms(self):
        self.Rb_abs_shutter(1)
        self.wait_ms(6)
        self.Rb_abs_shutter(0)
        self.wait_ms(1)
        self.Rb_abs_shutter(1)

    def Rb_abs_shutter_off_nobounce7ms(self):
        self.Rb_abs_shutter(0)
        self.wait_ms(6)
        self.Rb_abs_shutter(1)
        self.wait_ms(1)
        self.Rb_abs_shutter(0)
        
    ###################################################################################
    ## camera methods or properties
    ###################################################################################
    @property
    def nr_camera_triggers(self):
        return self.__pixelink_triggers
        
    def nr_camera_triggers(self):
        return self.__apogee_triggers
        
    @property
    def pixelink_triggers_count(self):
        return self.__pixelink_triggers
        
    @property
    def apogee_triggers_count(self):
        return self.__apogee_triggers
        
    @property
    def pointgrey_triggers_count(self):
        return self.__pointgrey_triggers    
        
    def trigger_pixelink(self,string=None):
        # print 'trigger image %s\n' % (string)
        self.pixelink_trigger(1)
        self.wait_us(5)
        self.pixelink_trigger(0)
        self.__pixelink_triggers += 1
        return self.pixelinkLabels.next(string)

    def trigger_apogee(self,string=None):
        self.apogee_trigger(1)
        self.wait_us(10)
        self.apogee_trigger(0)
        self.__apogee_triggers += 1
        return self.apogeeLabels.next(string)
        
    def trigger_pointgrey(self, string=None):
        self.pointgrey_trigger(1)
        self.wait_us(5) #5
        self.pointgrey_trigger(0)
        self.__pointgrey_triggers += 1
        return self.pointgreyLabels.next(string)
        
    def readout_apogee(self):
        # i think this was for testing the kinetics mode.  may be obsolete.
        self.apogee_readout(1)
        self.wait_s(.4)
        self.apogee_readout(0)
        

    ###################################################################################
    ## Li methods or properties
    ###################################################################################
    
    ## AOM's
    def __set_Li_pump_F(self):
        """
        calculates correct AOM frequencies to get desired detuning based 
        on fixed lock parameters
        """
        lock_F = lock_DDS_params['Li']['f0']
        AOM1shift = lock_DDS_params['Li']['f1']
        F = 0.5*(lock_F/2.0 + AOM1shift - self.__Li_pump_dF)
        # print 'Li_pumpAOM frequency is ',F
        self.Li_pump.single_tone(F)
        
    def __set_Li_repump_F(self):
        """
        calculates correct AOM frequencies to get desired detuning based 
        on fixed lock parameters AND setting of pump laser
        """
        lock_F = lock_DDS_params['Li']['f0']
        F = 0.5*(228*MHz - lock_F/2.0 + self.__Li_repump_dF)
        # print 'Li_repumpAOM frequency is ',F
        self.Li_repump.single_tone(F)

    def __set_Li_imaging_F(self):
        """
        just sets Li imaging AOM.  Normally this will be fixed.
        """
        F = self.__Li_imaging_F       
        # print 'Li imaging AOM frequency is ',F
        self.Li_imaging.single_tone(F)

    def __set_IPG_cross_F(self):
        """
        just sets IPG AOM used for crossed trap (80MHz on the breadboard).  Normally this will be fixed.
        """
        F = self.__IPG_cross_F       
        # print 'IPG cross AOM frequency is ',F
        self.IPG_cross.single_tone(F)    
        
    def __set_LiSS_F(self):
        """
        calculates correct RF frequencies to get desired detuning
        """
        lock_F = lock_DDS_params['LiSS']['f0']
        F = 0.5*(228.205*MHz + self.__LiSS_dF)          
        # print 'Li StateSelector frequency is ',F
        self.LiSS.single_tone(F)
        
    def __set_TiSapph1_comb_lock_AOM_F(self):
        """
        sets the frequency
        """
        F = self.__TiSapph1_comb_lock_AOM_F            
        # print 'TiSapph1 comb lock AOM frequency is ',F
        self.TiSapph1_comb_lock_AOM.single_tone(F)
        
    def __set_TS1_main_AOM_F(self):
        """
        sets the frequency
        """
        F = self.__TS1_main_AOM_F            
        # print 'TiSapph1 main AOM frequency is ',F
        self.TS1_main_AOM.single_tone(F)
        
    def __set_TS2_main_AOM_F(self):
        """
        sets the frequency
        """
        F = self.__TS2_main_AOM_F            
        # print 'TiSapph2 main AOM frequency is ',F
        self.TS2_main_AOM.single_tone(F)
        
        
    def __set_Li6_pump_modulate(self):
        """
        calculates correct AOM frequenciues to get desired high and low detunings
        based on fixed lock parameteres and ramps between them
        """
        lock_F = lock_DDS_params['Li']['f0']
        AOM1shift = lock_DDS_params['Li']['f1']
        F1 = 0.5*(lock_F/2.0 + AOM1shift - self.__Li_pump_dF1)
        F2 = 0.5*(lock_F/2.0 + AOM1shift - self.__Li_pump_dF2)
        T = 1/float(self.__Li_pump_modf)
        # print 'Li6_PUMP-AOM low frequency is ',F1
        # print 'Li6_PUMP-AOM high frequency is ',F2
        # print 'Li6_PUMP-AOM ramping period is ',T*2
        self.Li_pump.triangle_ramp(F1,F2,T)   
        
    def __set_Li6_repump_modulate(self):
        """
        calculates correct AOM frequencies to get desired detuning based 
        on fixed lock parameters AND setting of pump laser
        """
        lock_F = lock_DDS_params['Li']['f0']
        F1 = 0.5*(228*MHz - lock_F/2.0 + self.__Li_repump_dF1)
        F2 = 0.5*(228*MHz - lock_F/2.0 + self.__Li_repump_dF2)
        T = 1/float(self.__Li_repump_modf)
        # print 'Li6_PUMP-AOM low frequency is ',F1
        # print 'Li6_PUMP-AOM high frequency is ',F2
        # print 'Li6_PUMP-AOM ramping period is ',T*2
        self.Li_repump.triangle_ramp(F1,F2,T)   
        
    def set_Li_pump_modulate(self,dF1,dF2,modf):
        self.__Li_pump_dF1 = dF1*MHz
        self.__Li_pump_dF2 = dF2*MHz
        self.__Li_pump_modf = modf*MHz
        self.__set_Li6_pump_modulate()
        
    def set_Li_repump_modulate(self,dF1,dF2,modf):
        self.__Li_repump_dF1 = dF1*MHz
        self.__Li_repump_dF2 = dF2*MHz
        self.__Li_repump_modf = modf*MHz
        self.__set_Li6_repump_modulate()
        
    def set_Li_pump_dF(self,delta):
        self.__Li_pump_dF = delta*MHz
        self.__set_Li_pump_F()

    def set_Li_repump_dF(self,delta):
        self.__Li_repump_dF = delta*MHz
        self.__set_Li_repump_F()
        
    def set_LiSS_dF(self,delta):
        self.__LiSS_dF = delta*MHz
        self.__set_LiSS_F()
        
    def set_Li_imaging_F(self,F):
        self.__Li_imaging_F = F*MHz
        self.__set_Li_imaging_F()

        
    def set_IPG_cross_F(self,F):
        self.__IPG_cross_F = F*MHz
        self.__set_IPG_cross_F()

    def set_TiSapph1_comb_lock_AOM_F(self,F):
        self.__TiSapph1_comb_lock_AOM_F = F*MHz
        self.__set_TiSapph1_comb_lock_AOM_F()

    def set_TS1_main_AOM_F(self,F):
        self.__TS1_main_AOM_F = F*MHz
        self.__set_TS1_main_AOM_F()
        
    def set_TS2_main_AOM_F(self,F):
        self.__TS2_main_AOM_F = F*MHz
        self.__set_TS2_main_AOM_F()
    
    # def set_TS2_FM_volts(self,V_):
        # 1V = 56 MHz
        # 1mV = 56 kHz
        # 20DB att. before driver
        # V_ = numpy.clip(V_,-.5,.5)
        # V = V_
        # self.TS2_FM.set_scaled_value(V)

    # def set_TS2_AM_volts(self,V_):
        # 1V = full on, depends on set level
        # V_ = numpy.clip(V_,-.5,.5)
        # V = V_
        # self.TS2_AM.set_scaled_value(V)
     
        
    def set_IGP_AOM_RF_Level_on_analog(self):
        self.IGP_AOM_RF_Level.set_scaled_value(5.0)
    
    def set_IGP_AOM_RF_Level_off_analog(self,val):
        self.IGP_AOM_RF_Level.set_scaled_value(0)
    
        
        
        
        
    def ramp_LiSS_dF(self,start_dF,end_dF,time_s,amp):      
        """
        calculates correct DDS frequencies to get desired high and low detunings
        based on fixed lock parameters, and ramps between them
        """  
        # lock_F = lock_DDS_params['LiSS']['f0']
        F1 = 0.5*(228.205*MHz + start_dF*MHz)   
        F2 = 0.5*(228.205*MHz + end_dF*MHz)            
        # print 'Li StateSelector start frequency is ',F1
        # print 'Li StateSelector end frequency is ',F2
        # print 'Li StateSelector ramp duration is ',time_s
        self.LiSS.single_tone(F1)
        self.LiSS.ramped_FSK(F1,F2,time_s)
        self.LiSS.set_amplitude(amp) 
        self.RbSS_FSK(1)
        self.wait_s(time_s)
        self.LiSS.single_tone(F2)
        self.RbSS_FSK(0)
        
    # def ramp_Li_pump(self,start_dF,end_dF,time_s):
    
   
    def set_LiSS_amplitude(self,amplitude):
        self.LiSS.set_amplitude(amplitude) 
      
    def set_TiSapph1_comb_lock_AOM_amplitude(self,amplitude):
        amp = min(1*amplitude,1)
        self.TiSapph1_comb_lock_AOM.set_amplitude(amp) 
        
    def set_TS1_main_AOM_amplitude(self,amplitude):
        # amp = min(0.65*amplitude,0.65) #amp = min(1*amplitude,1) with RF attenuator
        amp = min(amplitude,1) #amp = min(1*amplitude,1) with RF attenuator
        self.TS1_main_AOM.set_amplitude(amp)
        
    def set_TS2_main_AOM_amplitude(self,amplitude):
        # amp = min(0.65*amplitude,0.65) #amp = min(1*amplitude,1) with RF attenuator
        amp = min(1*amplitude,1)
        self.TS2_main_AOM.set_amplitude(amp)
        
        
    def set_Li_imaging_amplitude(self,amplitude):
        self.Li_imaging.set_amplitude(amplitude)
       
  
    def set_Li_pump_amplitude(self,amp):
        # Normalized to accept a value between 0 and 1
        a = numpy.clip(amp,0,1)
        a = a*0.12
        self.Li_pump.set_amplitude(a)
        
    def set_Li_repump_amplitude(self,amp):
        a = numpy.clip(amp,0,1)
        a = a*0.10
        self.Li_repump.set_amplitude(a)
     

    ## shutters
        

        
    def Li_pump_shutter_on(self):
        self.Li_pump_shutter(1)
    def Li_pump_shutter_off(self):
        self.Li_pump_shutter(0)
                
    def Li_pump_shutter_on_nobounce_5ms(self):
        self.Li_pump_shutter_on()
        self.wait_ms(3.5)
        self.Li_pump_shutter_off()
        self.wait_ms(1.5)
        self.Li_pump_shutter_on()

    
    # def high_field_imaging_shutter_on(self): #lithium high field imaging shutter(located on the master table)
        # self.high_field_imaging_shutter(1)
    # def high_field_imaging_shutter_off(self):
        # self.high_field_imaging_shutter(0)
    
    ## NEW IPOD SHUTTERS
    ############################################
    
    def Li_MOT_shutter_open(self):
        self.Li_MOT_shutter(1)
    def Li_MOT_shutter_close(self):
        self.Li_MOT_shutter(0)
        
    def Zeeman_Slower_shutter_open(self):
        self.Zeeman_Slower_shutter(1)
    def Zeeman_Slower_shutter_close(self):
        self.Zeeman_Slower_shutter(0)
        
    def Li_repump_abs_shutter_open(self):
        self.Li_repump_abs_shutter(1)
    def Li_repump_abs_shutter_close(self):
        self.Li_repump_abs_shutter(0)
    
    def Li_pump_abs_shutter_open(self):
        self.Li_pump_abs_shutter(1)
    def Li_pump_abs_shutter_close(self):
        self.Li_pump_abs_shutter(0)
    
    def Li_HF_imaging_shutter_open(self):
        self.Li_HF_imaging_shutter(1)
    def Li_HF_imaging_shutter_closed(self):
        self.Li_HF_imaging_shutter(0)

    ###################################################################################
    ## general methods or properties (same for both isotopes)
    ###################################################################################

    def Rb_repump_on(self):
        self.Rb_repump.set_amplitude(1.0)
        
    def Rb_repump_off(self):
        self.Rb_repump.set_amplitude(0.0)  
        
    def Rb_pumpAOM_on(self):
        self.Rb_pump.set_amplitude(1.0)
        
    def Rb_pumpAOM_off(self):
        self.Rb_pump.set_amplitude(0)

    # def Rb_optical_pump_on(self):
        # self.Rb_optical_pump.set_amplitude(1.0)
        
    # def Rb_optical_pump_off(self):
        # self.Rb_optical_pump.set_amplitude(0.0)

    # def far_detuned_shutter_open(self):
        # self.far_detuned_mot_shutter(0)
        
    # def far_detuned_shutter_closed(self):
        # self.far_detuned_mot_shutter(1)

    ###################################################################################
    ## Rb85 methods or properties
    ###################################################################################

    def __set_Rb85_pump_F(self):
        """
        calculates correct AOM frequencies to get desired detuning based 
        on fixed lock parameters
        """
        lock_F = lock_DDS_params['dirty_blonde']['f0']
        #F = 0.5*(60.5*MHz + lock_F + self.__Rb_pump_dF)
        F = 0.5*(180*MHz + self.__Rb_pump_dF)        
        # print 'Rb85-PUMP-AOM frequency is ',F
        self.Rb_pump.single_tone(F)
    
    def __set_Rb85_pump_ramped_F(self):
        """
        calculates correct AOM frequenciues to get desired high and low detunings
        based on fixed lock parameteres and ramps between them
        """
        lock_F = lock_DDS_params['dirty_blonde']['f0']
        F1 = 0.5*(180*MHz + self.__Rb_pump_dF1)
        F2 = 0.5*(180*MHz + self.__Rb_pump_dF2)
        T = self.__Rb_pump_ramped_time
        # print 'Rb85-PUMP-AOM low frequency is ',F1
        # print 'Rb85-PUMP-AOM high frequency is ',F2
        # print 'Rb85-PUMP-AOM ramping period is ',T*2
        self.Rb_pump.triangle_ramp(F1,F2,T)
        
    def __set_Rb85_repump_saw_tooth_F(self):
        """
        calculates correct AOM frequencies to get desired detuning based 
        on fixed lock parameters. creates saw tooth pattern from D1 -> D2
        """
        lock_F = lock_DDS_params['blonde']['f0']
        F1 = 0.5*(180*MHz + self.__Rb_pump_dF1)
        F2 = 0.5*(180*MHz + self.__Rb_pump_dF2)
        T = self.__Rb_pump_ramped_time
        self.Rb_repump.sawtooth(F1,F2,T)
        
        
    def __set_Rb85_repump_ramped_F(self):
        """
        calculates correct AOM frequenciues to get desired high and low detunings
        based on fixed lock parameteres and ramps between them
        """
        lock_F = lock_DDS_params['blonde']['f0']
        F1 = 0.5*(180*MHz + self.__Rb_pump_dF1)
        F2 = 0.5*(180*MHz + self.__Rb_pump_dF2)
        T = self.__Rb_pump_ramped_time
        # print 'Rb85-PUMP-AOM low frequency is ',F1
        # print 'Rb85-PUMP-AOM high frequency is ',F2
        # print 'Rb85-PUMP-AOM ramping period is ',T*2
        self.Rb_repump.triangle_ramp(F1,F2,T)

    def __set_Rb85_repump_F(self):
        """
        calculates correct AOM frequencies to get desired detuning based 
        on fixed lock parameters
        """
        lock_F = lock_DDS_params['blonde']['f0']
        #F = 0.5*(77*MHz + lock_F + self.__Rb_repump_dF)
        F = 0.5*(180*MHz + self.__Rb_repump_dF)
        # print 'Rb85-REPUMP-AOM frequency is ',F
        self.Rb_repump.single_tone(F)

    def __set_Rb85_zeeman_slower_F(self):
        """
        calculates correct AOM frequencies to get desired detuning based 
        on fixed lock parameters
        """
        #lock_F = lock_DDS_params['dirty_blonde']['f0']
        #F = 0.5*(60.5*MHz + lock_F + self.__Rb_pump_dF)
        F = 0.5*(180*MHz + self.__Rb85_zeeman_slower_dF)    
        # print 'Rb85_zeeman_slower_frequency is ',F
        self.Rb_zeeman_slower.single_tone(F)
    
    def set_Rb85_pump_dF(self,delta):        
        self.__Rb_pump_dF = delta*MHz
        self.__set_Rb85_pump_F()
    
    def set_Rb85_pump_ramped_dF(self,delta1, delta2, Pramp_ms):
        self.__Rb_pump_dF1 = delta1*MHz
        self.__Rb_pump_dF2 = delta2*MHz
        self.__Rb_pump_ramped_time = Pramp_ms/1000.0/2
        self.__set_Rb85_pump_ramped_F()
     
    def set_Rb85_repump_saw_tooth_dF(self, delta1, delta2, Pramp_ms):
        self.__Rb_pump_dF1 = delta1*MHz
        self.__Rb_pump_dF2 = delta2*MHz
        self.__Rb_pump_ramped_time = Pramp_ms/1000.0
        self.__set_Rb85_repump_saw_tooth_F()
        
    def set_Rb85_repump_ramped_dF(self, delta1, delta2, Pramp_ms):
        self.__Rb_pump_dF1 = delta1*MHz
        self.__Rb_pump_dF2 = delta2*MHz
        self.__Rb_pump_ramped_time = Pramp_ms/1000.0/2
        self.__set_Rb85_repump_ramped_F()
        
    def set_Rb85_repump_dF(self,delta):
        self.__Rb_repump_dF = delta*MHz
        self.__set_Rb85_repump_F()

    # def set_Rb85_optical_pump_dF(self,delta):
        # self.__Rb85_optical_pump_dF = delta*MHz
        # self.__set_Rb85_optical_pump_F()

    def set_Rb85_zeeman_slower_dF(self,delta):
        self.__Rb85_zeeman_slower_dF = delta*MHz
        self.__set_Rb85_zeeman_slower_F()
    
    def set_Rb85_zeeman_slower_amplitude(self,amp):
        A = numpy.clip(amp,0,1) #was 0.22
        self.Rb_zeeman_slower.set_amplitude(A)

    def Rb85_light_off(self,**kw):
        self.Rb_pump_shutter_off()
        self.Rb_repump_off()

    ###################################################################################
    ## Rb87 methods or properties
    ###################################################################################

    def __set_Rb87_pump_F(self):
        """
        calculates correct AOM frequencies to get desired detuning based 
        on fixed lock parameters
        """
        lock_F = lock_DDS_params['brunette']['f0']
        #F = 0.5*(133*MHz + 0.5*lock_F + self.__Rb_pump_dF)
        F = 0.5*(180*MHz + self.__Rb_pump_dF)
        # print 'Rb87-PUMP-AOM frequency is ',F
        self.Rb_pump.single_tone(F)
        
    def __set_Rb87_repump_F(self):
        """
        calculates correct AOM frequencies to get desired detuning based 
        on fixed lock parameters
        """
        lock_F = lock_DDS_params['jet_black']['f0']
        #F = 0.5*(79*MHz + lock_F + self.__Rb_repump_dF)
        F = 0.5*(180*MHz + self.__Rb_repump_dF)
        # print 'Rb87-REPUMP-AOM frequency is ',F
        self.Rb_repump.single_tone(F)  

    def __set_Rb87_optical_pump_F(self):
        """
        calculates correct AOM frequencies to get desired detuning based 
        on fixed lock parameters
        """
        #lock_F = lock_DDS_params['dirty_blonde']['f0']
        #F = 0.5*(60.5*MHz + lock_F + self.__Rb_pump_dF)
        F = (86*MHz)-self.__Rb87_optical_pump_df      
        # print 'Rb85_optical_pump_frequency is ',F
        self.Rb_optical_pump.single_tone(F)

    def set_Rb87_pump_dF(self,delta):
        self.__Rb_pump_dF = delta*MHz
        self.__set_Rb87_pump_F()
        
    def set_Rb87_repump_dF(self,delta):
        self.__Rb_repump_dF = delta*MHz
        self.__set_Rb87_repump_F()
      
    ###################################################################################
    ## Li zeeman slower methods or properties
    ###################################################################################
      
    def set_Li_zeeman_Slower_F(self,freq):
        """
        Sets AOM freq for Li Zeeman Slower
        """
        freq=freq*MHz
        # print 'Li_zeeman_slower requency is ',freq
        self.Li_zeeman_slower.single_tone(freq)
    
    def set_Li_zeeman_slower_amplitude(self,amplitude):
        """
        Sets AOM amplitude for Li Zeeman Slower
        """
        amplitude=0.0918*numpy.clip(amplitude,0,1) # 0.65power peaks at 0.65 amplitude
        # print 'Li_zeeman_slower requency is ', amplitude
        self.Li_zeeman_slower.set_amplitude(amplitude) 

    ###################################################################################
    ## Coil methods or properties
    ###################################################################################

    def mot_coil_enabled(self):
        # print '\n'
        # print 'COILS ARE BEING ENABLED'
        # print '\n'
        self.mot_coil_HBridge_left(1)
        self.mot_coil_HBridge_right(0)
        # self.fb_coils_supply_output_on() # this is added to remote enable the Sorenson power supply
        
    def mot_coil_disabled(self):
        # print '\n'
        # print 'COILS ARE BEING DISABLED'
        # print '\n'
        self.mot_coil_HBridge_left(0)
        self.mot_coil_HBridge_right(0)
        # self.fb_coils_supply_output_off() # this is added to remote disable the Sorenson power supply

    def mot_coil_set_polarity_10ms(self,config):
        # print '\n'
        # print 'COILS ARE SETTING POLARITY'
        # print '\n'
        self.mot_coil_disabled()
        self.wait_ms(10)
        if config=='helmholtz':
            self.mot_coil_HBridge_right(1)
            self.mot_coil_HBridge_left(0)
        if config=='antihelmholtz':
            self.mot_coil_HBridge_right(0)
            self.mot_coil_HBridge_left(1)
     
    def set_supply_max_current(self,A):
        Amps = numpy.clip(A,0,50)
        self.fb_coil_supply_current_control.set_scaled_value(0.1*Amps)
        # print '\n'
        # print 'SUPPLY MAX CURRENT IS SET TO ', 0.1*Amps
        # print '\n'

    def set_mot_coil_I(self,A):
        Amps = numpy.clip(A,0,40)
        # self.fb_coils_supply_output_on() # this is added to remote enable the Sorenson power supply       
        # self.fb_coil_supply_current_control.set_scaled_value(0.2*Amps)  # this is used to set the Sorenson current output - note different scale factor       
        self.mot_coil_plus.set_scaled_value(0.1*Amps) 
        self.mot_coil_minus.set_scaled_value(0.0)
        # print '\n'
        # print 'MOT COIL CURRENT IS SET TO ', 0.1*Amps
        # print '\n'

    # def set_gradient_coils_I(self,A): # sets current of the curvature coils using comp coil driver channel M3
        # C = COMPCOIL_COVERSION_V_PER_A  #current must be <5A
        # self.gradient_coils.set_scaled_value(C*A)

    def ramp_mot_coil_I(self,start_A,end_A,speed_A_per_sec):
        #NOT FINISHED IMPLEMENTING
        start_V = start_A*0.1
        end_V = end_A*0.1
        t_s = float(end_A - start_A)/float(speed_A_per_sec)
        min_volt_change = 20.0/65536.0
        numsteps = (end_V-start_V)/min_volt_change
        delta_t_s = t_s/numsteps
        # print numsteps,t_s,delta_t_s
        return t_s

    def set_comp_coils_I(self,x,y,z):
        # print "===================\n"
        # print 'comp coil I %lf %lf %lf\n'%(x,y,z)
        # print "===================\n"
        C = COMPCOIL_COVERSION_V_PER_A 
        self.comp_coil_x.set_scaled_value(C*x)
       # self.comp_coil_x_wind.set_scaled_value(C*x)
        self.comp_coil_y_oven.set_scaled_value(C*y)
        self.comp_coil_y_pump.set_scaled_value(C*y)
        self.comp_coil_z_top.set_scaled_value(C*z)
        self.comp_coil_z_bot.set_scaled_value(C*z)
        
    def set_comp_coils_V(self,x,y,z):
        # print "===================\n"
        # print 'comp coil V %lf %lf %lf\n'%(x,y,z)
        # print "===================\n"
        self.comp_coil_x.set_scaled_value(x)
       # self.comp_coil_x_wind.set_scaled_value(x)
       # self.comp_coil_y_oven.set_scaled_value(y) used for atom shutter on 11/4/2015
        self.comp_coil_y_pump.set_scaled_value(y)
        self.comp_coil_z_top.set_scaled_value(z)
        self.comp_coil_z_bot.set_scaled_value(z)
     
    def set_mot_coil_supply_current_A(self,I):                             
        Amps = numpy.clip(I,0,30)
        self.fb_coil_supply_current_control.set_scaled_value(0.2*Amps)
    
    def set_mot_coil_supply_voltage_V(self,V):
        Volts = numpy.min(V,50)
        self.fb_coil_supply_voltage_control.set_scaled_value(0.1*Volts)
 
 # hack
    def set_zeeman_coil_V(self,channel,volt_in):
    #For setting the voltage of specific zeeman coils
    #channel is an array of channel numbers from 1 to 8.
    #volt_in is an array of voltages corresponding to the order of the channels
    #Note that even if one wishes to pass a single channel-voltage pair,
    #they must each be in an array format
        vref = 3.3
        V = numpy.clip(volt_in,0,vref)
        for i in numpy.arange(0,len(channel)):
            zeeman_attr='zeeman_coil_'+str(channel[i])
            getattr(self,zeeman_attr).set_value(V[i]/vref*4096)

    def set_zeeman_coil_I(self,channel,current_in):
    #For setting the voltage of specific zeeman coils
    #channel is an array of channel numbers from 1 to 8.
    #volt_in is an array of voltages corresponding to the order of the channels
    #Note that even if one wishes to pass a single channel-voltage pair,
    #they must each be in an array format
        vref = 3.3
        for i in numpy.arange(0,len(channel)):
            self.wait_ms(10)
            channel_num_str = "COIL"+str(channel[i])
            coil_v_per_a = zeeman_coil_current_calib[channel_num_str]["SLOPE_V_PER_A"]
            offset = zeeman_coil_current_calib[channel_num_str]["intercept"]
            zeeman_attr='zeeman_coil_'+str(channel[i])
            v = numpy.clip(current_in[i]*coil_v_per_a+offset,0,vref)
            #print channel_num_str + ": " + str(coil_v_per_a) + ", writing voltage: " + str(v);
            getattr(self,zeeman_attr).set_value(v/vref*4096)       
        
        
    ###################################################################################
    ## TiSapph Control
    ###################################################################################    

    def set_tisapph_external_control_voltage(self,voltage):
        volts = numpy.clip(voltage,-5,5) 
        # print 'SETTING VOLTAGE TO: ', volts
        self.TiSapph_scan_output.set_scaled_value(volts)
    
    def ramp_Ti_Sapph(self,T,low,high,dt=0.1):
        dt = float(numpy.max(dt, .1))
        N = int(T/dt)
        V1 = low
        V2 = high
        dV = (V2-V1)/float(N)
        #print '!!!!!!!!!!!!SCANNING TISAPPH!!!!!!!!!!!!!!!!',N,T,dt,V1,V2
        for i in range(0,N):
            self.set_tisapph_external_control_voltage(V1 + dV*i)
            #print V1+dV*i
            self.wait_ms(dt)
            
    def lockbox_ttl_on(self):#sets TTL signal sent to TiSaph loxkbox to 5V
        self.lockbox_ttl(1)
    def lockbox_ttl_off(self):#sets TTL signal sent to TiSaph loxkbox to 0V
        self.lockbox_ttl(0)
        
    def TS1_error_signal_set_invert(self):
        self.TS1_error_signal_invert(0)
    def TS1_error_sigal_set_normal(self):
        self.TS1_error_signal_invert(1)
        
    def TS1_error_signal_inversion(self,boolean):
        if boolean==0:
            self.TS1_error_sigal_set_normal()
        elif boolean==1:
            self.TS1_error_signal_set_invert()
        
    ###################################################################################
    ## IPG methods or properties
    ###################################################################################
        
    def set_IPG_AOM_analog_in_V(self,V):
        # User should set the tweezer AOM manual offset to 0
        # corrects for dissapation due to the voltage combiner, clips at AO input of 2V.
        # V_corr = 2.1289*V-0.0903
        volts = numpy.clip(V,0,1.2)    # 0 = AOM off (no light), 2 = AOM max (max light)
        self.IPG_AOM_analog_in_V.set_scaled_value(volts)
    
    def set_IPG_cross_amplitude(self,amplitude):
        self.IPG_cross.set_amplitude(amplitude)
    
    def set_IPG_power_W(self,Power):
        P = Power    # Conversion for decrease in AOM efficiency
        # print P
        # Converts the desired power into the correct AOM setting. ASSUMES IPG SET TO 20W
        if P>=0.7840:
            p1 = 1.4747e-006
            p2 = -4.2564e-005            
            p3 = 3.9767e-004
            p4 =  -5.9853e-004
            p5 = -0.0119
            p6 = 0.1326
            p7 = 0.1044
            ipg_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        if P < 0.7840 and P >= .0940:
            p1 = -0.7762
            p2 = 2.8840
            p3 = -4.2103
            p4 = 3.1961
            p5 = -1.4435
            p6 = 0.5601
            p7 = 0.0246
            ipg_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        if P < 0.0940:
            p1 = -2.2947*1e6
            p2 =  7.1637e+005
            p3 =  -8.7557e+004
            p4 = 5.3306e+003
            p5 =  -173.3167
            p6 =  3.5585
            p7 = -0.0022
            ipg_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        
        ipg_aom_setting = numpy.clip(ipg_aom_setting_,0,1)
        # print ipg_aom_setting_
        # print '*** SETTING IPG AOM TO:', ipg_aom_setting
        self.set_IPG_AOM_analog_in_V(ipg_aom_setting)

    def set_IPG_power_DDS_control_W(self,Power):
        max_power=20
        P = Power
        # Converts the desired power into the correct AOM setting. ASSUMES IPG SET TO 20W
        # used when running IPG AOM driver via DDS control (NOT AO)
        # if P>=1.35:
        #     p1 = 7.6415e-8
        #     p2 = 4.9873e-6            
        #     p3 = -2.1778e-4
        #     p4 =  0.0033
        #     p5 = -0.0244
        #     p6 = 0.1586
        #     p7 = 0.1135
        #     ipg_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        # if P < 1.35 and P >= .08:
        #     p1 = -0.2788
        #     p2 = 1.2496
        #     p3 = -2.2557
        #     p4 = 2.1475
        #     p5 = -1.2256
        #     p6 = 0.5830
        #     p7 = 0.0300
        #     ipg_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        # if P < 0.08:
        #     p1 = -8.3996e6
        #     p2 =  2.1769e6
        #     p3 =  -2.1884e5
        #     p4 = 1.0805e4
        #     p5 =  -277.7057
        #     p6 =  4.3107
        #     p7 = 0.0037
        #     ipg_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
            
        # if P==0:
        #     ipg_aom_setting_ = 0
        power = Power*1.0/max_power*1.0
        a = 0.369253349662
        b = 0.925142644829
        c = 1.36565985279
        d = 0.531660731916
        aom_setting = a*(erfinv(power/d-b)+c)

        if isinf(aom_setting):
            aom_setting = 1
        if power == 0:
            aom_setting = 0
        ipg_aom_setting = clip(aom_setting,0,1)
        # print ipg_aom_setting
        # print ipg_aom_setting_
        # print '*** SETTING IPG AOM TO:', ipg_aom_setting
        self.set_IPG_AOM_driver_input_amplitude(ipg_aom_setting)
    
    def set_IPG_cross_power_W(self,Power):
        P = Power/2.5 # Conversion for decrease in AOM efficiency
        # Converts the desired power into the correct AOM setting. ASSUMES IPG SET TO 20W, FIRST AOM SET TO 0
    
        #P = (Power*1.25)/20.0  # Conversion for decrease in AOM efficiency
        #Converts the desired power into the correct AOM setting. ASSUMES IPG SET TO 20W, FIRST AOM SET TO 0
        # if P <.3494 and P>=0.1571:
            # p1 = 1.7722e+004
            # p2 =  -3.2171e+004
            # p3 = 2.3071e+004
            # p4 = -8.3570e+003
            # p5 =  1.6247e+003
            # p6 =  -160.5250
            # p7 = 6.6517
            # ipg_cross_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        # elif P < 0.1571 and P >= .0180:
            # p1 =  -3.1275e+005
            # p2 =  1.4663e+005
            # p3 =-2.6373e+004
            # p4 = 2.3643e+003
            # p5 = -120.4269
            # p6 = 5.4784
            # p7 = 0.0487
            # ipg_cross_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        # elif P < 0.0180: 
            # p1 =  -7.7429e+010
            # p2 = 4.8393e+009
            # p3 =  -1.1711e+008
            # p4 = 1.3852e+006
            # p5 =  -8.4658e+003
            # p6 = 31.3091
            # p7 = 0.0041
            # ipg_cross_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        
        # else:
            # ipg_cross_aom_setting_ = 1 
        # if P==0:
            # ipg_cross_aom_setting_ = 0
        if P>=0.2350:
            p1 = -0.0622
            p2 = 0.5018
            p3 = -1.4155
            p4 = 1.9237
            p5 = -1.3971
            p6 = 0.7569
            p7 = 0.0270
            ipg_cross_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        if P < 0.2350 and P >= .0443:
            p1 = 1.0395e+003
            p2 = -2.2617e+003
            p3 = 1.3857e+003
            p4 = -369.2542
            p5 = 46.0066
            p6 = -1.9747
            p7 = 0.0851
            ipg_cross_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        if P < 0.0443: 
            p1 = -1.3258*1e8
            p2 = 1.9534e+007
            p3 =  -1.1345e+006
            p4 = 3.3270e+004
            p5 =  -536.0357
            p6 = 5.8036
            p7 = 0.0011
            ipg_cross_aom_setting_ = (p1*P**6)+(p2*P**5)+(p3*P**4)+(p4*P**3)+(p5*P**2)+(p6*P**1)+p7
        
        if P==0:
            ipg_cross_aom_setting_ = 0
        # print '*** SETTING CROSS IPG AOM TO:', ipg_cross_aom_setting_
        ipg_cross_aom_setting = numpy.clip(ipg_cross_aom_setting_,0,1)
        # print '*** SETTING CROSS IPG AOM TO:', ipg_cross_aom_setting
        self.set_IPG_cross_amplitude(ipg_cross_aom_setting)
        
    def set_IPG_modulation_order1(self,time,freq_MHz,ampl,offset=1.25,phase=0,t0=0,limits=(0,2),dtmin_s=0):
        #this one assumes that when set up to use order 1 from AOM we control the
        # amplitude with the analog out above "set_IPG_AOM_analog_in_V" 
        #set the tweezer manual offset to 0.  Set AOM offset to 1.25V
        #allowing modulation from 1 to 1.5 being about linear.
        modkw = dict(
            frequency = freq_MHz*MHz,
            amplitude = ampl,
            offset = offset,
            phase = phase,
            t0 = t0,
                )
        func = self.set_IPG_AOM_analog_in_V
        self.__modulate_function(func,time,limits=limits,dtmin_s=dtmin_s, **modkw)
    
    def set_IPG_AOM_driver_input_amplitude(self,amp):
        # set amplitude input, but fixed freq at 90.8 MHz
        # After preamp, max power into driver is -5dBm.
        # This means the max DDS setting is .16... this module accepts a value from 0 to 1 and takes the max
        # allowed value into account
        # A_corrected = amp*.16
        # A = numpy.clip(A_corrected,0,.16)
        A_corrected = 0.40*amp # do not change 0.4 
        # A_corrected = .65*amp
        A = numpy.clip(A_corrected,0,0.40)
        # print 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
        # print A
        # A = numpy.clip(A_corrected,0,.65)
        F = 110*MHz
        self.ipg_AOM_driver_input.single_tone(F)
        self.ipg_AOM_driver_input.set_amplitude(A)

    def set_SPI_AOM_amplitude(self,amp):
        conversion_factor = 0.22#0.17 # Given the amplification setup, setting the output power of the DDS to be 0.22 gives 2.5W (34dBm) for the AOM
        A = conversion_factor*numpy.clip(amp,0,1)
        self.SPI_AOM.set_amplitude(A)

    def set_SPI_AOM_frequency(self,f):
        # Takes:
        #  f: A frequency in MHZ. This AOM is centered at 110MHz.
        self.SPI_AOM.single_tone(f*MHz)

    def set_SPI_setpoint_code(self,code):
        self.SPI_intensity_setpoint.set_value(code)   

    def set_SPI_setpoint_voltage(self,v):
        # 306.2mV for 1000 code
        volt_per_code = 0.3062/1000.0;
        # 
        code_offset = 32768; # small offset + 2^15

        code_val = v*1.0/volt_per_code+code_offset;
        #print code_val;
        self.SPI_intensity_setpoint.set_value(code_val)   ;

    def set_SPI_setpoint_intenisty(self,p):
        volt_per_watt=-0.243*1510.0; 

        # PD reading, percentage of light to experiment
        PD_percent = 5.5/1000.0/10.0; # 6.7 # 5.8 #8.6

        voltage_val = p*PD_percent*volt_per_watt
        # print code_val
        self.set_SPI_setpoint_voltage(voltage_val)   

    # Switched DDS to controlling AOM directly
    # def set_IPG_modulation(self,F,A):
        # intended to be combined with set_IPG_AOM_analog_in_V dc output in minicircuits
        # combiner to modulate a given dc output level for the IPG AOM
        # Freq = F*MHz
        # print 'Tweezer modulation frequency is ',Freq
        # Amp = numpy.clip(A, 0, 1.0)  # Amp will be 1.0 maximum
        # print 'Tweezer amplitude  is ',Amp
        # self.tweezer_modulation.reset()
        # self.tweezer_modulation.single_tone(Freq)
        # self.tweezer_modulation.set_amplitude(Amp)
        
    def IPG_power_mod(self,time,freq_kHz,ampl,offset):
        # Drives the IPG AOM with a voltage signal that creates a sin wave of IPG power
        freq_Hz = freq_kHz*1e3
        for tt in range(0,time*1000,5):
            t = tt*1e-6
            power = ampl*numpy.sin(t*2*numpy.pi*freq_Hz)+offset
            self.set_IPG_power_DDS_control_W(power)
            self.wait_us(3.5)

    def ramp_IPG(self,time,T,V1,V2,limits=(0,1),dtmin_s=0):
        R = ramp(T=T,V1=V1,V2=V2)
        rampkw = dict(
            T = T,
            V1 = V1,
            V2 = V2
                )
        func = self.set_IPG_AOM_analog_in_V
        self.__ramp_function(func,time,limits=limits,dtmin_s=dtmin_s, **rampkw)

    def IPG_shutter(self,boolean):
        if boolean in ['True','T','on',1,'open']:
            #self.thin_fiber_shutter(0)
            self.fat_fiber_shutter(1)
        elif boolean in ['False','F','off',0,'closed']:
            self.fat_fiber_shutter(0)
            #self.thin_fiber_shutter(1)
    
    def IPG_shutter_open(self):
        self.fat_fiber_shutter(1)

    def IPG_shutter_close(self):
        self.fat_fiber_shutter(0)
    ###################################################################################
    ## SPI methods or properties
    ###################################################################################

    def spi_laser_off(self):
        self.spi_mod_control(0)

    def spi_laser_on(self):
        self.spi_mod_control(1)
        
    def spi_enable(self,boolean = False ):
        if boolean in ['True','T','on',1]:
            self.spi_mod_control(1)
        elif boolean in ['False','F','off',0]:
            self.spi_mod_control(0)
    
    #The laser is "on" in 400us
    def spi_control(self,val,boolean = False ,):
        if boolean in ['True','T','on',1]:
            self.spi_enable(1)
            if 2.0<val:
                self.spi_power_set_p(2)
            self.wait_ms(.3)
            self.spi_power_set_p(val)
        elif boolean in ['False','F','off',0]:
            self.spi_power_set_v(0)
            self.spi_enable(0)
        
    def spi_power_set_v(self,val):
        self.spi_voltage_control.set_scaled_value(val)

    def spi_power_set_p(self,val):
        set_volt = 0.0984196*val+1.00884
        set_volt_clipped = numpy.clip(set_volt,0,10)
        self.spi_voltage_control.set_scaled_value(set_volt_clipped)

    def spi_power_set_p_lock(self,val):
        
        # open loop, little attenuation after spi output
        if(val > 10):
            self.spi_power_set_p(val)
        # close loop, give actuator head room
        elif(val > 5):
            self.spi_power_set_p(10)
        # close loop, keeping actuator mid range
        elif(val > 0.15):
            self.spi_power_set_p(val*2.0)
        # close loop, park spi at a power level it favours
        else:
            self.spi_power_set_p(0.15)
        
        # intensity setpoint
        self.set_SPI_setpoint_intenisty(val)
        
    # note that this is the unlocked version! Still needs to be fixed
    def spi_power_mod(self,time,freq_MHz,ampl,offset,phase=0,t0=0,limits=(0,50),dtmin_s=0):
        #spi power mod requires: duration,freq,ampl,and offset 
        #optional args: t0,phase, and limit
        # modkw = dict(
            # frequency = freq_MHz*MHz,
            # amplitude = ampl,
            # offset = offset,
            # phase = phase,
            # t0 = t0,
                # )
        # func = self.spi_power_set_p
        # self.__modulate_function(func,time,limits=limits,dtmin_s=dtmin_s, **modkw)
        freq_Hz = freq_MHz*1e6
        for tt in range(0,time*1000,10):
            t = tt*1e-6
            power = ampl*numpy.sin(t*2*numpy.pi*freq_Hz)+offset
            self.spi_power_set_p(power)
            self.wait_us(9.25)


    # note that this is the locked version!
    def spi_power_ramp_locked(self, period, min_power, max_power, count):
        #spi_power_ramp_locked requires: period, min, max, count (number of repetition)
        for c in range(0, count):
            for tt in range(0,int(numpy.floor(period/1e-6/2)),10):
                # 10us time resolution
                t = tt*1e-6
                power = min_power+(max_power-min_power)*1.0/period*t*2
                self.spi_power_set_p_lock(power)
                # self.spi_power_set_p(power)
                self.wait_us(9.25)
            for tt in range(int(numpy.floor(period/1e-6/2)),int(numpy.floor(period/1e-6)),10):
                # 10us time resolution
                t = tt*1e-6
                power = max_power+(max_power-min_power)-(max_power-min_power)*1.0/period*t*2
                self.spi_power_set_p_lock(power)
                # self.spi_power_set_p(power)
                self.wait_us(9.25)
    
    def ipg_second_arm_mod(self,time,freq_kHz,ampl,offset,phase=0,t0=0,limits=(0,50),dtmin_s=0):
        # NOTE: This feeds to the function that converts a power to a AOM setting for the second arm of
        #       the IPG. This is NOT calibrated properly as of 2012/05/30...
        #       Can't really go much fast then 1/10us = 100kHz
        freq_Hz = freq_kHz*1e3
        for tt in range(0,time*1000,5):
            t = tt*1e-6
            # print ampl
            # print freq_Hz
            # print offset
            power = ampl*numpy.sin(t*2*numpy.pi*freq_Hz)+offset
            # print power
            self.set_IPG_cross_power_W(power)
            self.wait_us(3.3)
        
        
    #########################################
    ## High Voltage Power Suppply Settings ##
    #########################################
    
    def set_high_voltage_kV(self,voltage):
        voltage_clipped = numpy.clip(voltage,0,50)
        set_volt = (10.0/60.0)*voltage_clipped
        self.hv_supply_voltage_set.set_scaled_value(set_volt)
    
    def set_hv_relay_polarity(self,pol):
        if pol==1:
            self.hv_relay_control(1)
        if pol==0:
            self.hv_relay_control(0)
            
    def hv_voltage_control_on(self):
        self.hv_pot_control(1)
    
    def hv_voltage_control_off(self):
        self.hv_pot_control(0)
    
    ###################################################################################
    ## PA-light options including shutter and AOM settings
    ###################################################################################
    #shutter for the TiSapph laser light used for Photoassociation
    def PA_shutter_open(self):
        self.PA_shutter(1)
    def PA_shutter_closed(self):
        self.PA_shutter(0)

    def PA_shutter_open_nobounce7ms(self):
        self.PA_shutter(1)
        self.wait_ms(5.5)
        self.PA_shutter(0)
        self.wait_ms(1.5)
        self.PA_shutter(1)
    def PA_shutter_closed_nobounce7ms(self):
        self.PA_shutter(0)
        self.wait_ms(5.5)
        self.PA_shutter(1)
        self.wait_ms(1.5)
        self.PA_shutter(0)
        
    #on-off trigger and amplitude setting for the Photoassociation AOM
    def PA_AOM_on(self):
        self.PA_AOM_trigger(1)
    def PA_AOM_off(self):
        self.PA_AOM_trigger(0)
    def set_PA_AOM_amplitude(self,val):
        self.PA_AOM_amplitude.set_scaled_value(val)

    #complete turn on of the PA-light 
    def PA_light_on(self,PA_amplitude):
        self.PA_shutter(1)
        self.wait_ms(5.5)
        self.util_trig_high()
        if PA_amplitude==0:
            self.set_PA_AOM_amplitude(PA_amplitude)
            self.PA_AOM_off()
        else:
            self.set_PA_AOM_amplitude(PA_amplitude)
            self.PA_AOM_on()
        self.wait_ms(1.5)
        self.PA_shutter(0)
        self.wait_ms(1)
        self.PA_shutter(1)
    
    def PA_light_off(self):
        self.PA_shutter(0)
        self.wait_ms(4.3)
        self.set_PA_AOM_amplitude(1)
        self.PA_AOM_on()
        self.util_trig_low()
        self.wait_ms(1.7)
        self.PA_shutter(1)
        self.wait_ms(1)
        self.PA_shutter(0)

    def PA_light_enable(self,PA_amplitude,boolean = False ):
        if boolean in ['True','T','on',1]:
            self.PA_light_on(PA_amplitude)
        elif boolean in ['False','F','off',0]:
            self.PA_light_off()
     
    ###################################################################################
    ## Rb state selection (SS) methods or properties
    ###################################################################################
       
    def _RbSS_set(self, chan = 1, ampl = 0): # sets switches and voltage contralled attenuator

        self.RbSS_switch(0)
        self.RbSS_FSK(0)
        self.RbSS_setpoint.set_scaled_value(0)
        if chan == 1:
            self.RbSS_sel(0) # Sets 3.0 GHz path
            if ampl == 1:
                ampl = 3.5
            elif ampl > 0:
                if ampl < -30:
                    ampl = -30
                    print "Requested RbSS power output exceeded minimum.  Power set to minimum, -30dB."
                ampl = 7.82-0.137*ampl-0.256e-3*ampl**2#((-ampl+79.6)/.124)**0.5 - 21.45
            else:
                if ampl != 0:
                    print "Invalid RbSS setpoint.  Power off."
                ampl = 0
        elif chan == 2:
            self.RbSS_sel(1) # Sets 6.8GHz path
            if ampl == 1:
                ampl = 5.2
            elif ampl < 0:
                if ampl < -32.84:
                    ampl = -32.84
                    print "Requested RbSS power output exceeded minimum.  Power set to minimum, -32.84dB."
                ampl = (-ampl+36)/6.884
            else:
                if ampl != 0:
                    print "Invalid RbSS setpoint. Power off."
                ampl = 0
        else:
            self.RbSS_sel(0)
        self.RbSS_setpoint.set_scaled_value(ampl) # Sets VCA and PiN switch

    def RbSS_on(self, on = 1):
        self.RbSS_switch(on)
        
    def RbSS_single_tone(self, freq, ampl = 0, test = False): # sets single tone signal to prepare loop.

        self.RbSS_ref.reset()
        self.RbSS_ref.set_amplitude(0.7)
        if freq < 5*GHz: # Check if 3 or 6.8GHz path is to be used
            chan = 1
            self.RbSS_ref.single_tone(freq / D['phaseDetectorSetting_xN'] / 8)
        else:
            chan = 2
            self.RbSS_ref.single_tone(freq / D['phaseDetectorSetting_xN'] / 16)
            
        if not ampl == 0:
            self._RbSS_set(chan, ampl)
            # self.wait_ms(20) # wait for frequency to stabilize.  Takes care of worst case.
            if test:#(not test) or ampl == 0:
                self.RbSS_switch(1)
        else:
            self._RbSS_set()

    def RbSS_ramp(self, f1, fdelta, rate, ampl = 1): # Set rampable signal controlled by digital output.  Prepare loop using RbSStone before using this method.

        f1 /= D['phaseDetectorSetting_xN'] * 8
        fdelta /= D['phaseDetectorSetting_xN'] * 8
        rate /= D['phaseDetectorSetting_xN'] * 8
        chan = 1

        if max(f1, f1+fdelta) > 100*MHz: # Check if 6.8GHz path is to be used
            f1 /= 2
            fdelta /= 2
            rate /= 2
            chan = 2


        self.RbSS_FSK(0)
        self.RbSS_ref.ramped_FSK(f1, f1+fdelta, fdelta*1./rate)
        self.RbSS_ref.set_amplitude(0.7)

        self._RbSS_set(chan, ampl)
        self.wait_ms(.5) # wait for loop to stabilize after DDS transient.
        if not ampl==0:
            self.RbSS_switch(1)
        # self.wait_ms(0.1) # wait for switch to stabilize
        self.wait_ms(6) # wait for switch to stabilize
        self.RbSS_FSK(1)
        self.wait_s(fdelta*1./rate+0.001)
        self._RbSS_set(chan, 0)
        self.RbSS_FSK(0)

    def LiSS_ramp(self):
        self.RbSS_FSK(0)

        self.LiSS.ramped_FSK(70, 80, 1)
        self.LiSS.set_amplitude(1)
        self.wait_ms(10)
        self.RbSS_FSK(1)
        self.wait_s(2)
        self.RbSS_FSK(0)

    ###################################################################################
    ## Standford Reasearch DS345 Methods
    ###################################################################################
    def set_Sinewave_parameters(self,frequency,amplitude,offset,comAddress):
        freq = frequency*1e3
        fgen = serial.Serial(comAddress,timeout=1, bytesize=8, baudrate=9600,stopbits=2, parity=serial.PARITY_NONE) #open Serial port
        fgen.write('func 0 \n')
        ldstring='FREQ'+str(freq)
        fgen.write(ldstring+' \n')
        ldstring='AMPL'+str(amplitude)+'VP'
        fgen.write(ldstring +' \n')
        ldstring='OFFS'+str(offset)
        fgen.write(ldstring +' \n')
        fgen.close()
    
    def TS1_DS345_trigger(self):
        self.TS1_DS345_Trig(1)
        self.TS1_DS345_Trig(0)
    
    def TS2_DS345_trigger(self):
        self.TS2_DS345_Trig(1)
        self.TS2_DS345_Trig(0)
            
    def DS345_set_offset(self, comAddress, offset):
        #comAdress: serial address of DS345 to find go to control panel->system->hardware->device manager->ports(com &LPI)
        #take the comp port and -1 i.e. com4 means comAddress=3
        #offset: desired DC offset in volts
        offset=offset/2. #in volts
        fgen = serial.Serial(comAddress,timeout=1, bytesize=8, baudrate=9600,stopbits=2, parity=serial.PARITY_NONE) 
        ldstring='OFFS'+str(offset)
        fgen.write(ldstring+' \n')
        fgen.close()
        
    def DS345_load_gaussian_wavefrom(self, comAddress, amplitude, delay, sigma, alpha=0):
        #comAdress: serial address of DS345 to find go to control panel->system->hardware->device manager->ports(com &LPI)
        #take the comp port and -1 i.e. com4 means comAddress=3
        #amplitude: amplitude of pulse in volts (max 10)
        #delay: delay from start of waveform to peak in us
        #simga: sigma of peak in us
        #alpha: control parameter between -1 and 1 to skew peak shape 

        amplitude=min(amplitude,10.)
        amplitude=amplitude/10.*2045.; 
        delay_Time=delay*10**(-6); #delay in us between start and peak location
        sigma_Time=sigma*10**(-6);  #sigma of pulse in us
        peakPoints=1000; #number of data points between -3sigma to +3sigma
        frequency=peakPoints/(6*sigma_Time); 
        if frequency>40e6:
            print 'resolution limit exceeded'
            frequency=40e6;
            peakPoints=frequency*6*sigma_Time;

        frequency=round(frequency);
        N=round(40e6/frequency);
        frequency=40e6/N;
        peakPoints=frequency*6*sigma_Time;
        dT=1/frequency;
        delay=round(delay_Time/dT);
        sigma=round(sigma_Time/dT);
        x=numpy.linspace(0,delay+peakPoints,delay+peakPoints+1)

        fgen = serial.Serial(comAddress,timeout=1, bytesize=8, baudrate=9600,stopbits=2, parity=serial.PARITY_NONE) #open Serial port


        alpha=alpha/sigma;

        if alpha==0:
            waveform= numpy.round(amplitude*numpy.exp(-(x-delay)**2/(2*sigma**2)))
        else:
            g=(1+special.erf(alpha*numpy.sqrt(sigma/2)*(x-delay)))/4
            waveform = (g*numpy.exp(-(x-delay)**2/(2*sigma**2)))
            waveform = waveform/max(waveform)
            waveform = numpy.round(amplitude*waveform)

        lengthData = len(waveform)
        checkSum= 0
        for iDataItem in range(lengthData):
            checkSum = int(checkSum + waveform[iDataItem])
        checkSum=checkSum%2**16

        ldstring='OFFS'+str(0.)
        fgen.write(ldstring+' \n')

        ldstring='ldwf?0'+','+str(lengthData)
        fgen.write(ldstring+' \n')
        reply = fgen.readline()
        for iDataItem in range(lengthData):
            fgen.write(pack('h',waveform[iDataItem]))
        fgen.write(pack('H',checkSum))
        fgen.write('func 5 \n')
        ldstring='FSMP'+str(frequency)
        fgen.write(ldstring+' \n')
        ldstring='AMPL'+str(10.)+'VP'
        fgen.write(ldstring+' \n')
        fgen.close()
        
        
    def DS345_load_ramp(self, comAddress, amplitude, hilo, rampTime, t1, t2 ):
        t1=t1*10**-6;
        t2=t2*10**-6;
        
        rampTime=rampTime*10**-6;
        numPoints=1000.;
        t_total= rampTime+t1+t2
        dt=t_total/numPoints;

        frequency=1/dt
        frequency=round(frequency);
        N=round(40e6/frequency);
        frequency=40e6/N;
        dt=1/frequency

        stopup = 4
        stopdown= 6
        if frequency>40e6:
            print 'resolution limit exceeded'
            frequency=40e6;

        if hilo:
            region1=numpy.zeros(round(t1/dt));
            region2=10.*numpy.ones(round(t2/dt));
            region3=numpy.linspace(10,0,round(rampTime/dt))
            waveform=numpy.concatenate((region1, region2, region3))

        else:
            # print 'rampTime',rampTime
            
            
            fracup = 0.70
            fracdw = 0.40

            region1=numpy.zeros(round(t1/dt));
            # region2=numpy.linspace(0,10,round(rampTime/dt))
            region2=numpy.linspace(0,stopup,round((fracup*rampTime)/dt))
            region3=numpy.linspace(stopup,10,round(((1-fracup)*rampTime)/dt))
            region4=10.*numpy.ones(round((t2)/dt));
            region5=numpy.linspace(10,stopdown,round(((1-fracdw)*rampTime)/dt))
            region6=numpy.linspace(stopdown,0,round((fracdw*rampTime)/dt))
            # region4=5.*numpy.ones(round(t1/dt));
            region7=numpy.zeros(round(t1/dt));
            waveform=numpy.concatenate((region1, region2, region3, region4,region5,region6,region7))    
            # waveform=numpy.concatenate((region1,region4,region7))  
        amplitude=min(amplitude,10)
        
        waveform=amplitude*2045*waveform/100.

        fgen = serial.Serial(comAddress,timeout=1, bytesize=8, baudrate=9600,stopbits=2, parity=serial.PARITY_NONE)

        lengthData = len(waveform)
        checkSum= 0
        for iDataItem in range(lengthData):
            checkSum = int(checkSum + waveform[iDataItem])
        checkSum=checkSum%2**16    

        ldstring='OFFS'+str(0.)
        fgen.write(ldstring+' \n')
        
        ldstring='ldwf?0'+','+str(lengthData)
        fgen.write(ldstring+' \n')
        reply = fgen.readline()
        for iDataItem in range(lengthData):
            fgen.write(pack('h',waveform[iDataItem]))
        fgen.write(pack('H',checkSum))
        fgen.write('func 5 \n')
        ldstring='FSMP'+str(frequency)
        fgen.write(ldstring+' \n')
        ldstring='AMPL'+str(10.)+'VP'
        fgen.write(ldstring+' \n')
        fgen.close()
    
    def DS345_load_staircase(self, comAddress, times, setPoints):

        numPoints=100.;
        times=numpy.array(times)
        times=times*10**-6
        t_total=max(times)
        dt=t_total/numPoints;
        frequency=1/dt
        frequency=round(frequency);
        N=round(40e6/frequency);
        if N==0:
            N=N+1
        frequency=40e6/N;
        dt=1/frequency


        if frequency>40e6:
            print 'resolution limit exceeded'
            frequency=40e6;
            
        if setPoints[0]>10:
            setPoints[0]=10
            
        waveform=numpy.linspace(setPoints[0],setPoints[1],round((times[1]-times[0])/dt))

        for i in range(len(times)-2):
            index=i+1;
            if setPoints[index+1]>10:
                setPoints[index+1]=10
            nextRegion=numpy.linspace(setPoints[index],setPoints[index+1],round((times[index+1]-times[index])/dt))
            waveform=numpy.concatenate((waveform, nextRegion))

        waveform=2045*waveform/10.



        fgen = serial.Serial(comAddress,timeout=1, bytesize=8, baudrate=9600,stopbits=2, parity=serial.PARITY_NONE)

        lengthData = len(waveform)
        checkSum= 0
        for iDataItem in range(lengthData):
            checkSum = int(checkSum + waveform[iDataItem])
        checkSum=checkSum%2**16  

        ldstring='OFFS'+str(0.)
        fgen.write(ldstring+' \n')  

        ldstring='ldwf?0'+','+str(lengthData)
        fgen.write(ldstring+' \n')
        reply = fgen.readline()
        for iDataItem in range(lengthData):
            fgen.write(pack('h',waveform[iDataItem]))
        fgen.write(pack('H',checkSum))
        fgen.write('func 5 \n')
        ldstring='FSMP'+str(frequency)
        fgen.write(ldstring+' \n')
        ldstring='AMPL'+str(10.)+'VP'
        fgen.write(ldstring+' \n')
        fgen.close()
        
        
    def DS345_load_exp(self, comAddress, rising, twoStep, tau, t, t_hold, tau2=0, t2=0, t_hold2=0, waitTime=0):

        numPoints=100.;
        waitTime=waitTime*10**-6
        t=t*10**-6
        t2=t2*10**-6
        t_hold=t_hold*10**-6
        t_hold2=t_hold2*10**-6
        tau=tau*10**-6
        tau2=tau2*10**-6
        t_total=t+t_hold+t2
        dt=t_total/numPoints;
        tau=tau/dt
        tau2=tau2/dt
        frequency=1/dt
        frequency=round(frequency);
        N=round(40e6/frequency);
        if N==0:
            N=N+1
        frequency=40e6/N;
        dt=1/frequency


        if frequency>40e6:
            print 'resolution limit exceeded'
            frequency=40e6;
            
        x=numpy.linspace(0,round(t/dt),round(t/dt)+1)
        if rising==1: 
            Rzeros=numpy.zeros(round(waitTime/dt))
            R1=10.*(1-numpy.exp(-x/tau))
            R2=10.*numpy.ones(round(t_hold/dt))
            if twoStep==1:
                x2=numpy.linspace(0,round(t2/dt),round(t2/dt)+1)
                R3=10.*numpy.exp(-x2/tau2)
                R4=numpy.zeros(round(t_hold2/dt))
                waveform=numpy.concatenate((Rzeros,R1,R2,R3,R4)) 
            else:    
                waveform=numpy.concatenate((R1,R2))  
            
        else:
            bufferTimes=20*10**-6
            Rzeros=numpy.zeros(round(bufferTimes/dt))
            Rhigh=10*numpy.ones(round(bufferTimes/dt))
            R1=10.*(numpy.exp(-x/tau))
            R2=numpy.zeros(round(t_hold/dt))
            if twoStep==1:
                x2=numpy.linspace(0,round(t2/dt),round(t2/dt)+1)
                R3=10.*(1-numpy.exp(-x/tau2))
                R4=10*numpy.ones(round(t_hold2/dt))
                waveform=numpy.concatenate((Rzeros,Rhigh,R1,R2,R3,Rhigh,Rzeros)) 
            else:    
                waveform=numpy.concatenate((R1,R2))  

        waveform=2045*waveform/10.
        
        fgen = serial.Serial(comAddress,timeout=1, bytesize=8, baudrate=9600,stopbits=2, parity=serial.PARITY_NONE)

        lengthData = len(waveform)
        checkSum= 0
        for iDataItem in range(lengthData):
            checkSum = int(checkSum + waveform[iDataItem])
        checkSum=checkSum%2**16  

        ldstring='OFFS'+str(0.)
        fgen.write(ldstring+' \n')  

        ldstring='ldwf?0'+','+str(lengthData)
        fgen.write(ldstring+' \n')
        reply = fgen.readline()
        for iDataItem in range(lengthData):
            fgen.write(pack('h',waveform[iDataItem]))
        fgen.write(pack('H',checkSum))
        fgen.write('func 5 \n')
        ldstring='FSMP'+str(frequency)
        fgen.write(ldstring+' \n')
        ldstring='AMPL'+str(10.)+'VP'
        fgen.write(ldstring+' \n')
        fgen.close()        
        

    ###################################################################################
    ## RF methods or properties
    ###################################################################################
       
    #    def enable_RF_SingleTone(self,f1,amp):
    #       self.Microwave.reset()
    #        self.Microwave.single_tone(f1)
    #        self.Microwave.set_amplitude(amp)
    #    
    #    def enable_RF(self,f1,f2,amp,framp):
    #        DT=1.0/framp
    #        self.Microwave_FSK.enable_comp()
    #        self.Microwave_FSK.enable_control_DAC()
    #        self.Microwave_FSK.single_tone(framp)
    #        self.Microwave.reset()
    #        self.Microwave.ramped_FSK(f1,f2,DT)
    #        self.Microwave.set_amplitude(amp)
    #
    #    def disable_RF(self):
    #        self.Microwave.set_amplitude(0)

    #    def enable_RF_SingleTone(self,f1,amp):
    #       self.Microwave.reset()
    #        self.Microwave.single_tone(f1)
    #        self.Microwave.set_amplitude(amp)
    #    
    #    def enable_RF(self,f1,f2,amp,framp):
    #        DT=1.0/framp
    #        self.Microwave_FSK.enable_comp()
    #        self.Microwave_FSK.enable_control_DAC()
    #        self.Microwave_FSK.single_tone(framp)
    #        self.Microwave.reset()
    #        self.Microwave.ramped_FSK(f1,f2,DT)
    #        self.Microwave.set_amplitude(amp)
    #
    #    def disable_RF(self):
    #        self.Microwave.set_amplitude(0)
