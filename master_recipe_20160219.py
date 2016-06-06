'''
modified by Bruce Klappauf
try to add ability to capture the loaded mot fluorescence with pixelink just before
experiment.  add triggers into load_atoms function.
add value 'bool_loaded_mot_flourescence_imaging' to tell it to do this.
add keyword to load_atoms with default value so should not effect previous scripts

090915 changed offset field turnon, first ramp up z-field, then reduce x- and y-field to compensation values

091006 added a oscillating turn on/off of the repump AOM to adjust the mot

091021 added Li load and imaging 

091022 changes to evaporative cooling, two separate cooling stages for SPI and IPG respectively

091023 work on Li Absorption routines

091023_1 work on Li dipole trap routines

091027_0 changing some settings from the previous working Li trapping recipes like the pumping

091027_1 changes in the absorption image, moved the first dark image into the mot loading, if not in tweezer

091028_0 changes in the Li fl image, put tweezers on b4 bkgnd. added cooling ramp

091028_1 changes in the IPG loading, now it's possible to first cool the mot 
at the position of the IPG beam, then turn on the IPG and change the detunings 
and powers for proper loading. The variables used for the mot cooling are the comp_cool
(no extension), and the cool_mot detunings and amplitudes.

091030_0 start adding ipg to li 

091030_1 added boolean (S.bool_Rb87) to switch between Rb85 and Rb87 settings

091103_0 included UV_lamp for mot loading

091105_0 added separate IPG loading ramp for the SPIPG setting making it possible to load atoms in the SPI and then turn on the IPG

091117_1 added leave mot on variable for end of recipe

091208_0 added molasses cooling for Rb
wo
091209_0 added cooling stage for Rb into mot loading

091211_0 changed Li cool to compress and added Feshbach hold to tweezer hold

091214_2 implemented dual load for mot and SPI.  made dual load set and changed 
load mot to use those. added start load commands for this. add many settings,
L/R mot coil grad, L/R load mot_s, Load tweezer was changed a little to acount 
not closing mot shutter always, and having a SPI settling time. tried to move 
rb mot during this but didn't see much effect.

091216_0  implemented dual transfer to IPG, although it is normally quite bad.  
at it works.  need to use bool_Rb_absorption_image or bool_Li_absorption_image
to get image

20010114_0 change Li imaging to use Li mot shutters instead of old mot shutter.
20100217_1 put in function to do pump imaging for Li, and to use various options for 
    repump during image (fiber or mot repump or none). 

20100226_0 changed Rb feshbach using the same functions as for Li

20100302_0 -bruce- added commands for new dual load of Rb onto IPG with Li loaded.

20100322_0 -ben- changed Raman stage magnetic field setting to polar coordinate system

20100325_0 -ben- added drsc_cycle_sequence for raman field and pumping in an alternating loop

20100421_0 -ben- slight changes to the Rb only feshbach field

20100422_0 -bruce added function to set feshbach field in Gauss using calibration values 
        (slope and offset) to be set in settings file.  Works with new setting variables
        for feshbach field given in Gauss ending in _G.  changed some names for Li and dual
        fb variable to be more descriptive than _1 _2.

20100429_0 - added option to cycle mot coils off after every shot to reset coils. usefull if running
fb field. also added rb_repump_shutter turnoff after traploading. initalize shutter commands
at start of sequence

20100623 - replaced the repump mot shutter which was called "repump_shadow_only(0/1)" with the command
"X.Rb_repump_mot_shutter_open/closed()"

20100623 - added depumping along xy axis

20100913 -ben- implemented nobounce shutter controller for Rb-Mot shutter (X.mot_shutter_) changed timing accordingly.

20100915 -ben- replaced Rb_optical_pumping_shutter by main_optical_pump_srs_shutter and adjusted timing

20101013 -ben- replaced optical_pump_shutter by optical_depump_srs_shutter

20110509 -bruce- added statements for using the high field imaging beam with 
bool_high_field_imaging.

20120221  - Swichted control of IPG AOM driver from AO to DDS to cut back on light leakage... this resulting in replacing two 
sets of commands:
set_IPG_AOM_analog_in_V with set_IPG_AOM_driver_input_amplitude
set_IPG_power_W with set_IPG_power_DDS_control_W
left variables the same

all comands that deal with IPG modulation have been commented out, since they will not work anymore

20150628 - Changed S.wait_Li_mw_transfer to S.wait_Li_mw_transfer_ms to make units clear - Kahan
'''

from UTBus1.Experiments.MOLExperimentRecipe_20151216 import MOLExperimentRecipe as Recipe
# from UTBus_Recipesb.tool_scripts.MyClients import WaveClient
# wavemeter = WaveClient()

from UTBus_Recipesb.tool_scripts.WavemeterDummyClient import WavemeterClient # Dummy Wavemeter Client
#from UTBus_Recipesb.tool_scripts.WavemeterClient import WavemeterClient      # Real Wavemeter Client.
wavemeter = WavemeterClient()


import math
import scipy.special
import serial
import numpy
import os
import sys
sys.path.insert(0, 'C:\UTBus_Recipesb\public_scripts')
from debugger import debug

#######################################################################################
## Functions used in a single Sequence
#######################################################################################
   
print '================================================'
print 'Master Recipe: ',os.path.basename(__file__)
print '================================================'
        
## Program part to load atoms into trap
def load_atoms(X,S,set_only=False,label='motimage_%i',takeimage=True):
    # set_only means it just sets the basic values but doesn't wait for any load time.
    if S.bool_loaded_mot_flourescence_imaging_pixelink and takeimage:
        X.trigger_pixelink('dark_%i')       # trigger camera for flush 
        X.wait_ms(S.Pixelink.expTime_ms)
        X.wait_ms(S.Pixelink.wait_ms)  
        
    if S.bool_Rb and S.bool_Li:
        # print "****************in dual mot load"
        if 1:#S.bool_tweezer_load_Rb_on_Li:
            set_Rb_load(X,S) 
            start_Rb_load(X,S) #let the rb maybe collect some atoms without really trying
            set_Li_load(X,S)
            start_Li_load(X,S)
            if not set_only:
                X.wait_s(S.Li6.loadmot_s)
            
        else:
            # loads Li then Rb with the intent that Rb will probably be loaded in dipole trap first.
            set_Li_load(X,S)
            start_Li_load(X,S)
            if not set_only:
                X.wait_s(S.Li6.loadmot_s)
            X.set_mot_coil_I(S.mot_coil_gradient_dualLoad_A)
            set_dualLoad(X,S)
            start_Rb_load(X,S)
            if not set_only:
                X.wait_s(S.Rb.loadmot_s)
                if S.bool_mot_cooling_stage: #this may hurt li mot because of coil setting
                    mot_cooling_stage(X,S)
     
    elif S.bool_Rb: 
        X.Li_MOT_shutter_close()
        
        set_Rb_load(X,S) 
        start_Rb_load(X,S)

        if not set_only: 
            X.wait_s(S.Rb.loadmot_s) 

     
            
    elif S.bool_Li: 
        #X.Rb_repump_mot_shutter_closed()
        #X.mot_shutter_off()
        set_Li_load(X,S)
        start_Li_load(X,S)
        if not set_only:
            X.wait_s(S.Li6.loadmot_s)
    
    if S.bool_loaded_mot_flourescence_imaging_apogee and takeimage:
        apogee_mot_floresence(X,S)
        set_Li_load(X,S)
        X.wait_ms(S.Apogee.wait_ms) # to give the apogee time to finish
        
    if S.bool_loaded_mot_flourescence_imaging_pixelink and takeimage:
        X.Rb_pump.set_amplitude(S.Rb.pump_cool_ampl)
        X.trigger_pixelink(label)       # trigger camera for motimage
        set_mot_imaging(X,S)
        X.wait_ms(S.Pixelink.expTime_ms)
        if S.bool_Rb:
            set_Rb_load(X,S)
        if S.bool_Li:
            set_Li_load(X,S)
        X.wait_ms(S.Pixelink.wait_ms)  
        
def init_shutters(X,S):
    
    if S.bool_Rb and S.bool_Li:
        pass
    
    elif S.bool_Rb: 
        pass
    
    elif S.bool_Li:
        X.Li_MOT_shutter_open()
        
    if S.bool_zeeman_slower:
        X.Zeeman_Slower_shutter_open()   # temp ZS shutter
         
    X.Li_pump_abs_shutter_close()
    X.Li_repump_abs_shutter_close()
    X.Li_HF_imaging_shutter_closed()
    
    # All shutters that should be closed for MOT loading. Or Else. 
    X.Rb_abs_shutter_off()
    X.optical_depump_srs_shutter_closed()
    X.main_optical_pump_srs_shutter_closed()
    X.fat_fiber_shutter(0)
    
            
def start_Rb_load(X,S):
    X.Rb_repump.set_amplitude(S.Rb.repump_load_ampl)
    X.Rb_pump.set_amplitude(S.Rb.pump_load_ampl)
    X.set_Rb85_zeeman_slower_amplitude(S.Rb.slowing_beam_ampl)
    
def start_Li_load(X,S):
    X.set_Li_pump_amplitude(S.Li6.pump_load_amplitude)
    X.set_Li_repump_amplitude(S.Li6.repump_load_amplitude)
    X.set_Li_zeeman_slower_amplitude(S.Li6.slowing_beam_AOM_amplitude)
    
            
def set_Rb_load(X,S):                                                  # sets values for loading atoms     
    X.set_comp_coils_V(S.Rb.compx_load,S.Rb.compy_load,S.Rb.compz_load)      # set compensation coils
    X.set_zeeman_coil_I([1,2,3,4,5,6,7,8],[S.Rb.zeeman_coil_1_I,S.Rb.zeeman_coil_2_I,S.Rb.zeeman_coil_3_I,S.Rb.zeeman_coil_4_I,S.Rb.zeeman_coil_5_I,S.Rb.zeeman_coil_6_I,S.Rb.zeeman_coil_7_I,S.Rb.zeeman_coil_8_I])
    X.Rb_pump.set_amplitude(0)
    X.Rb_repump.set_amplitude(0)
    X.set_Rb85_repump_dF(S.Rb.repump_load_dF)                     # set repump frequency
    X.set_Rb85_pump_dF(S.Rb.pump_load_dF)                         # set pump frequency
    X.set_Rb85_zeeman_slower_dF(S.Rb.slowing_beam_dF)      
    #X.set_Rb85_pump_ramped_dF(-25, -15, .0001)
    
def set_Li_load(X,S):      
    X.set_comp_coils_V(S.Li6.compx_load,S.Li6.compy_load,S.Li6.compz_load)      # set compensation coils    
    X.set_zeeman_coil_I([1,2,3,4,5,6,7,8],[S.Li6.zeeman_coil_1_I,S.Li6.zeeman_coil_2_I,S.Li6.zeeman_coil_3_I,S.Li6.zeeman_coil_4_I,S.Li6.zeeman_coil_5_I,S.Li6.zeeman_coil_6_I,S.Li6.zeeman_coil_7_I,S.Li6.zeeman_coil_8_I])
    X.set_Li_pump_amplitude(0)
    X.set_Li_repump_amplitude(0)
    X.set_Li_pump_dF(S.Li6.pump_load_dF)
    X.set_Li_repump_dF(S.Li6.repump_load_dF)
    X.set_Li_zeeman_Slower_F(S.Li6.slowing_beam_AOM_frequency)      
              
    
def set_dualLoad(X,S):
    # print '*************in dual load set'    
    X.set_comp_coils_V(S.compx_dualLoad,S.compy_dualLoad,S.compz_dualLoad)                        # set pump EO
    X.Rb_pump.set_amplitude(S.Rb.pump_dual_load_ampl)
    X.set_Rb85_repump_dF(S.Rb.repump_dualLoad_dF)                     # set repump frequency
    X.set_Rb85_pump_dF(S.Rb.pump_dualLoad_dF)                         # set pump frequency
    X.set_Li_pump_amplitude(S.Li6.pump_dualLoad_amplitude)
    X.set_Li_pump_dF(S.Li6.pump_dualLoad_dF)
    X.set_Li_repump_amplitude(S.Li6.repump_dualLoad_amplitude)
    X.set_Li_repump_dF(S.Li6.repump_dualLoad_dF)    
    
def mot_cooling_stage(X,S):                        # set pump EO
    X.Rb_pump.set_amplitude(S.Rb.pump_mot_cooling_stage_ampl)
    X.Rb_repump.set_amplitude(S.Rb.repump_mot_cooling_stage_ampl)
    X.set_Rb85_repump_dF(S.Rb.repump_mot_cooling_stage_dF)                     # set repump frequency
    X.set_Rb85_pump_dF(S.Rb.pump_mot_cooling_stage_dF)                         # set pump frequency
    X.set_mot_coil_I(S.mot_cooling_stage_coil_gradient_A)
    X.wait_s(S.duration_mot_cooling_stage_s)
    
def Rb_pump_detuning_change(X,S):
    X.set_Rb85_pump_dF(S.Rb.pump_detuning_check_dF)
    X.wait_ms(S.pump_detuning_check_wait_ms)
 
def mot_oscillation(X,S):
    X.wait_ms(S.wait_mot_oscillation_ms)
    for tt in range(S.repetitions_mot_oscillation):
        X.set_Rb85_repump_dF(S.repump_mot_oscillation_dF)
        X.wait_ms(S.offtime_mot_oscillation_ms)
        X.set_Rb85_repump_dF(S.Rb.repump_load_dF)
        X.wait_ms(S.ontime_mot_oscillation_ms)

def coil_supply_cycle(X,S):
        X.mot_coil_set_polarity_10ms('antihelmholtz')
        X.set_mot_coil_I(10)
        X.fb_coils_supply_output_off()
        X.wait_ms(150)
        X.fb_coils_supply_output_on()
        X.wait_ms(5)
        X.set_mot_coil_I(0)
  
def high_anithelmoltz_field(X,S):
        X.mot_coil_set_polarity_10ms('antihelmholtz')
        X.set_mot_coil_I(S.current_high_antihelmoltz_field_A)
        X.wait_ms(S.hold_high_antihelmoltz_field_ms)
        X.set_mot_coil_I(0)
        X.wait_ms(S.wait_after_high_antihelmoltz_field_ms)
        
def cool_mot(X,S):                              # sets values for cooling atoms in the mot before loading into the dipole trap or magnetic trap
    X.Rb_pump.set_amplitude(S.Rb.pump_cool_ampl)    
    X.Rb_repump.set_amplitude(S.Rb.repump_cool_mot_ampl)
    X.set_Rb85_pump_dF(S.Rb.pump_cool_mot_dF)
    X.set_Rb85_repump_dF(S.Rb.repump_cool_mot_dF)
    X.set_comp_coils_V(S.Rb.compx_cool,S.Rb.compy_cool,S.Rb.compz_cool)
   
def move_Rb_mot(X,S):
    ## moves Rb MOT to the dipole trap, and allows it to reload for some time
    ## uses the same settings as trap loading for now (as of 2010/01/15)                       # set pump EO
    # X.Rb_pump.set_amplitude(S.Rb.pump_load_ampl)
    # X.set_Rb85_repump_dF(S.Rb.repump_load_dF)                     # set repump frequency
    # X.set_Rb85_pump_dF(S.Rb.pump_load_dF)
    # X.Rb_repump.set_amplitude(S.Rb.repump_load_ampl)
    X.Rb_pump.set_amplitude(S.Rb.pump_cool_ampl)
    X.Rb_repump.set_amplitude(S.Rb.repump_cool_ampl)
    X.set_Rb85_pump_dF(S.Rb.pump_cool_dF)
    X.set_Rb85_repump_dF(S.Rb.repump_cool_dF)
    if S.bool_SPI or S.bool_SPIPG:
        X.set_comp_coils_V(S.Rb.compx_cool_SPI,S.Rb.compy_cool_SPI,S.Rb.compz_cool_SPI)
    else:
        X.set_comp_coils_V(S.Rb.compx_cool_IPG,S.Rb.compy_cool_IPG,S.Rb.compz_cool_IPG)

def molasses_cooling(X,S):
    
    # Start by compressing the MOT
    if S.bool_molasses_initial_compression:
        X.set_mot_coil_I(S.molasses_compress_coil_gradient_A)
        X.set_comp_coils_V(S.compx_molasses,S.compy_molasses,S.compz_molasses)
        X.Rb_pump.set_amplitude(S.Rb.pump_molasses_compress_ampl)
        X.Rb_repump.set_amplitude(S.Rb.repump_molasses_compress_ampl)
        X.set_Rb85_pump_dF(S.Rb.pump_molasses_compress_dF)
        X.set_Rb85_repump_dF(S.Rb.repump_molasses_compress_dF)
        X.wait_ms(S.duration_molasses_compress_cooling_ms)
        
    # Next, detune without field and cool
    # X.Rb_pump.set_amplitude(S.Rb.pump_molasses_ampl)
    # X.Rb_repump.set_amplitude(S.Rb.repump_molasses_ampl)
    # X.set_Rb85_pump_dF(S.Rb.pump_molasses_dF)
    # X.set_Rb85_repump_dF(S.Rb.repump_molasses_dF)
    # X.set_comp_coils_V(S.compx_molasses,S.compy_molasses,S.compz_molasses)
    # X.set_mot_coil_I(S.molasses_coil_gradient_A)
    # X.wait_ms(S.duration_molasses_cooling_ms)

def Rb_pump_dF_change(X,S): 
    Rb_pump_dF_change_difference = S.Rb_pump_high_field_load_dF - S.Rb.pump_load_dF
    time_step_us = 100                                                    # time step between power changes in us
    dF_step = (Rb_pump_dF_change_difference*time_step_us) / (S.duration_Rb_pump_dF_change_ms *1e3)
    Rb_pump_dF_temp = S.Rb.pump_load_dF
    X.set_Rb85_pump_dF(Rb_pump_dF_temp)
    # print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    # print dF_step
    # print int((S.duration_Rb_pump_dF_change_ms*1e3)/time_step_us)
    for tt in range(int((S.duration_Rb_pump_dF_change_ms*1e3)/time_step_us)):
        X.wait_us(time_step_us)
        time_elapsed_ms = tt*time_step_us*1e-3
        Rb_pump_dF_temp = Rb_pump_dF_temp + dF_step
        X.set_Rb85_pump_dF(Rb_pump_dF_temp)

def Rb_pump_repump_dF_change(X,S): 
    Rb_repump_dF_change_difference = S.Rb_repump_high_field_load_dF - S.Rb.repump_load_dF
    Rb_pump_dF_change_difference = S.Rb_pump_high_field_load_dF - S.Rb.pump_load_dF
    
    time_step_us = 100                                                    # time step between power changes in us
    
    dF_step_repump = (Rb_repump_dF_change_difference*time_step_us) / (S.duration_Rb_repump_dF_change_ms *1e3)
    dF_step_pump = (Rb_pump_dF_change_difference*time_step_us) / (S.duration_Rb_pump_dF_change_ms *1e3)
    
    Rb_repump_dF_temp = S.Rb.repump_load_dF
    X.set_Rb85_repump_dF(Rb_repump_dF_temp)
    
    Rb_pump_dF_temp = S.Rb.pump_load_dF
    X.set_Rb85_pump_dF(Rb_pump_dF_temp)
    
    for tt in range(int((S.duration_Rb_repump_dF_change_ms*1e3)/time_step_us)):
        X.wait_us(time_step_us)
        time_elapsed_ms = tt*time_step_us*1e-3
        Rb_repump_dF_temp = Rb_repump_dF_temp + dF_step_repump
        Rb_pump_dF_temp = Rb_pump_dF_temp + dF_step_pump
        X.set_Rb85_repump_dF(Rb_repump_dF_temp)
        X.set_Rb85_pump_dF(Rb_pump_dF_temp)

def get_wavemeter_freq():
    wavemeterstring = wavemeter.getWaveMeasure(1) #returns string from wavemeter (input of 1 specifies GHz)
    freq = wavemeterstring.split()[0]
    if freq != 'inf':
        freq = float(freq)
    else:
        freq = -99
    units = wavemeterstring.split()[1]
    return freq
        
def rb_mot_stark_shift_detection(X,S):
    # print '--------------------- IN RB MOT STARK SHIFT DETECTION --------------------------'
    
    # Take one image to flush the chip before field is turned on
    t0 = X.labels.next()
    X.set_time_marker(t0)
    X.trigger_pixelink()                                    # trigger camera to flush chip
    X.wait_ms(S.Pixelink.expTime_ms)
    X.goto_ms(S.Pixelink.wait_ms,t0)
    
    # Turn on electric field
    X.set_comp_coils_V(0,0,0)
    # Added beacuse MOT number drops when changing to 3A if held there for too long
    # However, 3A gives a much denser MOT to image, and a better signal
    # X.set_mot_coil_I(3)
    #X.hv_voltage_control_off()
    if not S.bool_field_disabled:
        X.set_hv_relay_polarity(S.hv_field_polarity)                 # Turns on field
        X.wait_ms(100)
        # ##X.util_trig_high()
        X.set_high_voltage_kV(S.Rb_MOT_stark_shift_detection_voltage_kV)      #
        # Rb_pump_dF_change(X,S)
        Rb_pump_repump_dF_change(X,S)
    ##X.util_trig_high()
    
    if S.bool_field_disabled:
        X.wait_ms(100)
        X.set_mot_coil_I(3)
        X.wait_ms(50)
    
    #NOTE: This wait now takes place within the Rb_pump_dF_change
    #X.wait_ms(S.MOT_stark_shift_turn_on_wait_ms)
    
    # Added beacuse MOT number drops when changing to 3A if held there for too long
    # However, 3A gives a much denser MOT to image, and a better signal
    else:
        X.wait_ms(S.MOT_stark_shift_wait_ms-50)
        X.set_mot_coil_I(3)
        X.wait_ms(50)
    
    # Not used anymore because we are controlling power supplies through fiber optics
    # if S.MOT_stark_shift_negative_plate_turn_on_wait_ms > S.MOT_stark_shift_positive_plate_turn_on_wait_ms:
        # X.hv_voltage_control_on()
        # X.wait_ms(S.MOT_stark_shift_negative_plate_turn_on_wait_ms-S.MOT_stark_shift_positive_plate_turn_on_wait_ms)
        # X.set_positive_plate_voltage_kV(S.positve_hv_plate_voltage_kV)
        # X.wait_ms(S.MOT_stark_shift_positive_plate_turn_on_wait_ms)
    
    # else:   
        # X.set_positive_plate_voltage_kV(S.positve_hv_plate_voltage_kV)
        # X.wait_ms(S.MOT_stark_shift_positive_plate_turn_on_wait_ms-S.MOT_stark_shift_negative_plate_turn_on_wait_ms)
        # X.hv_voltage_control_on()
        # X.wait_ms(S.MOT_stark_shift_negative_plate_turn_on_wait_ms)
        
    # #X.util_trig_low()
   
    # Take One Image to Prove MOT still exists
    t0 = X.labels.next()
    X.set_time_marker(t0)
    X.trigger_pixelink()                                    # trigger camera to flush chip
    X.wait_ms(S.Pixelink.expTime_ms)
    X.goto_ms(S.Pixelink.wait_ms,t0)
    
    for nn in range(len(S.Rb.pump_MOT_stark_shift_dF)):
    
        # Now need to take images
        # TAKE IMAGE AT A STANDARD DETUNING
        if S.bool_take_ref_images:
            t0 = X.labels.next()
            X.set_time_marker(t0)
            X.trigger_pixelink('image_%i')                       # trigger camera for image with atoms
            X.set_Rb85_pump_dF(S.Rb.pump_load_dF)                # set pump AO to resonance
            X.Rb_pump.set_amplitude(S.Rb.pump_load_ampl)
            X.wait_ms(S.Pixelink.expTime_ms)
            X.goto_ms(S.Pixelink.wait_ms,t0)
        
        #X.util_trig_low()
        # TAKE IMAGE AT A DIFFERENT DETUNING
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('dark_%i')                       # trigger camera for image with atoms
        X.set_Rb85_pump_dF(S.Rb.pump_MOT_stark_shift_dF[nn])                # set pump AO to resonance
        X.Rb_pump.set_amplitude(S.Rb.pump_MOT_stark_shift_ampl)
        X.wait_ms(S.Pixelink.expTime_ms)
        X.goto_ms(S.Pixelink.wait_ms,t0)
    
    
    # Take background image with no atoms
    X.set_Rb85_pump_dF(S.Rb.pump_load_dF)                # set pump AO to resonance
    X.Rb_pump.set_amplitude(S.Rb.pump_load_ampl)
    # X.Rb_pump.set_amplitude(1)
    X.Rb_repump.set_amplitude(0)
    t0 = X.labels.next()
    X.set_time_marker(t0)
    X.trigger_pixelink()                                    # trigger camera to flush chip
    X.wait_ms(S.Pixelink.expTime_ms)
    X.goto_ms(S.Pixelink.wait_ms,t0)
    
def load_rb_magnetic_trap(X,S):
    # Set loading parameters (soon to be the same as MOT cooling)
    X.set_Rb85_pump_dF(S.Rb.pump_rb_magnetic_trapping_dF)
    X.set_Rb85_repump_dF(S.Rb.repump_rb_magnetic_trapping_dF)
    X.Rb_pump.set_amplitude(S.Rb.pump_rb_magnetic_trapping_ampl)        
    X.Rb_repump.set_amplitude(S.Rb.repump_rb_magnetic_trapping_ampl)
    X.set_mot_coil_I(S.compress_magnetic_trap_coil_gradient_A)
    X.wait_ms(1)
    # coils for compress stage
    # wait for compress stage
    

    # Turn off pump or repump light (or neither), depending on hyperfine pumping
    # Turning off all light before ramping coils up gave marginally better trapping
    if S.bool_pump_rb_magnetic_trap_F2:
        # print 'pumping magnetic trap to F2'
        X.Rb_repump_off()
        # commented out until nobounce controler in place X.Rb_repump_AOM_shutter_closed()
        X.Rb_repump_mot_shutter_closed()
        X.wait_ms(S.Rb_magnetic_trap_pump_ms)
        X.Rb_pumpAOM_off() 
        #X.mot_shutter_off()
    elif S.bool_pump_rb_magnetic_trap_F3:
        # print 'pumping magnetic trap to F3'
        X.Rb_pumpAOM_off() 
        #X.mot_shutter_off()
        X.wait_ms(S.Rb_magnetic_trap_pump_ms)
        X.Rb_repump_off()
        # commented out until nobounce controler in place X.Rb_repump_AOM_shutter_closed()
        X.Rb_repump_mot_shutter_closed()
    else:
        # print 'NOT pumping magnetic trap'
        X.Rb_repump_off()
        X.Rb_pumpAOM_off() 
        #X.mot_shutter_off()
        # commented out until nobounce controler in place X.Rb_repump_AOM_shutter_closed()
        X.Rb_repump_mot_shutter_closed()
        
    # Ramp up coils to begin trapping
    # X.set_comp_coils_V(S.Rb.compx_magnetic_trap_load,S.Rb.compy_magnetic_trap_load,S.Rb.compz_magnetic_trap_load)
    X.set_mot_coil_I(S.initial_magnetic_trap_coil_gradient_A+5)
    X.set_supply_max_current(S.initial_magnetic_trap_coil_gradient_A)
    
def Rb_magnetic_trap_ss_ramp(X,S):
    X.wait_ms(S.Rb_magnetic_trap_ss_ramp_wait_ms)
    X.set_mot_coil_I(S.Rb_magnetic_trap_ss_ramp_gradient_A)
    X.wait_ms(S.Rb_magnetic_trap_ss_time_ms)
    X.set_mot_coil_I(S.hold_magnetic_trap_coil_gradient_A)
    
def set_Rb_cool(X,S):                              # sets values for cooling atoms into dipole trap
    # print '########################### in set cool ###########################'
    X.Rb_pump.set_amplitude(S.Rb.pump_cool_ampl)
    X.Rb_repump.set_amplitude(S.Rb.repump_cool_ampl)
    X.set_Rb85_pump_dF(S.Rb.pump_cool_dF)
    X.set_Rb85_repump_dF(S.Rb.repump_cool_dF)
    X.set_mot_coil_I(S.Rb.coil_cool_I)
    
    # if (S.bool_SPI or S.bool_SPIPG) and not S.bool_tweezer_load_Rb_on_Li:
    if (S.bool_SPI or S.bool_SPIPG or S.bool_tweezer_load_Rb_on_Li):
        # print '********** SETTING COOL SPI **********'
        X.set_comp_coils_V(S.Rb.compx_cool_SPI,S.Rb.compy_cool_SPI,S.Rb.compz_cool_SPI)
    else:
        # print '***** LOADING IPG *****'
        # X.set_comp_coils_V(S.Rb.compx_cool_IPG,S.Rb.compy_cool_IPG,S.Rb.compz_cool_IPG)
        X.set_comp_coils_V(S.Rb.compx_cool_SPI,S.Rb.compy_cool_SPI,S.Rb.compz_cool_SPI)
    
def set_Li_compress(X,S):    # the magnetic gradient is set before this command is issued in the tweezer load routine                        
    X.set_comp_coils_V(S.Li6.compx_compress_SPI,S.Li6.compy_compress_SPI,S.Li6.compz_compress_SPI)
    X.set_Li_pump_amplitude(S.Li6.pump_compress_amplitude)
    X.set_Li_pump_dF(S.Li6.pump_compress_dF)
    X.set_Li_repump_amplitude(S.Li6.repump_compress_amplitude)
    X.set_Li_pump_dF(S.Li6.repump_compress_dF)                                               # sets values for loading atoms
    
def set_Li_cool(X,S):   
    X.set_comp_coils_V(S.Li6.compx_cool_SPI,S.Li6.compy_cool_SPI,S.Li6.compz_cool_SPI)   
    X.set_Li_repump_amplitude(S.Li6.repump_cool_amplitude)
    X.set_Li_pump_amplitude(S.Li6.pump_cool_amplitude)
    X.set_Li_pump_dF(S.Li6.pump_cool_dF)
    X.set_Li_repump_dF(S.Li6.repump_cool_dF)
    
def set_Li_cool_ramp(X,S):                              # sets values for cooling atoms into dipole trap   X.set_Li_pump_amplitude(S.Li6.pump_load_amplitude)
  
    if S.bool_SPI:# or S.bool_SPIPG:
        X.set_comp_coils_V(S.Li6.compx_cool,S.Li6.compy_cool,S.Li6.compz_cool)
    elif S.bool_IPG or (S.bool_IPG and S.bool_SPI):
        X.set_comp_coils_V(S.Li6.compx_cool_IPG,S.Li6.compy_cool_IPG,S.Li6.compz_cool_IPG)
    else:
        X.set_comp_coils_V(S.Li6.compx_cool,S.Li6.compy_cool,S.Li6.compz_cool)
    X.set_mot_coil_I(S.Li6.coil_cool_I)
    
    S.Ncool = N = 100.0
    dt = .001*S.Li6.cooling_ramp_ms/N
    # print 'dt = ',dt
    dpumpamp = (S.Li6.pump_cool_amplitude - S.Li6.pump_load_amplitude)/N
    drepumpamp = (S.Li6.repump_cool_amplitude - S.Li6.repump_load_amplitude)/N
    dpumpdF = (S.Li6.pump_cool_dF - S.Li6.pump_load_dF)/N
    drepumpdF = (S.Li6.repump_cool_dF - S.Li6.repump_load_dF)/N
    t0_cool = X.labels.next()
    X.set_time_marker(t0_cool)
    for j in range(N):
        t = (j+1)*dt
        # print 't = ',t
        X.set_Li_pump_amplitude(S.Li6.pump_load_amplitude + (j+1)*dpumpamp)
        X.set_Li_repump_amplitude(S.Li6.repump_load_amplitude + (j+1)*drepumpamp)
        X.set_Li_pump_dF(S.Li6.pump_load_dF + (j+1)*dpumpdF)
        X.set_Li_repump_dF(S.Li6.repump_load_dF + (j+1)*drepumpdF) 
        # print X.get_time(reference=t0_cool)
        # print 't0_cool (%s) = %f'%(t0_cool,X.get_time(reference=t0_cool))
        if t > X.get_time(reference=t0_cool):
            X.goto_s(t,t0_cool)
    # print 'ramp took %.6f ms'%(X.get_time(reference=t0_cool)*1000)
        
        
def load_tweezer(X,S,enabled=True):##load,cool, and depump atoms before turning off mot
    # ##X.util_trig_high()
    # if S.bool_absorption_imaging and S.bool_Rb_absorption_image:
        # print '################# clear pixelink at',X.get_time()
        # X.trigger_pixelink()                         # trigger camera for clear image
    # This picture is taken to flush the camera chip.
    # X.wait_ms(S.Pixelink.wait_ms)
    # X.trigger_pixelink()                         
    # X.wait_ms(S.Pixelink.expTime_ms)
    # X.wait_ms(S.Pixelink.wait_ms)
       
    #***#
    #set_magnetic_field_A(X,S,10)
    X.set_comp_coils_V(S.Rb.compx_PL_fl,S.Rb.compy_PL_fl,S.Rb.compz_PL_fl)
        
    if S.bool_IPG:
        X.IPG_shutter_open()
        X.wait_ms(20.6)
        #X.set_IPG_modulation(0,0)  # ensure the DDS is not sending an oscillation to IPG AO
        X.set_IPG_AOM_driver_input_amplitude(S.IPG_power_set)
        if S.bool_IPG_cross:
            # #X.util_trig_high()
            X.wait_ms(50)
            X.set_IPG_cross_F(100)
            X.set_IPG_cross_amplitude(S.IPG_cross_AOM_amplitude)
            X.util_trig_low()
        # ##X.util_trig_high()
    # if S.bool_align_second_arm_cross_IPG:
        # X.set_IPG_cross_amplitude(0)
    if S.bool_SPI:
        X.spi_control(S.SPI_power_set,enabled)
    if S.bool_SPIPG:
        X.IPG_shutter_open()
        #X.set_IPG_modulation(0,0)  # ensure the DDS is not sending an oscillation to IPG AO
        if not S.bool_IPG_turnon_ramp and not S.bool_SPIPG_transfer:
            X.set_IPG_AOM_driver_input_amplitude(S.IPG_power_set)
        X.spi_control(S.SPI_power_set,enabled)
    X.wait_ms(S.SPI_settle_ms) # this is the time between turning on laser on moving MOT to beam, ensures everything is stable. may want to increase to conteract the effect of the lensing. 
    # #X.util_trig_low()
    ##cool
    #***# if S.bool_Rb:
        # ##X.util_trig_high()
        #***# set_Rb_cool(X,S)  
    
    if S.bool_IPG_load_ramp:
        X.wait_ms(S.wait_IPG_load_ramp_ms)
        time_step_us = 10                                                    # time step between power changes in us
        power_ramping_difference = S.IPG_power_set - S.power_IPG_load_ramp
        power_step = power_ramping_difference * time_step_us / (S.duration_IPG_load_ramp_s *1e6)
        IPG_power_actual = S.IPG_power_set
        X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual)
        freq_ramping_difference = S.Rb.pump_cool_dF - S.freq_IPG_load_ramp
        freq_step = freq_ramping_difference * time_step_us / (S.duration_IPG_load_ramp_s *1e6)
        pump_dF_actual = S.Rb.pump_cool_dF
        X.set_Rb85_pump_dF(pump_dF_actual)
        repump_ampl_ramping_difference = S.Rb.repump_cool_ampl - S.repump_ampl_IPG_load_ramp
        repump_ampl_step = repump_ampl_ramping_difference * time_step_us / (S.duration_IPG_load_ramp_s *1e6)
        repump_ampl_actual = S.Rb.repump_cool_ampl
        X.Rb_repump.set_amplitude(repump_ampl_actual)
        eo_pump_ramping_difference = S.Rb.eo_pump_cool_v - S.eo_pump_IPG_load_ramp
        eo_pump_step = eo_pump_ramping_difference * time_step_us / (S.duration_IPG_load_ramp_s *1e6)
        eo_pump_actual = S.Rb.eo_pump_cool_v
        for tt in range(int(S.duration_IPG_load_ramp_s*1e6/time_step_us)):
            X.wait_us(time_step_us)
            IPG_power_actual = IPG_power_actual - power_step
            pump_dF_actual = pump_dF_actual - freq_step
            repump_ampl_actual = repump_ampl_actual - repump_ampl_step
            eo_pump_actual = eo_pump_actual - eo_pump_step
            if S.bool_load_power_ramp:
                X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual)
            if S.bool_load_freq_ramp:
                X.set_Rb85_pump_dF(pump_dF_actual)
                X.Rb_repump.set_amplitude(repump_ampl_actual)
    # ##X.util_trig_high()
    if S.bool_pump_to_upper:
        X.wait_ms(S.tweezer_load_ms-S.mot_shutter_delay_ms)
    else:
        # print '######################## WAITING ########################'
        X.wait_ms(S.tweezer_load_ms-S.mot_shutter_delay_ms+S.depump_ms)    #trap is loading during this time
        #X.mot_shutter_off() 
        X.wait_ms(S.mot_shutter_delay_ms-S.depump_ms)      # mot shutter open for 4.4ms, closed after 4.7ms
    ##Depump to lower/upper state to reduce hold losses and  turn off mot #########
    if S.bool_pump_to_upper: #pump to upper : part 1
        #X.mot_shutter_off() 
        X.wait_ms(S.mot_shutter_delay_ms)  # mot shutter open for 4.4ms, shutter completely closed after 4.7ms
        X.Rb_pumpAOM_off()## turns off pump AO
        X.Rb_repump.set_amplitude(1)
        X.set_Rb85_repump_dF(S.pump_to_upper_dF)
    else:  #pump to lower : part 1
        # ##X.util_trig_high()
        X.Rb_repump_off()
        if not S.bool_tweezer_molasses_cooling:
            # print '!!!!!!!!!!!!!!!!!!! closing repump shutter!!!!!!!!!!!!!!!'
            # if S.bool_depump_along_xy:
                # commented out until nobounce controler in place X.Rb_repump_AOM_shutter_closed()
            # else:
            # ##X.util_trig_high()
            X.Rb_repump_mot_shutter_closed()  # closes main repump shutter
    X.wait_ms(S.depump_ms)
    ##turn off mot/repump light 
    ##(EO not important here but want to turn on fast later
    if S.bool_pump_to_upper:#pump to upper : part 2
        X.set_Rb85_repump_dF(60)
        X.Rb_repump_off()
        if not S.bool_tweezer_molasses_cooling:
            # if S.bool_depump_along_xy:
                # commented out until nobounce controler in place X.Rb_repump_AOM_shutter_closed()
            # else:
            X.Rb_repump_mot_shutter_closed()  # closes main repump shutter
    else:     #pump to lower : part 2
        X.Rb_pumpAOM_off() ## turns off pump AO
    if S.bool_coil_turnoff and not S.bool_Li:#not S.bool_Li:
        X.set_mot_coil_I(S.mot_coil_gradient_off_A)
        X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)
        X.wait_ms(1)
        X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)
    if S.bool_forced_depump_Rb:
        X.Rb_repump_AOM_shutter_closed()
    # #X.util_trig_low()
    
    #***#
    X.wait_ms(0)
    print "===========leaving load tweezer============\n"

def finish_Rb_tweezer_load(X,S):
    # if S.bool_pump_to_upper:
        # X.wait_ms(S.tweezer_load_ms-S.mot_shutter_delay_ms)
    # else:
        # print '######################## WAITING ########################'
        # X.wait_ms(S.tweezer_load_ms-S.mot_shutter_delay_ms+S.depump_ms)    #trap is loading during this time
        # X.mot_shutter_off()
        # X.wait_ms(S.mot_shutter_delay_ms-S.depump_ms)      # mot shutter open for 4.4ms, closed after 4.7ms
    # Depump to lower/upper state to reduce hold losses and  turn off mot #########
    # if S.bool_pump_to_upper: #pump to upper : part 1
        # X.mot_shutter_off() 
        # X.wait_ms(S.mot_shutter_delay_ms)  # mot shutter open for 4.4ms, shutter completely closed after 4.7ms
        # X.Rb_pumpAOM_off()## turns off pump AO (disinjects pump laser)
        # X.Rb_repump.set_amplitude(1)
        # X.set_Rb85_repump_dF(S.pump_to_upper_dF)
    # else:  #pump to lower : part 1
        # X.Rb_repump_off()
        # if not S.bool_tweezer_molasses_cooling:
            # X.Rb_repump_mot_shutter_closed()  # closes main repump shutter
    # X.wait_ms(S.depump_ms)
    # turn off mot/repump light 
    # (EO not important here but want to turn on fast later
    # if S.bool_pump_to_upper:#pump to upper : part 2
        # X.set_Rb85_repump_dF(60)
        # X.Rb_repump_off()
        # if not S.bool_tweezer_molasses_cooling:
            # print '!!!!!!!!!!!!!!!!!!! closing repump shutter!!!!!!!!!!!!!!!'
            # # if S.bool_depump_along_xy:
                # # commented out until nobounce controler in place X.Rb_repump_AOM_shutter_closed()
            # # else:
            # X.Rb_repump_mot_shutter_closed()  # closes main repump shutter
    # else:     #pump to lower : part 2
        # X.Rb_pumpAOM_off() ## turns off pump AO 
    # if S.bool_coil_turnoff and not S.bool_Li:#not S.bool_Li:
        # X.set_mot_coil_I(S.mot_coil_gradient_off_A)
        # X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)
        # X.wait_ms(1)
        # X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)
    if S.bool_pump_to_upper:
        X.wait_ms(S.tweezer_load_ms-S.mot_shutter_delay_ms)
    else:
        # print '######################## WAITING ########################'
        X.wait_ms(S.tweezer_load_ms-S.mot_shutter_delay_ms+S.depump_ms)    #trap is loading during this time
        #X.mot_shutter_off() 
        X.wait_ms(S.mot_shutter_delay_ms-S.depump_ms)      # mot shutter open for 4.4ms, closed after 4.7ms
    ##Depump to lower/upper state to reduce hold losses and  turn off mot #########
    if S.bool_pump_to_upper: #pump to upper : part 1
        #X.mot_shutter_off() 
        X.wait_ms(S.mot_shutter_delay_ms)  # mot shutter open for 4.4ms, shutter completely closed after 4.7ms
        X.Rb_pumpAOM_off()## turns off pump AO
        X.Rb_repump.set_amplitude(1)
        X.set_Rb85_repump_dF(S.pump_to_upper_dF)
    else:  #pump to lower : part 1
        # ##X.util_trig_high()
        X.Rb_repump_off()
        if not S.bool_tweezer_molasses_cooling:
            # print '!!!!!!!!!!!!!!!!!!! closing repump shutter!!!!!!!!!!!!!!!'
            # if S.bool_depump_along_xy:
                # commented out until nobounce controler in place X.Rb_repump_AOM_shutter_closed()
            # else:
            # ##X.util_trig_high()
            X.Rb_repump_mot_shutter_closed()  # closes main repump shutter
    X.wait_ms(S.depump_ms)
    ##turn off mot/repump light 
    ##(EO not important here but want to turn on fast later
    if S.bool_pump_to_upper:#pump to upper : part 2
        X.set_Rb85_repump_dF(60)
        X.Rb_repump_off()
        if not S.bool_tweezer_molasses_cooling:
            # if S.bool_depump_along_xy:
                # commented out until nobounce controler in place X.Rb_repump_AOM_shutter_closed()
            # else:
            X.Rb_repump_mot_shutter_closed()  # closes main repump shutter
    else:     #pump to lower : part 2
        X.Rb_pumpAOM_off() ## turns off pump AO
    if S.bool_coil_turnoff and not S.bool_Li:#not S.bool_Li:
        X.set_mot_coil_I(S.mot_coil_gradient_off_A)
        X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)
        X.wait_ms(1)
        X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)
    if S.bool_forced_depump_Rb:
        X.Rb_repump_AOM_shutter_closed()
    # #X.util_trig_low()
def depump_atoms(X,S):
        # used to depump atoms to lower ground state after transfer to IPG from SPI
        X.Rb_pumpAOM_on()
        X.wait_ms(S.depump_ms)
        X.Rb_pumpAOM_off() 
        # X.mot_shutter_off()
        
def IPG_turnon_ramp(X,S):
    X.wait_ms(S.wait_IPG_turnon_ramp_ms)
    IPG_turnon_ramp_difference = S.IPG_power_set_W
    time_step_us = 10                                                    # time step between power changes in us
    power_step = IPG_turnon_ramp_difference * time_step_us / (S.duration_IPG_turnon_ramp_ms *1e3)
    IPG_power_actual = 0
    X.set_IPG_power_DDS_control_W(IPG_power_actual)
    for tt in range(int(S.duration_IPG_turnon_ramp_ms*1e3/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual = IPG_power_actual + power_step
        X.set_IPG_power_DDS_control_W(IPG_power_actual)
  

    
def load_tweezer_Li(X,S,bool_pump_lower=True,enabled=True):
    '''
    Compresses and cools the MOT, then loads these atoms into the SPI.

    It will turn up the SPI and open the IPG shutter so be careful.

    Order of operations:
        1) Turn off Zeeman slower light and coils
        2) Set magnetic field to compress settings
        3) Open IPG shutter and turn up the IPG's power (OPTIONAL)
        4) Turn up the SPI's power (OPTIONAL)
        5) Compress the MOT
        6) Start closing the MOT shutter
        7) Cool the MOT
        8) Hyperfine pumping
        9) Turn off Helmholtz field
        10) Disable Helmholtz coils (OPTIONAL)

    INPUTS:
        1) X: An instance of the MOLExperimentRecipe
        2) S: An instance of the Settings_Module
        3) bool_pump_lower: A boolean to determine if you want to pump to the lower hyperfine state (F=1/2)
        4) enabled: A boolean to enable the SPI to have its power set
    '''

    ## MAG TRAP LOADING
    # X.atom_shutter_close()
    # X.Zeeman_Slower_shutter_close()  
    # X.wait_ms(S.Zeeman_Slower_shutter_close_delay_ms)
    # X.set_Li_zeeman_slower_amplitude(0)
    # X.set_comp_coils_V(0,0,0)
    # # X.wait_ms(1000) # This is here just to give us time to close the atom shutter. Remove once this shutter is "online"
        
    # set_magnetic_field_A(X,S,S.Li6.MagneticTrapCurrent_Li_A)  # includes 1 ms wait
    # X.wait_ms(20)

    # # Turn off light to optically pump to F=1/2 state
    # if S.Li6.bool_PumpLower:
    #     X.Li_MOT_shutter_close()
    #     X.wait_ms(S.Li_MOT_shutter_close_delay_ms-S.Li6.hyperfine_Pump_time_ms)
    #     # X.util_trig_high()
    #     X.set_Li_repump_amplitude(0)
    #     X.wait_ms(S.Li6.hyperfine_Pump_time_ms)
    #     X.set_Li_pump_amplitude(0)
    #     # X.util_trig_low()
     
    # if S.Li6.bool_PumpUpper:
    #     X.Li_MOT_shutter_close()
    #     X.wait_ms(S.Li_MOT_shutter_close_delay_ms-S.Li6.hyperfine_Pump_time_ms)
    #     # X.util_trig_high()
    #     X.set_Li_pump_amplitude(0)
    #     X.wait_ms(S.Li6.hyperfine_Pump_time_ms)
    #     X.set_Li_repump_amplitude(0)
    #     # X.util_trig_low()
    
    # # Turn off Zeeman Coils to finish loading
    # X.set_zeeman_coil_I([1,2,3,4,5,6,7,8],[0,0,0,0,0,0,0,0])
   ####################################################

    #================================
    #--------1) ZEEMAN SLOWER--------
    #================================
    X.Zeeman_Slower_shutter_close()
    X.atom_shutter_close()

    X.set_zeeman_coil_I([1,2,3,4,5,6,7,8],[0,0,0,0,0,0,0,0])
    X.set_Li_zeeman_slower_amplitude(0)
    

    #================================
    #--------2) MAGNETIC FIELD-------
    #================================
    # Changes gradient coil to the ODT loading setting, and waits a short time for the field to stabilize
    set_magnetic_field_A(X,S,S.Li6.coil_compress_I)
    X.wait_ms(S.Li6.ODT_Bfield_stabilization_time_ms)
    
    #================================
    #----3,4) DIPOLE TRAP LASERS-----
    #================================
    if S.bool_IPG:
        X.IPG_shutter_open()
        X.wait_ms(19) # <-- What is this wait time for? Can we add it to the settings dictionary? -Gene
        X.set_IPG_power_DDS_control_W(S.IPG_power_set_W)
        X.set_IPG_AOM_driver_input_amplitude(S.IPG_power_set)
    if S.bool_SPI :#and not S.bool_Rb: <-- can we delete this comment if the associated code is no longer needed?
        X.set_SPI_AOM_amplitude(S.SPI_AOM_amplitude)
        X.set_SPI_AOM_frequency(S.SPI_AOM_F)
        X.spi_control(S.SPI_power_set,enabled) 
    if (S.bool_SPIPG or S.bool_SPIPG_transfer):
        # If loading both SPI and IPG at the start.
        # If not, the IPG is ramped on after the SPI trap is loaded, but we open the shutter now
        X.IPG_shutter_open()
        if S.bool_load_SPI_and_IPG:
            X.set_IPG_power_DDS_control_W(S.IPG_power_set_W)

    
    # If Loading SPI, Wait some time for beams to settle. This is the time between turning on laser on moving MOT to beam
    if S.bool_SPI:
        X.wait_ms(S.SPI_settle_ms) # Set to 0 ms
        
    # Sets time marker for loading timing
    t0 = X.labels.next()
    X.set_time_marker(t0)
    total_time = S.Li_MOT_shutter_close_delay_ms + S.Li6.tweezer_load_Li_ms

    #================================
    #---------5) COMPRESS MOT--------
    #================================
    # Compress the MOT with the right timings via goto command.
    X.goto_ms(total_time - S.Li_MOT_shutter_close_delay_ms - S.Li6.tweezer_load_Li_ms, t0)
    set_Li_compress(X, S)
    #X.wait_s(5)


    #================================
    #---------6) MOT SHUTTER---------
    #================================
    # Starting the process of closing the Li MOT shutter
    X.goto_ms(total_time - S.Li_MOT_shutter_close_delay_ms, t0)
    # NOTE: Shutter closing happens within the Cooling and HF Pumping stages
    X.Li_MOT_shutter_close()


    #================================
    #----------7) COOL MOT-----------
    #================================
    # Cool the MOT with the right timings via goto command.
    X.goto_ms(total_time - S.Li_hyperfine_pump_us/1000.0 - S.Li6.mot_cool_ms, t0)
    set_Li_cool(X,S) 
    #X.wait_s(2)
    #================================
    #------8) HYPERFINE PUMPING------
    #================================
    # After atoms loaded, pump atoms to one of the ground hyperfine states, by turning off either
    # Pump or Repump light slightly before the other. Labels for light:
    # F=3/2 -> Pump
    # F=1/2 -> Repump
    # Pump to the F=1/2 State (want to turn off repump, so pump drives atoms out of 3/2,which could decay to 1/2 state)
    
    X.goto_ms(total_time-S.Li_hyperfine_pump_us/1000.0,t0)
    X.set_Li_repump_amplitude(0)
    X.set_Li_repump_dF(-100) 
    X.goto_ms(total_time,t0)
    X.set_Li_pump_amplitude(0)
    X.set_Li_pump_dF(-100) 

    # This was replaced by the hyperfine pumping above. They should do the exact same thing except the one above won't let you pump to the upper state.
    # X.goto_ms(total_time - S.Li_hyperfine_pump_us/1000.0,t0)
    # if bool_pump_lower==True:
    #     X.set_Li_repump_amplitude(0)
    #     X.set_Li_repump_dF(-100) 
    # else:
    #     X.set_Li_pump_amplitude(0)
    #     X.set_Li_pump_dF(-100) 
    # X.goto_ms(total_time,t0)
    # if bool_pump_lower==True:
    #     X.set_Li_pump_amplitude(0)
    #     X.set_Li_pump_dF(-100) 
    # else:
    #     X.set_Li_repump_amplitude(0)
    #     X.set_Li_repump_dF(-100) 
    # X.util_trig_low
    #================================
    #-------9,10) DISABLE FIELD------
    #================================
    set_magnetic_field_A(X,S,0)

    # The magnetic field doesn't need to be disabled for a dipole trap so it should still function with this commented out
    if S.bool_coil_turnoff:
       feshbach_field_disable(X,S)
        

def load_magnetic_trap_Li(X,S):
   
    # Take picture to flush Pixelink Camera
    #if (S.bool_absorption_imaging or S.Li6.bool_pixelink_flourescence_imaging):
    #    X.wait_ms(S.Pixelink.wait_ms)
    #    X.trigger_pixelink()                     
    #    X.wait_ms(S.Pixelink.expTime_ms)
    #    X.wait_ms(S.Pixelink.wait_ms)
    
    X.atom_shutter_close()
    X.Zeeman_Slower_shutter_close()  
    X.wait_ms(S.Zeeman_Slower_shutter_close_delay_ms)
    X.set_Li_zeeman_slower_amplitude(0)
    X.set_comp_coils_V(0,0,0)
    # X.wait_ms(1000) # This is here just to give us time to close the atom shutter. Remove once this shutter is "online"
        
    set_magnetic_field_A(X,S,S.Li6.MagneticTrapCurrent_Li_A)  # includes 1 ms wait
    X.wait_ms(20)

    # Turn off light to optically pump to F=1/2 state
    if S.Li6.bool_PumpLower:
        X.Li_MOT_shutter_close()
        X.wait_ms(S.Li_MOT_shutter_close_delay_ms-S.Li6.hyperfine_Pump_time_ms)
        # X.util_trig_high()
        X.set_Li_repump_amplitude(0)
        X.wait_ms(S.Li6.hyperfine_Pump_time_ms)
        X.set_Li_pump_amplitude(0)
        # X.util_trig_low()
     
    if S.Li6.bool_PumpUpper:
        X.Li_MOT_shutter_close()
        X.wait_ms(S.Li_MOT_shutter_close_delay_ms-S.Li6.hyperfine_Pump_time_ms)
        # X.util_trig_high()
        X.set_Li_pump_amplitude(0)
        X.wait_ms(S.Li6.hyperfine_Pump_time_ms)
        X.set_Li_repump_amplitude(0)
        # X.util_trig_low()
    
    # Turn off Zeeman Coils to finish loading
    X.set_zeeman_coil_I([1,2,3,4,5,6,7,8],[0,0,0,0,0,0,0,0])
    #X.wait_s(1)

        
        
   
def tweezer_molasses_cooling(X,S):
    X.wait_ms(S.wait_tweezer_molasses_cooling_ms)
    X.set_mot_coil_I(0)
    X.set_comp_coils_V(S.compx_zero,S.compy_zero,S.compz_zero)
    X.Rb_pumpAOM_off()
    X.Rb_repump_off()
    X.set_Rb85_repump_dF(S.Rb.repump_tweezer_molasses_cooling_dF)                     # set repump frequency
    X.set_Rb85_pump_dF(S.Rb.pump_tweezer_molasses_cooling_dF)                         # set pump frequency
    X.Rb_pumpAOM_on()                                               #pump AO on
    #X.mot_shutter_on()
    X.wait_ms(S.mot_shutter_delay_ms)
    X.Rb_repump.set_amplitude(S.Rb.repump_tweezer_molasses_cooling_ampl)
    X.Rb_pump.set_amplitude(S.Rb.pump_tweezer_molasses_cooling_ampl)
    X.wait_ms(S.duration_tweezer_molasses_cooling_ms-S.mot_shutter_delay_ms)
    #X.mot_shutter_off()
    X.Rb_repump_mot_shutter_closed()
    x.wait_ms(S.mot_shutter_delay_ms)
    X.Rb_pumpAOM_off() ## turns off pump AO (disinjects pump laser)
    X.Rb_repump_off()

def forced_depump_Rb(X,S):
    # Leaves the depump light on during the dipole trap to keep atoms in lower ground hyperfine state
    X.Rb_repump_off()                                       # turns off repump AOM, just to make sure
    X.Rb_repump_mot_shutter_closed()                                 # closes the repump shutter
    #X.Li_slowing_beam_shutter_open()                # replaced by SRS shutter
    X.optical_depump_srs_shutter_open()         # opens depumping shutter
    X.wait_ms(S.wait_forced_depump_Rb_ms)
    X.main_optical_pump_srs_shutter_open()                     # opens main pumping shutter
    X.wait_ms(3)
    X.set_Rb85_optical_pump_dF(S.detuning_forced_depump_Rb_MHz)    # sets the depumping light to the right frequency
    X.Rb_optical_pump.set_amplitude(S.power_forced_depump_Rb)      # turns the depumping AOM to desired power
    # X.wait_ms(S.duration_forced_depump_Rb_ms)

def Rb_res_out(X,S):
    X.Rb_abs_shutter_on_nobounce7ms()
    X.set_Rb85_pump_dF(S.Rb.pump_abs_dF)                # set pump AO to resonance
    X.Rb_pumpAOM_on()                                    # turn on abs. beam
    X.wait_ms(S.hold_Rb_out_ms)
    X.Rb_pumpAOM_off()                                    # turn off abs. beam
    X.Rb_abs_shutter_off()                                # close abs. beam shutter
    
def apply_PA_light(X,S,enabled=True):
    X.wait_ms(S.wait_PA_light_on)
    X.MOL_TiSapph_srs_shutter_open()
    X.wait_ms(S.PA_light_hold_ms)
    X.MOL_TiSapph_srs_shutter_closed()
    X.wait_ms(5)   # for shutter to be closed 
    
def optically_pumping_Rb(X,S):
    # # ##X.util_trig_high()
    # X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)
    # X.wait_ms(1)
    # X.set_comp_coils_V(S.compx_pump,S.compy_pump,S.compz_pump)
    # X.Rb_repump_mot_shutter_closed()   # is it OK to close twice?                              # close the repump shutter
    # X.Rb_optical_pump.set_amplitude(0)
    # X.Rb_repump_off()
    # # X.set_Rb85_repump_dF(-100)
    # if (S.wait_pump_Rb_ms > 5):
        # X.wait_ms(S.wait_pump_Rb_ms-5)
    # if not S.power_depump_Rb == 0:
        # X.Li_slowing_beam_shutter_open()                # replaced by SRS shutter
        # X.optical_depump_srs_shutter_open()         # opens depumping shutter
    # X.wait_ms(1)
    # X.main_optical_pump_srs_shutter_open()                     # opens pump shutter
    # X.wait_ms(3)
    # X.set_Rb85_optical_pump_dF(S.detuning_depump_Rb_MHz)    # sets the depumping light to the right frequency
    # X.set_Rb85_repump_dF(S.detuning_pump_Rb_MHz)            # sets the pumping light to the right frequency
    # X.Rb_optical_pump.set_amplitude(S.power_depump_Rb)      # turns the depumping AOM to desired power
    # X.Rb_repump.set_amplitude(S.power_pump_Rb)              # sets the repump/optical pum AOM to desired power
    # if (S.duration_pump_Rb_ms >= 5):
        # X.wait_ms(S.duration_pump_Rb_ms-2)
        # X.main_optical_pump_srs_shutter_closed()
        # X.wait_ms(2)
        # # X.set_Rb85_repump_dF(-100)
        # X.Rb_repump_off()
        # X.Rb_optical_pump_off()
  # else:
        # X.wait_ms(S.duration_pump_Rb_ms)
        # # X.set_Rb85_repump_dF(-100)
        # X.main_optical_pump_srs_shutter_closed()
        # X.wait_ms(2)
        # X.Rb_repump_off()
        # X.Rb_optical_pump_off()
    # # if not S.bool_hyperfine_pump_Rb or S.power_hyperfine_pump_Rb == 0:
        # # X.Rb_repump_AOM_shutter_closed()
        # # X.Rb_optical_pump.set_amplitude(0)# or S.power_forced_depump_Rb) if SPI trapping
    # if not (S.power_depump_Rb == 0 or (S.bool_hyperfine_pump_Rb and not S.power_hyperfine_depump_Rb == 0)):
        # # X.Li_slowing_beam_shutter_closed()      # replaced by SRS shutter
        # X.optical_depump_srs_shutter_closed()
    # # X.Rb_optical_pump_off()
    # # #X.util_trig_low()

    ## Try and do a quick rewrite of optical pumping
    ################################################
    # Apply magnetic dield, and ensure AOMs are off (no light)
    X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)
    X.wait_ms(1)
    X.set_comp_coils_V(S.compx_pump,S.compy_pump,S.compz_pump)
    X.Rb_optical_pump.set_amplitude(0)
    X.Rb_repump_off()
    
    # Open shutters and turn on light. 
    
    # ##X.util_trig_high()
    
    X.wait_ms(S.wait_pump_Rb_ms-S.SRS_shutter_open_delay_ms)
    X.main_optical_pump_srs_shutter_open()
    if not S.power_depump_Rb == 0:
        X.optical_depump_srs_shutter_open()
    X.wait_ms(S.SRS_shutter_open_delay_ms)
    
    if S.bool_opt_pump_with_ipg_off:
        X.set_IPG_AOM_driver_input_amplitude(0)
    
    # #X.util_trig_low()
    X.set_Rb85_repump_dF(S.detuning_pump_Rb_MHz)
    X.Rb_repump.set_amplitude(S.power_pump_Rb) 
    X.set_Rb85_optical_pump_dF(S.detuning_depump_Rb_MHz)
    X.Rb_optical_pump.set_amplitude(S.power_depump_Rb) 
       
    if S.duration_pump_Rb_ms>=5:
        X.wait_ms(S.duration_pump_Rb_ms-S.SRS_shutter_close_delay_ms)
        X.main_optical_pump_srs_shutter_closed()
        X.wait_ms(S.SRS_shutter_close_delay_ms)
        X.Rb_repump_off()
        X.optical_depump_srs_shutter_closed()
        X.Rb_optical_pump_off()
    else:
        X.wait_ms(S.duration_pump_Rb_ms)
        X.main_optical_pump_srs_shutter_closed()
        X.optical_depump_srs_shutter_closed()
        X.Rb_repump_off()
        X.Rb_optical_pump_off()
    
    if S.bool_opt_pump_with_ipg_off:
        X.set_IPG_AOM_driver_input_amplitude(S.IPG_power_set)

    # Leave coils in pumping configuration for now
    ###############################################
    # TEMP
    
    # X.Rb_repump_off()
    # X.Rb_optical_pump_off()
    # X.main_optical_pump_srs_shutter_closed()
    # X.optical_depump_srs_shutter_closed()
    # X.Rb_repump_mot_shutter_closed()
    # X.Rb_repump_off()
    # # if S.bool_coil_turnoff:
        # # X.set_mot_coil_I(0)
        # # X.set_comp_coils_V(S.compx_zero,S.compy_zero,S.compz_zero)
                
    # if S.bool_pump_imagine_IPG_axis:
    # X.wait_ms(4)
    # X.main_optical_pump_srs_shutter_open()
    
    # # Start opening absorption shutter (has 5ms delays time)
    # X.Rb_abs_shutter_on()
    # X.wait_ms(S.abs_shutter_delay_ms - S.SPI_turnoff_ms)
    
    # #X.util_trig_low()

def spin_cleanup(X,S):
    ##X.util_trig_high()
    X.mot_coil_set_polarity_10ms('antihelmholtz')
    X.set_mot_coil_I(S.spin_clean_grad_I)
    X.wait_ms(S.spin_cleanup_duration_ms)
    X.set_mot_coil_I(0)
    X.wait_ms(100)
    #X.util_trig_low()
    
def depump_along_xy(X,S):
    X.main_optical_pump_srs_shutter_closed()
    X.Rb_repump_mot_shutter_open()
    #X.Li_slowing_beam_shutter_open()                # replaced by SRS shutter
    X.optical_depump_srs_shutter_open()         # opens depumping shutter
    X.Rb_optical_pump.set_amplitude(S.power_depump_along_xy)
   
def hyperfine_pumping_Rb(X,S):
    X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient) 
    X.wait_ms(1)
    X.set_comp_coils_V(S.compx_pump,S.compy_pump,S.compz_pump)
    # X.set_comp_coils_V(S.compx_mw_offset,S.compy_mw_offset,S.compz_mw_offset)
    X.Rb_repump_mot_shutter_closed()                                 # close the repump shutter
    X.Rb_optical_pump.set_amplitude(0)
    if not (S.power_hyperfine_depump_Rb == 0 or (S.bool_optically_pump_Rb and not S.power_depump_Rb == 0)):
    # if not S.power_hyperfine_depump_Rb == 0:
        #X.Li_slowing_beam_shutter_open()                # replaced by SRS shutter
        X.optical_depump_srs_shutter_open()         # opens depumping shutter
    # if (S.power_hyperfine_pump_Rb == 0):
        # commented out until nobounce controler in place X.Rb_repump_AOM_shutter_closed()
    X.wait_ms(S.wait_hyperfine_pump_Rb_ms)
    X.main_optical_pump_srs_shutter_open()                     # opens pump shutter
    X.wait_ms(3)
    # X.wait_ms(11-S.duration_hyperfine_pump_Rb_ms-1)
    X.set_Rb85_optical_pump_dF(S.detuning_hyperfine_depump_Rb_MHz)    # sets the depumping light to the right frequency
    X.set_Rb85_repump_dF(S.detuning_hyperfine_pump_Rb_MHz)            # sets the pumping light to the right frequency
    X.Rb_optical_pump.set_amplitude(S.power_hyperfine_depump_Rb)      # turns the depumping AOM to desired power
    X.Rb_repump.set_amplitude(S.power_hyperfine_pump_Rb)              # sets the repump/optical pum AOM to desired power
    if S.bool_mw_removal:
        if S.mw_removal_end_freq == S.mw_removal_start_freq:
            X.RbSS_single_tone(S.mw_removal_start_freq, 30, 1)
            X.wait_ms(S.mw_removal_dur_ms)
            X.RbSS_single_tone(S.mw_removal_start_freq, 0)
        else:
            X.RbSS_single_tone(S.mw_removal_start_freq, 30, 1)
            X.RbSS_ramp(S.mw_removal_start_freq, (S.mw_removal_end_freq-S.mw_removal_start_freq), (S.mw_removal_end_freq-S.mw_removal_start_freq)/S.mw_removal_dur_ms*1e3, 1)
    X.wait_ms(S.duration_hyperfine_pump_Rb_ms)
    ## end additions
    X.set_Rb85_repump_dF(-80)
    X.Rb_repump_off()
    X.main_optical_pump_srs_shutter_closed()
    X.wait_ms(3)
    if not S.power_hyperfine_depump_Rb == 0:
        # X.Li_slowing_beam_shutter_closed()      # replaced by SRS shutter
        X.optical_depump_srs_shutter_closed()
    X.Rb_optical_pump_off()

def state_cleanup_cycle(X,S):
    # print '############## IN STATE CLEANUP CYCLE ###############'
    X.set_comp_coils_V(S.compx_pump,S.compy_pump,S.compz_pump)
    X.Rb_repump_mot_shutter_closed()                                 # close the repump shutter
    # First close optical pumping shutters (even though SPI drives transitions)
    X.wait_ms(S.wait_mw_transfer)
    X.main_optical_pump_srs_shutter_closed()   # closes main pumping shutter takes the same time as it takes to open the mw-switch
    # X.Li_slowing_beam_shutter_closed()      # replaced by SRS shutter
    X.optical_depump_srs_shutter_closed()
    # Now drive mw transition from a particular state
    if S.mw_removal_end_freq == S.mw_removal_start_freq:
            X.RbSS_single_tone(S.mw_removal_start_freq, 30, 1)
            X.wait_ms(S.mw_removal_dur_ms)
            X.RbSS_single_tone(S.mw_removal_start_freq, 0)
    else:
        X.RbSS_single_tone(S.mw_removal_start_freq, 30, 1)
        X.RbSS_ramp(S.mw_removal_start_freq, (S.mw_removal_end_freq-S.mw_removal_start_freq), (S.mw_removal_end_freq-S.mw_removal_start_freq)/S.mw_removal_dur_ms*1e3, 1)
    X.Rb_optical_pump_off()  
   
   
def raman_stage(X,S):
    S.compx_raman_stage = (S.raman_stage_field_strength_G/S.compx_calibration)*math.cos(math.radians(S.raman_stage_angle_theta))*math.sin(math.radians(S.raman_stage_angle_phi)) + S.compx_zero
    S.compy_raman_stage = (S.raman_stage_field_strength_G/S.compy_calibration)*math.cos(math.radians(S.raman_stage_angle_theta))*math.cos(math.radians(S.raman_stage_angle_phi))  + S.compy_zero
    S.compz_raman_stage = (S.raman_stage_field_strength_G/S.compz_calibration)*math.sin(math.radians(S.raman_stage_angle_theta)) + S.compz_zero
    
    X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)   
    X.wait_ms(1)
    X.set_comp_coils_V(S.compx_raman_stage,S.compy_raman_stage,S.compz_raman_stage)
    X.wait_ms(S.duration_raman_stage)
    
    # Move back to offset field for duration of remaining hold time
    X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)
    X.wait_ms(1)
    X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)



def drsc_cycle_sequence(X,S):
    S.compx_raman_stage = (S.raman_stage_field_strength_G/S.compx_calibration)*math.cos(math.radians(S.raman_stage_angle_theta))*math.sin(math.radians(S.raman_stage_angle_phi)) + S.compx_zero
    S.compy_raman_stage = (S.raman_stage_field_strength_G/S.compy_calibration)*math.cos(math.radians(S.raman_stage_angle_theta))*math.cos(math.radians(S.raman_stage_angle_phi))  + S.compy_zero
    S.compz_raman_stage = (S.raman_stage_field_strength_G/S.compz_calibration)*math.sin(math.radians(S.raman_stage_angle_theta)) + S.compz_zero
    
    X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)   
    X.wait_ms(1)
    X.set_comp_coils_V(S.compx_raman_stage,S.compy_raman_stage,S.compz_raman_stage)
    X.wait_ms(S.duration_drsc_cycle_field_ms)
    
    X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)   
    X.wait_ms(1)
    X.set_comp_coils_V(S.compx_pump,S.compy_pump,S.compz_pump)
    X.Rb_repump_mot_shutter_closed()                                 # close the repump shutter
    X.Rb_optical_pump.set_amplitude(0)
    if not S.power_depump_Rb_drsc_cycle == 0:
        #X.Li_slowing_beam_shutter_open()                # replaced by SRS shutter
        X.optical_depump_srs_shutter_open()         # opens depumping shutter
    X.main_optical_pump_srs_shutter_open()                     # opens pump shutter
    X.wait_ms(3)
    if S.duration_pump_Rb_drsc_cycle_ms <=5:
        X.wait_ms(9-S.duration_pump_Rb_drsc_cycle_ms-3)
    X.set_Rb85_optical_pump_dF(S.detuning_depump_Rb_MHz)    # sets the depumping light to the right frequency
    X.set_Rb85_repump_dF(S.detuning_pump_Rb_MHz)            # sets the pumping light to the right frequency
    X.Rb_optical_pump.set_amplitude(S.power_depump_Rb_drsc_cycle)      # turns the depumping AOM to desired power
    X.Rb_repump.set_amplitude(S.power_pump_Rb_drsc_cycle)              # sets the repump/optical pum AOM to desired power
    X.wait_ms(S.duration_pump_Rb_drsc_cycle_ms)
    X.set_Rb85_repump_dF(-80)
    X.Rb_repump_off()
    X.main_optical_pump_srs_shutter_closed()
    X.Rb_optical_pump.set_amplitude(.01)
    if not S.power_depump_Rb_drsc_cycle == 0:
        # X.Li_slowing_beam_shutter_closed()      # replaced by SRS shutter
        X.optical_depump_srs_shutter_closed()
    X.Rb_optical_pump_off()


def drsc_stage(X,S):
    S.compx_drsc = (S.drsc_field_strength_G/S.compx_calibration)*math.cos(math.radians(S.drsc_angle_theta))*math.sin(math.radians(S.drsc_angle_phi)) + S.compx_zero
    S.compy_drsc = (S.drsc_field_strength_G/S.compy_calibration)*math.cos(math.radians(S.drsc_angle_theta))*math.cos(math.radians(S.drsc_angle_phi))  + S.compy_zero
    S.compz_drsc = (S.drsc_field_strength_G/S.compz_calibration)*math.sin(math.radians(S.drsc_angle_theta)) + S.compz_zero
    
    X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)   
    X.wait_ms(1)
    X.set_comp_coils_V(S.compx_drsc,S.compy_drsc,S.compz_drsc)
    X.Rb_repump_mot_shutter_closed()                                 # close the repump shutter
    X.Rb_optical_pump.set_amplitude(0)
    if not S.power_depump_Rb == 0:
        #X.Li_slowing_beam_shutter_open()                # replaced by SRS shutter
        X.optical_depump_srs_shutter_open()         # opens depumping shutter
    X.wait_ms(S.wait_drsc_Rb_ms)
    X.main_optical_pump_srs_shutter_open()                     # opens pump shutter
    X.wait_ms(3)
    if S.duration_drsc_Rb_ms <=5:
        X.wait_ms(9-S.duration_drsc_Rb_ms-3)
    X.set_Rb85_optical_pump_dF(S.drsc_detuning_depump_Rb_MHz)    # sets the depumping light to the right frequency
    X.set_Rb85_repump_dF(S.drsc_detuning_pump_Rb_MHz)            # sets the pumping light to the right frequency
    X.Rb_optical_pump.set_amplitude(S.drsc_power_depump_Rb)      # turns the depumping AOM to desired power
    X.Rb_repump.set_amplitude(S.drsc_power_pump_Rb)              # sets the repump/optical pum AOM to desired power
    X.wait_ms(S.duration_drsc_Rb_ms)
    ## end additions
    X.set_Rb85_repump_dF(-80)
    X.Rb_repump_off()
    X.main_optical_pump_srs_shutter_closed()
    X.Rb_optical_pump.set_amplitude(.01)
    if not S.power_depump_Rb == 0:# or (S.bool_hyperfine_pump_Rb and not S.power_hyperfine_depump_Rb == 0)):
        # X.Li_slowing_beam_shutter_closed()      # replaced by SRS shutter
        X.optical_depump_srs_shutter_closed()
    X.Rb_optical_pump_off()
    
    # # X.comp_coil_z.set_scaled_value(S.compz_offset)
    # # X.wait_ms(1)
    # # X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)
   
def Li_mw_transfer(X,S):
    # X.comp_coil_z.set_scaled_value(S.compz_offset)
    X.wait_ms(1)
    X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)
    X.wait_ms(S.wait_Li_mw_transfer_ms)
    if S.Li_mw_end_dF == S.Li_mw_start_dF:
        X.set_LiSS_amplitude(0)
        X.set_LiSS_dF(S.Li_mw_end_dF)
        X.set_LiSS_amplitude(S.Li_mw_amplitude)
        X.wait_s(S.Li_mw_scan_dur_s)
        X.set_LiSS_amplitude(0)
    else:
        X.set_LiSS_amplitude(0)
        X.ramp_LiSS_dF(S.Li_mw_start_dF,S.Li_mw_end_dF,S.Li_mw_scan_dur_s,S.Li_mw_amplitude)
        X.set_LiSS_amplitude(0)
    X.set_comp_coils_V(0,0,0) 
    X.wait_s(numpy.clip(S.Li_mw_tot_time_s-(S.Li_mw_scan_dur_s+S.wait_Li_mw_transfer_ms*1e-3 +1e-3),0,1000))#To make sure the duration of the scan can be changed while maintaining the total time, 1000 as the upper bound is chosen arbitrarily 

def mw_transfer(X,S):
    
    #X.wait_ms(500)
    # For scan with MOT Coils, comment out temp.
    ############################################
    X.set_comp_coils_V(S.compx_transient,S.compy_transient,S.compz_transient)
    X.wait_ms(1)
    X.set_comp_coils_V(S.compx_mw_offset,S.compy_mw_offset,S.compz_mw_offset)
    ############################################
    # X.set_supply_max_current(S.Rb_mw_transfer_MOT_coil_A)
    # X.set_mot_coil_I(20)
    # feshbach_field_enable(X,S,0)
    # X.wait_ms(1000)
    ##X.util_trig_high() 
    X.wait_ms(S.wait_mw_transfer)
    # X.main_optical_pump_srs_shutter_closed()   # closes main pumping shutter takes the same time as it takes to open the mw-switch
    # X.Li_slowing_beam_shutter_closed()      # replaced by SRS shutter
    # X.optical_depump_srs_shutter_closed()
    if S.mw_end_freq == S.mw_start_freq:
        X.RbSS_single_tone(S.mw_start_freq, 30, 1)
        X.wait_ms(S.mw_scan_dur)
        X.RbSS_single_tone(S.mw_start_freq, 0)
    else:
        X.RbSS_single_tone(S.mw_start_freq, 30, 1)      # stabilizes frequency to desired starting value - important!
        X.RbSS_ramp(S.mw_start_freq, (S.mw_end_freq-S.mw_start_freq), (S.mw_end_freq-S.mw_start_freq)/S.mw_scan_dur*1e3, 1)
    X.Rb_optical_pump_off()                                     # turns off the depumping AOM

    X.set_mot_coil_I(0)
    # feshbach_field_disable(X,S)
    
    # #X.util_trig_low()
def ipg_flash_off_on(X,S):
    # ##X.util_trig_high()
    X.set_IPG_AOM_driver_input_amplitude(0)
    X.wait_ms(S.ipg_flash_off_time_ms)
    X.set_IPG_AOM_driver_input_amplitude(S.IPG_power_set)
    # X.util_trig_low()

def modulate_ipg_off_on(X,S,freq,duration_ms):
    period = 1.0/(freq*1e3)
    # print period
    period_us = period*1e6
    period_ms = period*1e3
    # print period_us
    for nn in (range(int(duration_ms/period_ms))):
        X.set_IPG_AOM_driver_input_amplitude(0)
        X.wait_ms(period_ms/2)
        X.set_IPG_AOM_driver_input_amplitude(S.IPG_power_set)
        X.wait_ms(period_ms/2)

def modulate_ipg_off_on_Li(X,S,period_us,duration_ms,IPG_power_W):

    period_ms = period_us*1e-3
    # for nn in (range(int(duration_ms/period_ms))):
    for nn in range(50):
        X.set_IPG_power_DDS_control_W(0)
        X.wait_us(1)
        X.set_IPG_power_DDS_control_W(.5)
        X.wait_us(30)

        
def ipg_mod(X,S):
    # ##X.util_trig_high()
    X.wait_ms(S.mod_wait_ms)
    if S.bool_mod_ramp_before:
        pass
        #X.ramp_IPG(S.mod_ramp_ms/2000.0,S.IPG_power_set,S.IPG_min_power_V)
        #X.ramp_IPG(S.mod_ramp_ms/2000.0,S.IPG_min_power_V,S.IPG_power_set)
    X.set_IPG_power_DDS_control_W(S.mod_offset_W)
    #X.set_IPG_modulation(S.mod_freq_kHz/1000.0,S.IPG_mod_amplitude)
    X.wait_ms(S.mod_time_ms)
    if S.bool_mod_ramp_after:
        pass
        #X.ramp_IPG(S.mod_ramp_ms/2000.0,S.IPG_power_set,S.IPG_min_power_V)
        #X.ramp_IPG(S.mod_ramp_ms/2000.0,S.IPG_min_power_V,S.IPG_power_set)
    #X.set_IPG_modulation(0,0)
    X.set_IPG_power_DDS_control_W(S.IPG_power_set_W)
    # #X.util_trig_low()

def IPG_aom_power_mod(X,S):
    X.wait_ms(S.mod_wait_ms)
    X.set_IPG_power_DDS_control_W(S.mod_offset_W)
    X.IPG_power_mod(S.mod_time_ms,S.mod_freq_kHz,S.IPG_mod_amplitude_W,S.mod_offset_W)

def IPG_aom_square_mod(X,S):
    X.wait_ms(S.mod_wait_ms)
    X.set_IPG_power_DDS_control_W(S.mod_offset_W)
    if S.mod_freq_kHz == 0:
        X.wait_ms(S.mod_time_ms)
    else:
        period_ms = 1.0/S.mod_freq_kHz
        num = int(S.mod_time_ms/period_ms)
        for nn in range(num*2.0):
            # print nn
            X.set_IPG_power_DDS_control_W(S.mod_offset_W+S.IPG_mod_amplitude_W)
            X.wait_ms(period_ms/2.0)
            X.set_IPG_power_DDS_control_W(S.mod_offset_W-S.IPG_mod_amplitude_W)
            X.wait_ms(period_ms/2.0)
    X.set_IPG_power_DDS_control_W(S.mod_offset_W)
    X.wait_ms(S.mod_wait_ms)

def spi_mod(X,S):
    X.wait_ms(S.mod_wait_SPI_ms)
    X.spi_power_mod(S.mod_time_SPI_ms,S.mod_freq_SPI_kHz/1000.0,S.mod_amp_p,S.SPI_power_set)

def ipg_second_arm_mod(X,S):
    X.wait_ms(S.IPG_second_arm_mod_wait_ms)
    X.ipg_second_arm_mod(S.IPG_second_arm_mod_time_ms,S.IPG_second_arm_freq_kHz,S.IPG_secomd_arm_mod_amp_W,S.IPG_second_arm_offset_W)

def evaporative_cooling_SPI(X,S,evaporation_stop_power,evaporation_time_ms,power_start):
    X.wait_ms(S.wait_cooling_SPI_ms)
    S.SPI_power_actual = power_start
    cooling_difference = S.SPI_power_actual - evaporation_stop_power                # difference between initial and final SPI-power
    time_step_us = 50                                                    # time step between power changes in us
    power_step = cooling_difference * time_step_us / (evaporation_time_ms*1e3)
    for tt in range(int(evaporation_time_ms*1e3/time_step_us)):
        X.wait_us(time_step_us)
        S.SPI_power_actual = S.SPI_power_actual - power_step
        X.spi_power_set_p(S.SPI_power_actual)
        
def evaporative_cooling_IPG(X,S):
    X.wait_ms(S.wait_cooling_IPG_ms)
    if S.bool_IPG_load_ramp and S.bool_load_power_ramp:
        cooling_difference_1 = S.power_IPG_load_ramp - S.IPG_power_cooling_1
        IPG_power_actual_1 = S.power_IPG_load_ramp
        X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_1)
    else:
        cooling_difference_1 = S.IPG_power_set - S.IPG_power_cooling_1
        IPG_power_actual_1 = S.IPG_power_set
        X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_1)
    time_step_us = 1000                                                    # time step between power changes in us
    power_step_1 = cooling_difference_1 * time_step_us / (S.ramp_duration_cooling_IPG_s_1 *1e6)
    for tt in range(int(S.ramp_duration_cooling_IPG_s_1*1e6/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual_1 = IPG_power_actual_1 - power_step_1
        X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_1)
        
    cooling_difference_2 = IPG_power_actual_1 - S.IPG_power_cooling_2
    time_step_us = 200                                                    # time step between power changes in us
    power_step_2 = cooling_difference_2 * time_step_us / (S.ramp_duration_cooling_IPG_s_2 *1e6)
    IPG_power_actual_2 = IPG_power_actual_1
    X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_2)
    for tt in range(int(S.ramp_duration_cooling_IPG_s_2*1e6/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual_2 = IPG_power_actual_2 - power_step_2
        X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_2)
        
    cooling_difference_3 = IPG_power_actual_2 - S.IPG_power_cooling_3
    time_step_us = 50                                                    # time step between power changes in us
    power_step_3 = cooling_difference_3 * time_step_us / (S.ramp_duration_cooling_IPG_s_3 *1e6)
    IPG_power_actual_3 = IPG_power_actual_2
    X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_3)
    for tt in range(int(S.ramp_duration_cooling_IPG_s_3*1e6/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual_3 = IPG_power_actual_3 - power_step_3
        X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_3)
        
    cooling_difference_4 = IPG_power_actual_3 - S.IPG_power_cooling_4
    time_step_us = 50                                                    # time step between power changes in us
    power_step_4 = cooling_difference_4 * time_step_us / (S.ramp_duration_cooling_IPG_s_4 *1e6)
    IPG_power_actual_4 = IPG_power_actual_3
    X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_4)
    for tt in range(int(S.ramp_duration_cooling_IPG_s_4*1e6/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual_4 = IPG_power_actual_4 - power_step_4
        X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_4)
        
    cooling_difference_5 = IPG_power_actual_4 - S.IPG_power_cooling_5
    time_step_us = 50                                                    # time step between power changes in us
    power_step_5 = cooling_difference_5 * time_step_us / (S.ramp_duration_cooling_IPG_s_5 *1e6)
    IPG_power_actual_5 = IPG_power_actual_4
    X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_5)
    for tt in range(int(S.ramp_duration_cooling_IPG_s_5*1e6/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual_5 = IPG_power_actual_5 - power_step_5
        X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_5)
        
    cooling_difference_6 = IPG_power_actual_5 - S.IPG_power_cooling_6
    time_step_us = 50                                                    # time step between power changes in us
    power_step_6 = cooling_difference_6 * time_step_us / (S.ramp_duration_cooling_IPG_s_6 *1e6)
    IPG_power_actual_6 = IPG_power_actual_5
    X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_6)
    for tt in range(int(S.ramp_duration_cooling_IPG_s_6*1e6/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual_6 = IPG_power_actual_6 - power_step_6
        X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual_6)

def IPG_relative_power(rel_power):
    A = 0.6026
    x0 = 0.5091
    w = 0.5155
    offset = 1.066
    return A*scipy.special.erfinv((rel_power-x0)/(w))+offset

def ramp_IPG(X,S,IPG_AOM_start,IPG_AOM_end,ramp_duration_ms):
    X.wait_ms(S.wait_ramp_IPG_ms)
    ramp_IPG_difference = IPG_AOM_start - IPG_AOM_end
    time_step_us = 10                                                    # time step between power changes in us
    power_step = ramp_IPG_difference * time_step_us / (ramp_duration_ms*1e3)
    IPG_power_actual = IPG_AOM_start
    X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual)
    for tt in range(int(ramp_duration_ms*1e3/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual = IPG_power_actual - power_step
        X.set_IPG_AOM_driver_input_amplitude(IPG_power_actual)

def ramp_IPG_linear(X,S,IPG_power_start_W,IPG_power_end_W,linear_ramp_duration_ms):
    linear_ramp_IPG_difference = IPG_power_start_W - IPG_power_end_W
    time_step_us = 50
    linear_power_step = linear_ramp_IPG_difference * time_step_us / (linear_ramp_duration_ms*1e3)
    IPG_power_actual = IPG_power_start_W
    X.set_IPG_power_DDS_control_W(IPG_power_actual)
    for tt in range(int(linear_ramp_duration_ms*1e3/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual = IPG_power_actual - linear_power_step 
        X.set_IPG_power_DDS_control_W(IPG_power_actual)

def ramp_IPG_linear_B_field(X,S,IPG_power_start_W,IPG_power_end_W,linear_ramp_duration_ms,B_start,B_stop):
    linear_ramp_IPG_difference = IPG_power_start_W - IPG_power_end_W
    B_diff = B_stop-B_start
    time_step_us = 50
    linear_power_step = linear_ramp_IPG_difference * time_step_us / (linear_ramp_duration_ms*1e3)
    B_step = B_diff*time_step_us/(linear_ramp_duration_ms*1e3)
    IPG_power_actual = IPG_power_start_W
    B_actual = B_start
    X.set_IPG_power_DDS_control_W(IPG_power_actual)
    for tt in range(int(linear_ramp_duration_ms*1e3/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual = IPG_power_actual - linear_power_step 
        X.set_IPG_power_DDS_control_W(IPG_power_actual)
        # current_A = ((B_start+tt*B_step) - S.helmholtz_cal_offset)/float(S.helmholtz_cal_slope)
        B_actual = B_actual+B_step
        set_magnetic_field_G(X,S,B_actual)

def ramp_IPG_exp(X,S,IPG_power_start_W,IPG_power_end_W,exp_ramp_duration_ms):
    X.wait_ms(S.wait_exp_ramp_IPG_ms)
    time_step_us = 50
    IPG_power_actual = IPG_power_start_W
    X.set_IPG_power_DDS_control_W(IPG_power_actual)
    # print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    # print 'EXP EVAP tau'
    # print S.tau_ms
    # print 'EXP EVAP total duration for time const calc'
    # print S.total_exp_ramp_duration_ms
    # print 'EXP EVAP duration for a given end power'
    # print S.exp_ramp_duration_ms
    for tt in range(int(exp_ramp_duration_ms*1e3/time_step_us)):
        X.wait_us(time_step_us)
        time_elapsed_ms = tt*time_step_us*1e-3
        IPG_power_actual = IPG_power_start_W*math.exp(-time_elapsed_ms/S.tau_ms)
        X.set_IPG_power_DDS_control_W(IPG_power_actual)
def IPG_evaporate_into_cross(X,S,IPG_power_start_W,IPG_power_end_W,IPG_cross_power_start_W,IPG_cross_power_end_W,evap_into_cross_duration):
    time_step_us = 100
    linear_ramp_IPG_difference = IPG_power_start_W - IPG_power_end_W
    linear_ramp_IPG_cross_difference = IPG_cross_power_start_W - IPG_cross_power_end_W
    IPG_power_actual = IPG_power_start_W
    IPG_cross_power_actual = IPG_cross_power_start_W
    
    linear_power_step = linear_ramp_IPG_difference * time_step_us / (evap_into_cross_duration*1e3)
    linear_power_step_cross = linear_ramp_IPG_cross_difference * time_step_us / (evap_into_cross_duration*1e3)
    
    # print '!!!!!!Evap into IPG cross!!!!!!!!!!!!!!!!!!!'
    # print linear_ramp_IPG_difference
    # print linear_ramp_IPG_cross_difference
    # print linear_power_step
    # print linear_power_step_cross
    # print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    for tt in range(int(evap_into_cross_duration*1e3/time_step_us)):
        X.wait_us(time_step_us)
        IPG_power_actual = IPG_power_actual - linear_power_step 
        IPG_cross_power_actual = IPG_cross_power_actual - linear_power_step_cross 
        # # print tt
        # print IPG_cross_power_actual
        X.set_IPG_power_DDS_control_W(IPG_power_actual)
        X.set_IPG_cross_power_W(IPG_cross_power_actual)
        
##this is exponential evaporation        
def IPG_cross_evap(X,S,IPG_power_start_W,IPG_power_end_W,IPG_cross_power_start_W,IPG_cross_power_end_W,dual_IPG_exp_ramp_duration_ms,tau_ms):
    X.wait_ms(S.wait_exp_ramp_IPG_ms)
    time_step_us = 500
    IPG_power_actual = IPG_power_start_W
    IPG_cross_power_actual = IPG_cross_power_start_W
    X.set_IPG_power_DDS_control_W(IPG_power_actual)
    X.set_IPG_cross_power_W(IPG_cross_power_actual)
    # print '!!!!!!!!!!!!Exp evap in the IPG cross!!!!!!!!!!!!!!!!!!!!!'
    # print tau_ms
    # print S.total_cross_exp_ramp_duration_ms
    # print dual_IPG_exp_ramp_duration_ms
    for tt in range(int(dual_IPG_exp_ramp_duration_ms*1e3/time_step_us)):
        X.wait_us(time_step_us)
        time_elapsed_ms = tt*time_step_us*1e-3
        IPG_power_actual = IPG_power_start_W*math.exp(-time_elapsed_ms/tau_ms)
        IPG_cross_power_actual = IPG_cross_power_start_W*math.exp(-time_elapsed_ms/tau_ms)
        X.set_IPG_power_DDS_control_W(IPG_power_actual)
        X.set_IPG_cross_power_W(IPG_cross_power_actual)
        
def ramp_SPI_exp(X,S,SPI_power_start_W,SPI_power_end_W,SPI_exp_ramp_duration_ms):
    time_step_us =50
    SPI_power_actual = SPI_power_start_W
    X.spi_power_set_p(S.SPI_power_actual)
    # print '^^^^^^^^^^ IN SPI EXPONENTIAL EVAP RAMP ^^^^^^^^^^'
    # print SPI_power_start_W
    # print SPI_power_end_W
    # print S.tau_SPI_ms
    # # print S.SPI_exp_total_ramp_duration_ms
    # print SPI_exp_ramp_duration_ms
    for tt in range(int(SPI_exp_ramp_duration_ms*1e3/time_step_us)):
        X.wait_us(time_step_us)
        time_elapsed_ms = tt*time_step_us*1e-3
        SPI_power_actual = SPI_power_start_W*math.exp(-time_elapsed_ms/S.tau_SPI_ms)
        X.spi_power_set_p(SPI_power_actual)

def set_field_config_hemholtz(X,S):
    X.set_mot_coil_I(0)
    X.wait_ms(S.wait_feshbach_ms/2)
    X.mot_coil_set_polarity_10ms('helmholtz')
    X.wait_ms(S.wait_feshbach_ms/2)
    X.set_mot_coil_I(0)
    
def set_field_config_antihemholtz(X,S):
    X.set_mot_coil_I(0)
    X.wait_ms(S.wait_feshbach_ms/2)
    X.mot_coil_set_polarity_10ms('antihelmholtz')
    X.wait_ms(S.wait_feshbach_ms/2)
    X.set_mot_coil_I(0)
    
def set_field_config_antihemholtz(X,S):
    X.set_mot_coil_I(0)
    X.wait_ms(S.wait_feshbach_ms/2)
    X.mot_coil_set_polarity_10ms('antihelmholtz')
    X.wait_ms(S.wait_feshbach_ms/2)
    X.set_mot_coil_I(0)
    
def set_magnetic_field_G(X,S,gauss):
    current_A = (gauss - S.helmholtz_cal_offset)/float(S.helmholtz_cal_slope)
    if S.bool_PS_current_control:
        print '--------------------------------------------------------'
        print current_A
        X.set_supply_max_current(current_A)
        X.set_mot_coil_I(current_A+5)
    else:
        X.set_mot_coil_I(current_A)
        X.set_supply_max_current(30)

def set_magnetic_field_A(X,S,current_A):
    if S.bool_PS_current_control:
        X.set_supply_max_current(current_A)
        X.set_mot_coil_I(current_A+5)
    else:
        X.set_mot_coil_I(current_A)
        X.set_supply_max_current(30)
  
def feshbach_field_enable(X,S,current_A):
    X.set_mot_coil_I(0)
    X.wait_ms(S.wait_feshbach_ms/2)
    X.mot_coil_set_polarity_10ms('helmholtz')
    X.wait_ms(S.wait_feshbach_ms/2)
    X.set_mot_coil_I(current_A)

def feshbach_field_disable(X,S):
    X.set_mot_coil_I(0)
    X.set_supply_max_current(0)
    X.wait_ms(50)
    # X.wait_ms(S.wait_feshbach_ms)
    X.mot_coil_disabled()


    
def feshbach_field_enable_Gauss(X,S,Gauss):
    # applies helmholz B field calibration to get Amps to set for a given field in Gauss
    # calibration assumes Bfield(G) = Current(A)*Slope(G/A) + Offset(G)
    current_A = (Gauss - S.helmholtz_cal_offset)/float(S.helmholtz_cal_slope)
    feshbach_field_enable(X,S,current_A)

def set_feshbach_field_Gauss(X,S,Gauss):
    current_A = (Gauss - S.helmholtz_cal_offset)/float(S.helmholtz_cal_slope)
    X.set_mot_coil_I(current_A)
    
def take_image(X,S):
    ### ABSORPTION IMAGING - IPG, SPI, or BOTH###
    # ##X.util_trig_high()
    if S.bool_absorption_imaging:
        # ##X.util_trig_high()
        # ##X.util_trig_high()
        # X.Rb_repump_AOM_shutter_open()
        if S.bool_Rb and (not S.bool_Li) and S.bool_cool_mot and S.cool_Rb_mot_ms>S.Pixelink.wait_ms and not S.bool_tweezer_load:
            #in this case cool rb mot here since we just have rb mot.
            X.Rb_pump.set_amplitude(S.Rb.pump_cool_ampl)  
            X.Rb_repump.set_amplitude(S.Rb.repump_cool_mot_ampl)
            X.set_Rb85_pump_dF(S.Rb.pump_cool_mot_dF)
            X.set_Rb85_repump_dF(S.Rb.repump_cool_mot_dF)
            X.set_comp_coils_V(S.Rb.compx_cool,S.Rb.compy_cool,S.Rb.compz_cool)
            X.wait_ms(S.cool_Rb_mot_ms-S.Pixelink.wait_ms)
        ##optical pumping for mot
        if not S.bool_tweezer_load:
            t0 = X.labels.next()
            X.set_time_marker(t0)
            X.trigger_pixelink()                                    # trigger camera to flush chip
            # print 'not in tweezerload'
            if S.bool_Rb and not S.bool_Li and S.bool_cool_mot and S.cool_Rb_mot_ms<S.Pixelink.wait_ms:
                if S.cool_Rb_mot_ms>S.abs_shutter_delay_ms:
                    X.goto_ms(S.Pixelink.wait_ms - S.cool_Rb_mot_ms - S.pump_ms,t0)
                    X.Rb_pump.set_amplitude(S.Rb.pump_cool_ampl)  
                    X.Rb_repump.set_amplitude(S.Rb.repump_cool_mot_ampl)
                    X.set_Rb85_pump_dF(S.Rb.pump_cool_mot_dF)
                    X.set_Rb85_repump_dF(S.Rb.repump_cool_mot_dF)
                    X.set_comp_coils_V(S.Rb.compx_cool,S.Rb.compy_cool,S.Rb.compz_cool)  
                    X.goto_ms(S.Pixelink.wait_ms - S.abs_shutter_delay_ms - S.pump_ms,t0)
                    X.Rb_abs_shutter_on()                            # begin opening abs. beam shutter (takes 5ms)
                    X.goto_ms(S.Pixelink.wait_ms - S.mot_shutter_delay_ms - S.pump_ms,t0)
                    #X.mot_shutter_off()     # mot shutter open for 4.4ms, shutter completely closed after 4.7ms
                else:
                    X.goto_ms(S.Pixelink.wait_ms - S.abs_shutter_delay_ms - S.pump_ms,t0)
                    X.Rb_abs_shutter_on()                            # begin opening abs. beam shutter (takes 5ms)
                    X.goto_ms(S.Pixelink.wait_ms - S.mot_shutter_delay_ms - S.pump_ms,t0)
                    #X.mot_shutter_off()     # mot shutter open for 4.4ms, shutter completely closed after 4.7ms
                    X.goto_ms(S.Pixelink.wait_ms - S.cool_Rb_mot_ms - S.pump_ms,t0)
                    X.Rb_pump.set_amplitude(S.Rb.pump_cool_ampl)  
                    X.Rb_repump.set_amplitude(S.Rb.repump_cool_mot_ampl)
                    X.set_Rb85_pump_dF(S.Rb.pump_cool_mot_dF)
                    X.set_Rb85_repump_dF(S.Rb.repump_cool_mot_dF)
                    X.set_comp_coils_V(S.Rb.compx_cool,S.Rb.compy_cool,S.Rb.compz_cool)
            else:
                if (S.abs_shutter_delay_ms > S.mot_shutter_delay_ms):
                    X.goto_ms(S.Pixelink.wait_ms - S.abs_shutter_delay_ms,t0)
                    X.Rb_abs_shutter_on() # begin opening abs. beam shutter (takes 5ms)
                    X.goto_ms(S.Pixelink.wait_ms - S.mot_shutter_delay_ms,t0)
                    #X.mot_shutter_off()     # mot shutter open for 4.4ms, shutter completely closed after 4.7ms
                else:
                    X.goto_ms(S.Pixelink.wait_ms - S.mot_shutter_delay_ms,t0)
                    #X.mot_shutter_off()     # mot shutter open for 4.4ms, shutter completely closed after 4.7ms
                    X.goto_ms(S.Pixelink.wait_ms - S.abs_shutter_delay_ms,t0)
                    X.Rb_abs_shutter_on() # begin opening abs. beam shutter (takes 5ms)
            # ##X.util_trig_high() 
            X.goto_ms(S.Pixelink.wait_ms - .01 - S.pump_ms,t0)
            # ##X.util_trig_high() 
            X.set_mot_coil_I(0)
            X.goto_ms(S.Pixelink.wait_ms - S.pump_ms,t0)  # at this point, there is S.pump_ms=.1 ms to go until expansion starts
            X.set_comp_coils_V(S.compx_zero,S.compy_zero,S.compz_zero)
            if S.bool_pump_imaging:
                X.set_Rb85_repump_dF(S.Rb.repump_abs_dF)                 # repump light on resonance
                # ##X.util_trig_high()
                X.Rb_pumpAOM_off()
            else:
                X.Rb_repump_off()                            # turn off repump light
            # this goto "waits" .1 ms for pumping to occur. then turns off all light and starts exp
            X.goto_ms(S.Pixelink.wait_ms,t0)
            X.Rb_repump_off()                                # turn off repump light
            X.Rb_pumpAOM_off()                                # turn off pump AOM
            ###X.util_trig_high()
            X.wait_ms(S.expansion_ms)
            ##X.util_trig_low()
            
        # Imaging for the Dipole Traps
        else:
            # print '!!!!!!!!!!!!!!!!!! Taking RB ODT Image !!!!!!!!!!!!!!!!!!!!!!!'
            # Trigger camera to flush chip
            # if not S.bool_tweezer_load_Rb_on_Li:     # when loading Li first, flush image taken elsewhere
            # t0 = X.labels.next()
            # X.set_time_marker(t0)
            # X.trigger_pixelink()   
            # X.wait_ms(S.Pixelink.wait_ms)            
            
            # Make sure all light is off, shutters closed, magnetic field off
            X.Rb_repump_off()
            X.Rb_optical_pump_off()
            X.main_optical_pump_srs_shutter_closed()
            X.optical_depump_srs_shutter_closed()
            X.Rb_repump_mot_shutter_closed()
            X.Rb_repump_off()
            if S.bool_coil_turnoff:
                X.set_mot_coil_I(0)
                X.set_comp_coils_V(S.compx_zero,S.compy_zero,S.compz_zero)
            if S.bool_forced_depump_Rb:
                # If force depump was on, turn off light and close shutters
                # Need to open repump AOM shutter for pump imaging
                # if S.bool_pump_imaging:
                    # X.Rb_repump_AOM_shutter_open()
                X.optical_depump_srs_shutter_closed()         # opens depumping shutter
                X.main_optical_pump_srs_shutter_closed()                     # opens main pumping shutter
                X.set_Rb85_optical_pump_dF(-100)    # sets the depumping light to the right frequency
                X.Rb_optical_pump.set_amplitude(0)      # turns the depumping AOM to desired power
                # X.wait_ms(5)
            # Start pump imaging process
            if S.bool_pump_imaging:
                if S.bool_pump_imagine_IPG_axis:
                    X.wait_ms(4)
                    if not S.bool_forced_depump_Rb:
                        X.main_optical_pump_srs_shutter_open()
                    X.Rb_repump_AOM_shutter_open()
                else:
                    X.Rb_repump_mot_shutter_open()
                    X.wait_ms(4)   #shutter has a delay of about 3.5ms from signal to opening
                    X.Rb_repump_AOM_shutter_open()
            
            if S.bool_forced_depump_Rb:
                if not S.bool_pump_imagine_IPG_axis:
                    X.main_optical_pump_srs_shutter_closed()  
                X.optical_depump_srs_shutter_closed()         # opens depumping shutter
                X.set_Rb85_optical_pump_dF(-100)    # sets the depumping light to the right frequency
                X.Rb_optical_pump.set_amplitude(0)      # turns the depumping AOM to desired power   
            
            # Start opening absorption shutter (has 5ms delays time)
            X.Rb_abs_shutter_on()
            X.wait_ms(S.abs_shutter_delay_ms - S.SPI_turnoff_ms)
            # Turn off dipole traps (if before pumping)
            ##X.util_trig_low()
            if not S.bool_pump_imaging_in_odt:
                if S.bool_SPI or S.bool_SPIPG:
                    X.spi_control(0,0)                            # turning off SPI-beam (takes 15us)
                    X.wait_ms(S.SPI_turnoff_ms)
                if S.bool_IPG or S.bool_SPIPG or S.bool_tweezer_load_Rb_on_Li:
                    # #X.util_trig_low()
                    X.set_IPG_AOM_driver_input_amplitude(0)    # turning off IPG-AOM (less than 1us?)
                    X.IPG_shutter_close()
                    if S.bool_IPG_cross:
                        # X.set_util_trig_high()
                        X.set_IPG_cross_amplitude(0)
                        # X.set_util_trig_low()
            
            
            # Pump atoms to F=3 state (pump imaging)
            if S.bool_pump_imaging:
                X.set_Rb85_repump_dF(S.Rb.repump_abs_dF)   
                X.Rb_repump.set_amplitude(S.Rb.repump_abs_ampl)
                X.wait_ms(S.pump_ms)
                X.Rb_repump_off()
                if S.bool_pump_imagine_IPG_axis:
                    X.main_optical_pump_srs_shutter_closed()
                else:
                    pass
                    X.Rb_repump_mot_shutter_closed()   
            # ##X.util_trig_high()
            # Turn off dipole traps (if after pumping)
            if S.bool_pump_imaging_in_odt:
                if S.bool_SPI or S.bool_SPIPG:
                    X.spi_control(0,0)                            # turning off SPI-beam (takes 15us)
                    X.wait_ms(S.SPI_turnoff_ms)
                if S.bool_IPG or S.bool_SPIPG or (S.bool_Li and S.bool_tweezer_load_Rb_on_Li):
                    # #X.util_trig_low()
                    X.set_IPG_AOM_driver_input_amplitude(0)    # turning off IPG-AOM (less than 1us?)
                    if S.bool_IPG_cross:
                        # X.set_util_trig_high()
                        X.set_IPG_cross_amplitude(0)
                        # X.set_util_trig_low()
                    X.IPG_shutter_close()
            
            # Wait for some expansion time
            X.wait_ms(S.expansion_ms)
            # #X.util_trig_low()

           
            

        ## take atom image
        t0 = X.labels.next()
        X.set_time_marker(t0)
        #print 'DEBUG1',X.get_time_marker(t0),X.get_time()
        X.trigger_pixelink('image_%i')                       # trigger camera for image with atoms
        X.set_Rb85_pump_dF(S.Rb.pump_abs_dF)                # set pump AO to resonance
        X.Rb_pump.set_amplitude(S.Rb.pump_abs_ampl)
        X.wait_ms(S.Pixelink.expTime_ms)
        X.Rb_pumpAOM_off()                                    # turn off abs. beam
        X.Rb_abs_shutter_off()                                # close abs. beam shutter
        #print 'DEBUG2',X.get_time_marker(t0),X.get_time()
        #print 'DEBUG3',S.Pixelink.expTime_ms,S.Pixelink.wait_ms
        X.goto_ms(S.Pixelink.wait_ms,t0)
        # #X.util_trig_low()
        X.spi_control(0,0) 
        ## take dark image
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('dark_%i')                         # trigger camera for dark image
        X.goto_ms(S.Pixelink.wait_ms - S.abs_shutter_delay_ms - S.pump_ms,t0)
        X.Rb_abs_shutter_on()                                # begin opening abs. beam shutter (takes 5ms)
        X.goto_ms(S.Pixelink.wait_ms,t0)
        
        ## take background image
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('backgnd_%i')                     # trigger camera for background image
        X.set_Rb85_pump_dF(S.Rb.pump_abs_dF)                #set pump AO to resonance
        X.Rb_pump.set_amplitude(S.Rb85.pump_abs_ampl)
        X.wait_ms(S.Pixelink.expTime_ms)
        X.Rb_pumpAOM_off()                                    # turn off abs. beam
        X.Rb_abs_shutter_off()                                # close abs. beam shutter
        X.goto_ms(S.Pixelink.wait_ms,t0) 
        
        # #X.util_trig_low()
    ### FLOURECENCE IMAGING - IPG AND SPI###
    if S.bool_fluorescence_imaging:
        ##open apogee shutter 
        ##turn off tweezer 
        ##but make sure mot light on first
        ##mark start camera shutter open (full at ~10ms)
     
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('image_%i')
        
        # Ensure light is off, then open shutters, if atoms were trapped not in MOT
        # If magnetically trapped, coils turned to MOT values here, to give enough time.
        if (S.bool_tweezer_load or S.bool_load_rb_magnetic_trap) and S.bool_recapture:
            X.Rb_repump_off()
            X.Rb_pumpAOM_off()
            if S.bool_load_rb_magnetic_trap:
                X.mot_coil_enabled()
                X.set_mot_coil_I(S.Rb.coil_fl_image_I)
            X.goto_ms(S.Apogee.shutterDelay_ms-S.mot_shutter_delay_ms,t0)#start mot shutter to open w/camera
            #X.mot_shutter_on()
            X.wait_ms(S.mot_shutter_delay_ms)
        
        # Turn off MOT light so that MOT imaged is actually a recaptured MOT (mot shutter still open)
        if not (S.bool_tweezer_load or S.bool_load_rb_magnetic_trap):
            X.Rb_pumpAOM_off()
            X.Rb_repump_off()
            
        # Turn on lasers to start image
        X.goto_ms(S.Apogee.shutterDelay_ms+.01, t0)#now camera full open
        X.Rb_pump.set_amplitude(S.Rb.pump_fl_image_ampl) 
        X.Rb_repump_on() 
        
        # Image is now being taken, so turn off ODT
        if S.bool_tweezer_load :
            X.spi_control(0,0)
            X.set_IPG_AOM_driver_input_amplitude(0)
            X.IPG_shutter_close()
        
        # While camera is open, recapture atoms for specified time, then close mot shutter
        if (S.mot_shutter_delay_ms>S.recapture_time_ms):
            #X.mot_shutter_off()
            X.wait_ms(S.recapture_time_ms) #recapture finished
        else:
            X.wait_ms(S.recapture_time_ms - S.mot_shutter_delay_ms)
            #X.mot_shutter_off()
            X.wait_ms(S.mot_shutter_delay_ms)
        
        # Turn light off to end recapture of MOT. Should happen just before camera shutter closes. 
        X.Rb_repump_off()
        X.Rb_pumpAOM_off()
        
        ##Shutter Closed
        X.wait_ms(500) # to give the apogee time to finish
        
        ## Now take background image
        t0 = X.labels.next()
        X.set_time_marker(t0)##mark start camera shutter open (full at ~10ms)
        X.trigger_pixelink('backgnd_%i')
        ##ensure all light off, then open MOT shuuter
        X.Rb_repump_off()
        X.Rb_pumpAOM_off()
        X.goto_ms(S.Apogee.shutterDelay_ms-S.mot_shutter_delay_ms,t0)#start mot shutter to open w/camera
        #X.mot_shutter_on()
        X.goto_ms(S.Apogee.shutterDelay_ms+.01, t0)#now camera full open
        ## turn on lasers to start image
        X.Rb_pump.set_amplitude(S.Rb.pump_fl_image_ampl) 
        X.Rb_repump_on()
        ## While camera is open, recapture atoms for specified time, then close mot shutter
        if (S.mot_shutter_delay_ms>S.recapture_time_ms):
            #X.mot_shutter_off()
            X.wait_ms(S.recapture_time_ms) #recapture finished
        else:
            X.wait_ms(S.recapture_time_ms - S.mot_shutter_delay_ms)
            #X.mot_shutter_off()
            X.wait_ms(S.mot_shutter_delay_ms)
        ## light off
        X.Rb_repump_off()    
        X.Rb_pumpAOM_off()
        X.wait_ms(500) # to give the apogee time to finish
    
    
    ## FLOURESCENCE MOT IMAGING WITH THE PIXELINK CAMERA
    if S.Rb.bool_pixelink_flourescence_imaging and not S.bool_load_rb_magnetic_trap:
        ##X.util_trig_high()
        # Take image to flush camera. While waiting for camera to finish, close slowing beam shutter.
        # moved because it takes up time while MOT is loading
        t0 = X.labels.next()
        X.set_time_marker(t0)
        # print 'taking clearing image in take_Li_image'
        X.trigger_pixelink('flush_%i')                    # trigger camera to flush 
        X.wait_ms(S.Pixelink.expTime_ms)           #time for camera to get ready for another
        X.wait_ms(S.Pixelink.wait_ms)
    
        print "============taking Rb image===================\n"
        #print 'Triggers Count: ', X.pixelink_triggers_count 
    
        X.Rb_pump.set_amplitude(S.Rb85.pump_PL_fl_amplitude)
        X.Rb_repump.set_amplitude(S.Rb85.repump_PL_fl_amplitude)
    
    
        # Set all parameters to take flourescence image of MOT
        
        set_magnetic_field_A(X,S,S.Rb85.coil_PL_fl_A)
        # X.set_mot_coil_I(S.Rb85.coil_PL_fl_A)
        X.set_comp_coils_V(S.Rb85.compx_PL_fl,S.Rb85.compy_PL_fl,S.Rb85.compz_PL_fl)    
        X.set_Rb85_pump_dF(S.Rb85.pump_PL_fl_F)
        X.set_Rb85_repump_dF(S.Rb85.repump_PL_fl_dF)    
        X.Zeeman_Slower_shutter_close()
        if S.bool_zeeman_slower:
            X.Rb_zeeman_slower.set_amplitude(0)    
        X.wait_ms(10)# ------------------------------------------------------ This seems to help, not sure why but it may have to do with comp coils settling -- 2015/11/15 -- Kahan
        # Take picture with atoms (and turn up AOM amplitude)
        # #X.util_trig_low()
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('image_%i')         # trigger camera for image with atoms
        X.Rb_pump.set_amplitude(S.Rb85.pump_PL_fl_amplitude)
        X.Rb_repump.set_amplitude(S.Rb85.repump_PL_fl_amplitude)
        X.wait_ms(S.Pixelink.expTime_ms)  
        X.wait_ms(S.Pixelink.wait_ms)
        
        
        print "============after Rb image===================\n"
        
        # take background image
        X.set_mot_coil_I(0)
        X.Rb_pump.set_amplitude(0)
        X.wait_ms(20) #use to be 20, but still sw rb mot
        
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('backgnd_%i')                       # trigger camera for image without atoms
        X.Rb_pump.set_amplitude(S.Rb85.pump_PL_fl_amplitude)  # with backround light
        X.Rb_repump.set_amplitude(S.Rb85.repump_PL_fl_amplitude)
        X.wait_ms(S.Pixelink.expTime_ms)  
        X.wait_ms(S.Pixelink.wait_ms)
        #X.util_trig_low()

    if S.Rb.bool_pixelink_flourescence_imaging and S.bool_load_rb_magnetic_trap:
        # Take image to flush camera. While waiting for camera to finish, close slowing beam shutter.
        t0 = X.labels.next()
        X.set_time_marker(t0)
        print 'taking clearing image in take_Li_image'
        X.trigger_pixelink('flush_%i')                    # trigger camera to flush 
        X.wait_ms(S.Pixelink.expTime_ms)           #time for camera to get ready for another
        X.wait_ms(S.Pixelink.wait_ms) 
        
        # set mot loading variables
        # X.Rb_repump.set_amplitude(S.Rb.repump_load_ampl)
        X.set_Rb85_repump_dF(S.Rb.repump_load_dF)                     # set repump frequency
        X.set_Rb85_pump_dF(S.Rb.pump_load_dF)
        X.Rb_zeeman_slower.set_amplitude(0)
        X.set_comp_coils_V(S.Rb.compx_load,S.Rb.compy_load,S.Rb.compz_load)      # set compensation coils
        X.set_supply_max_current(S.Rb.mot_coil_gradient_load_A)
        X.wait_ms(10)
        
        X.Rb_pump.set_amplitude(S.Rb.pump_load_ampl)
        X.Rb_repump.set_amplitude(S.Rb.repump_load_ampl)
        X.wait_ms(10)
        
        # Set all parameters to take flourescence image of MOT
        X.set_supply_max_current(S.Rb85.coil_PL_fl_A)
        X.set_comp_coils_V(S.Rb85.compx_PL_fl,S.Rb85.compy_PL_fl,S.Rb85.compz_PL_fl)    
        X.set_Rb85_pump_dF(S.Rb85.pump_PL_fl_F)
        X.set_Rb85_repump_dF(S.Rb85.repump_PL_fl_dF)    
        
        X.wait_ms(10)        
        
        # Take picture with atoms (and turn up AOM amplitude)
        # #X.util_trig_low()
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('image_%i')         # trigger camera for image with atoms
        X.Rb_pump.set_amplitude(S.Rb85.pump_PL_fl_amplitude)
        X.Rb_repump.set_amplitude(S.Rb85.repump_PL_fl_amplitude)
        X.wait_ms(S.Pixelink.expTime_ms)  
        X.wait_ms(S.Pixelink.wait_ms)
        
        # flush mot
        X.Rb_pump.set_amplitude(0)
        X.Rb_repump.set_amplitude(0)
        X.set_supply_max_current(0)
        X.wait_ms(20) #use to be 20, but still sw rb mot
        
        # set mot loading variables
        # X.Rb_repump.set_amplitude(S.Rb.repump_load_ampl)
        X.set_Rb85_repump_dF(S.Rb.repump_load_dF)                     # set repump frequency
        X.set_Rb85_pump_dF(S.Rb.pump_load_dF)
        X.Rb_zeeman_slower.set_amplitude(0)
        X.set_comp_coils_V(S.Rb.compx_load,S.Rb.compy_load,S.Rb.compz_load)      # set compensation coils
        X.set_supply_max_current(S.Rb.mot_coil_gradient_load_A)
        X.wait_ms(10)
        
        X.Rb_pump.set_amplitude(S.Rb.pump_load_ampl)
        X.Rb_repump.set_amplitude(S.Rb.repump_load_ampl)
        X.wait_ms(10)
        
        # Set all parameters to take flourescence image of MOT
        X.set_mot_coil_I(S.Rb85.coil_PL_fl_A)
        X.set_comp_coils_V(S.Rb85.compx_PL_fl,S.Rb85.compy_PL_fl,S.Rb85.compz_PL_fl)    
        X.set_Rb85_pump_dF(S.Rb85.pump_PL_fl_F)
        X.set_Rb85_repump_dF(S.Rb85.repump_PL_fl_dF)    
        
        X.wait_ms(10)        
        
        # Take picture with atoms (and turn up AOM amplitude)
        # #X.util_trig_low()
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('image_%i')         # trigger camera for image with atoms
        X.Rb_pump.set_amplitude(S.Rb85.pump_PL_fl_amplitude)
        X.Rb_repump.set_amplitude(S.Rb85.repump_PL_fl_amplitude)
        X.wait_ms(S.Pixelink.expTime_ms)  
        X.wait_ms(S.Pixelink.wait_ms)
        
def take_Li_image(X,S):  
    '''
    Takes 3 images using Li settings: 
    - A flush image to clear off any background noise on the CCD chip
    - An image with the atoms in whichever trap
    - A background image used to later calibrate the image with atoms

    Can be configured to do absorption imaging or fluorescence imaging of Li.
    The fluorescence imaging is set up to let you recapture from an ODT or magnetic trap and image the resulting MOT.

    INPUTS:
    - X: The MOL Experiment Recipe instance
    - S: The settings module instance
    '''
    if S.bool_absorption_imaging:
        #if not (S.bool_cool_mot or S.bool_tweezer_load):
        X.trigger_pixelink()                    # trigger camera to flush 
        X.wait_ms(S.Pixelink.wait_ms)
        #if cool it takes this pic in cool function b4 cooling
            # print 'taking clearing image in take_Li_image'
            #X.trigger_pixelink()                    # trigger camera to flush 
            #X.wait_ms(S.Pixelink.wait_ms)           #time for camera to get ready for another
        
        #############################
        ### if tweezer was loaded ###
        #############################
        if S.bool_tweezer_load:  
            # X.set_Li_repump_amplitude(0)
            # X.Li_repump_abs_shutter_open()
            # X.set_Li_repump_dF(S.Li6.repump_abs_dF)                # set pump AO to resonance
            # X.set_Li_pump_dF(S.Li6.pump_abs_dF)          
            X.Li_repump_abs_shutter_open()
            # feshbach_field_disable(X,S)  # we can't do this here as it will disable high field imaging!
            if S.bool_high_field_imaging:
                X.Li_HF_imaging_shutter_open()
            else:
                X.Li_pump_abs_shutter_open()
                feshbach_field_disable(X,S) 
            X.wait_ms(20)
            ##X.util_trig_high()            
            t0 = X.labels.next()
            X.set_time_marker(t0)
            # print '******************************in Tweezer image'
            # X.set_comp_coils_V(S.compx_zero,S.compy_zero,S.compz_zero)
            X.set_comp_coils_V(0,0,0)
            # This ASSUMES Feshbach field is already on
            # if S.bool_high_field_imaging:
        
                
            # Use MOT Repump Light (NO by default)
            # if S.bool_Li_absimage_motrepump_on: 
                # X.Li_repump_shutter_on()
                # X.LiRb_mot_shutter_on()             #begin opening LiRb mot shutter (takes 11.1s)
                # print "############open mot shutter"                                    #also requires repump shutter open -- should be
                                                    #unless pumping to upper state & fear small repump light
            
            # Open shutters such that they are full open for atom picture
            # Use counterprop absorption beam (YES by default)
            if not S.bool_high_field_imaging:
                X.goto_ms(S.Li_abs_imaging_delay_ms-S.Li_repump_abs_shutter_open_delay_ms,t0) #5.38
                X.Li_repump_abs_shutter_open()      # On for both HF and 0F imaging
                X.goto_ms(S.Li_abs_imaging_delay_ms-S.Li_pump_abs_shutter_open_delay_ms,t0) #4.06
                X.Li_pump_abs_shutter_open()
            # X.goto_ms(S.Li_abs_imaging_delay_ms-S.Li_high_field_imaging_no_bounce_on_action,t0)  #2.74
            # if S.bool_high_field_imaging:
                # X.high_field_imaging_shutter_on()
       
            # Set imaging detunings
            if S.bool_high_field_imaging:
                X.set_Li_imaging_F(S.Li6.high_field_abs_F)
            else:             
                X.set_Li_pump_dF(S.Li6.pump_abs_dF)  
                X.set_Li_repump_dF(S.Li6.repump_abs_dF)     # needed for high field imaging
            
            # Turn off trapping lasers
            if (S.bool_SPI or S.bool_SPIPG) and not S.bool_SPIPG_transfer:
                X.goto_ms(S.Li_abs_imaging_delay_ms-S.expansion_ms-S.SPI_turnoff_ms,t0) 
                # Found it was better to turn off SPI right before image was taken...
                X.spi_control(0,0)    
            elif S.bool_IPG or S.bool_SPIPG or S.bool_IPG_turnon_ramp or S.bool_special or S.bool_SPIPG_transfer:   
                X.goto_ms(S.Li_abs_imaging_delay_ms-S.expansion_ms,t0) 
                X.IPG_shutter_close()
                if S.bool_evaporate_into_IPG_cross:
                    ##X.util_trig_high()
                    X.set_IPG_cross_amplitude(0) 
                    # #X.util_trig_low()  
                # X.util_trig_high()                    
                X.set_IPG_AOM_driver_input_amplitude(0)    # turning off IPG-AOM (less than 1us?)
                # X.wait_us(3)
                ## the time from sending the trigger to the IPG AOM reacting is 3.5us 
                ## and it takes additional 2.5us to turn off completely 
                # X.set_TS1_main_AOM_amplitude(0)
                # X.set_TS1_main_AOM_F(80)
                
                # X.IPG_shutter_close()            
                # print '******************************in IPG turnoff'
            
            # Allow for balistic expansion
            #X.util_trig_low()
            # X.goto_ms(S.Li_abs_imaging_delay_ms,t0)
            X.wait_ms(S.expansion_ms)
            
            
            
        ######################################
        ## if no tweezer -- direct from mot ##
        ######################################
        else:
            # print 'not in tweezerload'
            # S.Li_pump_shutter_off_start_ms = S.Li_pump_shutter_off_delay_ms-S.Li_pump_shutter_off_duration_ms
            
            # If 'coolmot' stage, do the cooling at this point
            if S.bool_cool_mot:
                set_Li_cool(X,S)
                if S.Li6.mot_cool_ms > S.Li_pump_shutter_off_start_ms:
                    X.wait_ms(S.Li6.mot_cool_ms -S.Li_pump_shutter_off_start_ms) 
            
            # Close MOT Shutters, and turn off AOMs
            # At the same time, open abs. imaging shutters
            # Li_abs_imaging_delay is the time from t0 to when the atom expansion should start
            t0 = X.labels.next()
            X.set_time_marker(t0)
            X.goto_ms(S.Li_abs_imaging_delay_ms-S.Li_pump_abs_no_bounce_on_delay_ms,t0)
            X.Li_pump_abs_shutter_open()
            X.goto_ms(S.Li_abs_imaging_delay_ms-S.Li_pump_no_bounce_off_delays_ms,t0)
            #X.Li_pump_shutter_off()
            X.goto_ms(S.Li_abs_imaging_delay_ms-S.Li_repump_no_bounce_off_delays_ms,t0)
            # X.Li_repump_shutter_off()
            X.goto_ms(S.Li_abs_imaging_delay_ms,t0)
            ##turn of AOMS
            
            X.set_Li_repump_dF(S.Li6.repump_abs_dF)                # set pump AO to resonance
            X.set_Li_pump_dF(S.Li6.pump_abs_dF)  
            
            # X.goto_ms(S.Li_pump_shutter_off_delay_ms + S.expansion_ms -S.Li_pump_abs_shutter_on_delay_ms,t0)##   
            # so expansion must be<Li_pump_abs_shut_delay_ms-Li_pump_shutter_off_duration_ms
            # X.Li_pump_abs_shutter_open()              
            # X.goto_ms(S.Li_pump_shutter_off_start_ms,t0) # start of expansion
            # X.set_Li_pump_amplitude(0)
            # if X.get_time(reference=t0)*1000 <=S.Li_pump_shutter_off_delay_ms + S.expansion_ms:
                # X.goto_ms(S.Li_pump_shutter_off_delay_ms + S.expansion_ms ,t0)#time for image
        ## take atom image
        ## Trigger Camera, then turn light to correct settings (shutters are open)
        ## After image, turn off light
        t0 = X.labels.next()
        X.set_time_marker(t0)
        # X.util_trig_low()
        X.trigger_pixelink('image_%i')                       # trigger camera for image with atoms
        if S.bool_high_field_imaging:
            X.set_Li_imaging_amplitude(S.Li6.high_field_abs_amplitude)  
        else:
            X.set_Li_pump_amplitude(S.Li6.pump_abs_amplitude)             
            X.set_Li_repump_amplitude(S.Li6.repump_abs_amplitude)
        # print '***setting abs values******',S.Li6.pump_abs_dF,S.Li6.repump_abs_dF,S.Li6.pump_abs_amplitude,S.Li6.repump_abs_amplitude
        # X.util_trig_low()
        X.wait_ms(S.Pixelink.expTime_ms)
        # Turn off light after image is taken
        # X.spi_control(0,0) 
        
        X.set_Li_pump_amplitude(0)
        X.set_Li_repump_amplitude(0)
        X.set_Li_repump_dF(-100)                # set pump AO to resonance
        X.set_Li_pump_dF(-100)
        X.set_Li_imaging_amplitude(0)  
        X.set_Li_imaging_F(0)
        X.goto_ms(S.Pixelink.wait_ms,t0)
        ## take dark image
        ## All light is off
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('dark_%i')                         # trigger camera for dark image
        # ##X.util_trig_high()
        X.wait_ms(S.Pixelink.expTime_ms)
        # X.wait_ms(0.06)
        # #X.util_trig_low()
        # Finally, need to take background image. For this, we want all light off (including SPI)
        # However, the SPI gets turned off right before image (same as in atom image)
        # if S.bool_SPI and S.bool_tweezer_load:
            # X.spi_control(S.SPI_power_set,1)
        # X.Li_pump_abs_shutter_open()                            # begin opening abs. beam shutter (takes 5ms)
        # X.goto_ms(S.Pixelink.wait_ms + S.Li_pump_abs_shutter_on_delay_ms,t0)
        # if S.bool_SPI: #turns off spi right before taking background just like for the image
            # X.goto_ms(S.Pixelink.wait_ms-S.SPI_turnoff_ms,t0)
            # X.spi_control(0,0)              
        # else:
        X.goto_ms(S.Pixelink.wait_ms,t0)
        
        ## take background image
        # if S.bool_Li_absimage_absrepump_on:
            # X.set_Li_repump_amplitude(S.Li6.repump_abs_fiber_amplitude)    
        # if S.bool_Li_absimage_motrepump_on:
            # X.set_Li_repump_amplitude(S.Li6.repump_abs_amplitude)    
        # X.set_Li_repump_dF(S.Li6.repump_abs_dF)                # set pump AO to resonance
        # X.set_Li_pump_dF(S.Li6.pump_abs_dF)                # set pump AO to resonanceX.set_mot_coil_I(0)
        # X.set_Li_pump_amplitude(S.Li6.pump_abs_amplitude)
        # X.set_Li_repump_amplitude(S.Li6.repump_abs_amplitude)
        
        # For background image, set light to same conditions as atoms image
        if S.bool_high_field_imaging:
            X.set_Li_imaging_F(S.Li6.high_field_abs_F)
        else:             
            X.set_Li_pump_dF(S.Li6.pump_abs_dF)     
            X.set_Li_repump_dF(S.Li6.repump_abs_dF)  
        
        
        # ##X.util_trig_high()
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('backgnd_%i')                       # trigger camera for image with atoms
        if S.bool_high_field_imaging:
            X.set_Li_imaging_amplitude(S.Li6.high_field_abs_amplitude)
            print '\n########################################################'
            print 'here'
            print '########################################################\n'  
        else:
            X.set_Li_pump_amplitude(S.Li6.pump_abs_amplitude)               
            X.set_Li_repump_amplitude(S.Li6.repump_abs_amplitude)
        # print '***setting abs values******',S.Li6.pump_abs_dF,S.Li6.repump_abs_dF,S.Li6.pump_abs_amplitude,S.Li6.repump_abs_amplitude
        X.wait_ms(S.Pixelink.expTime_ms)
        # X.wait_ms(0.06)
        # #X.util_trig_low()
        # Turn off light after image is taken
        X.set_Li_pump_amplitude(0)
        X.set_Li_repump_amplitude(0)
        X.set_Li_repump_dF(-100)                # set pump AO to resonance
        X.set_Li_pump_dF(-100)
        X.set_Li_imaging_amplitude(0)  
        X.set_Li_imaging_F(0)
        X.goto_ms(S.Pixelink.wait_ms,t0)

        # Close absorption shutters and set MOT coils back to load setting
        X.Li_pump_abs_shutter_close()
        X.wait_ms(100)
        X.Li_repump_abs_shutter_close()
        X.Li_HF_imaging_shutter_closed()
        # X.wait_s(1)
        if S.bool_high_field_imaging:
            #X.high_field_imaging_shutter_off()
            #X.set_gradient_coils_I(0)
            feshbach_field_disable(X,S)   

    
    if S.Li6.bool_pixelink_flourescence_imaging:
        # The following section is for doing flourescence imaging, whether it is for recapture imaging or just normal MOT imaging.
        if S.bool_tweezer_load and not S.Li6.bool_Li_Magnetic_Trap:
            # If we ran the dipole trap the magnetic field is disabled, requiring us to reenable the field and set it to antihelmholtz
            set_field_config_antihemholtz(X,S)
            X.wait_ms(25) #This wait time is to let the coils settle

        # We then set the magnetic field to be the imaging field. We don't need a wait to let it settle as the light is turned on many ms later.
        set_magnetic_field_A(X,S,S.Li6.coil_PL_fl_A)

        # Here we trigger the camera to take a flush image to clear the CCD chip.
        # We have to wait here because the CCD takes some time to dump all of the data. 
        # The time it takes is dependent on the ROI so we have simply set this time to be sufficiently long so that, no matter how large we choose the ROI, the camera has enough time to read off the data.
        # We can wait a slightly shorter time here since the code below takes ~25ms, allowing us to take the atom image after the correct amount of time.
        X.trigger_pixelink()
        X.wait_ms(S.Pixelink.wait_ms-10) # the 10ms comes from the comp coil settle time below. We don't need to subtract it but this minimizes the duration we spend in this function.

        # Here we turn off the ZS beam just in case it was still on
        if S.bool_zeeman_slower:
            X.set_Li_zeeman_slower_amplitude(0)
            X.Zeeman_Slower_shutter_close()
        
        # We change the comp coils to the imaging settings and wait some time for them to settle.
        X.set_comp_coils_V(S.Li6.compx_PL_fl,S.Li6.compy_PL_fl,S.Li6.compz_PL_fl) 
        X.wait_ms(10)
        
        if S.bool_tweezer_load or S.Li6.bool_Li_Magnetic_Trap:
            # We place a time marker to carry out the following procedure in a well defined manner.
            # Since the procedure only concerns the ODT and magnetic trap recapture imaging, we only set the marker inside this if statement.
            t0 = X.labels.next()
            X.set_time_marker(t0)
            # The MOT light is shuttered during the ODT and the magnetic trap, so we open it here.
            # We do this so that the shutter is open right before the AOMs turn the light on.
            X.goto_ms(S.Li_PL_fl_imaging_delay_ms- S.Li_MOT_shutter_open_delay_ms,t0)
            X.Li_MOT_shutter_open()
            if S.bool_IPG or S.bool_SPIPG or S.bool_SPIPG_transfer:
                # Recapture imaging has never been done from the IPG before so this will need work. We might want to shutter with the AOM as well to do thing quickly. -- Kahan -- 20150226
                X.IPG_shutter_close()
            if S.bool_SPI or S.bool_SPIPG or S.bool_SPIPG_transfer:
                # If SPI is on, turn it off and close the IPG shutter. The SPI takes some time to turn off so we start the process so that the imaging light turns on right when it is done.
                X.goto_ms(S.Li_PL_fl_imaging_delay_ms- S.SPI_turnoff_ms,t0)
                X.spi_control(0,0) 
            # We then go to the correct time for the ODT/magnetic trap procedure to be done before turning on the imaging light.
            X.goto_ms(S.Li_PL_fl_imaging_delay_ms,t0)

        # Here we turn on the imaging light and set the correct detunings.
        X.set_Li_pump_amplitude(S.Li6.pump_PL_fl_amplitude)
        X.set_Li_pump_dF(S.Li6.pump_PL_fl_F)
        X.set_Li_repump_amplitude(S.Li6.repump_PL_fl_amplitude)
        X.set_Li_repump_dF(S.Li6.repump_PL_fl_dF)

        # Take the picture with atoms
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('image_%i')
        X.wait_ms(S.Pixelink.expTime_ms)  
        X.wait_ms(S.Pixelink.wait_ms)

        # Turn off the magnetic field so that any leftover atoms are released from the trap for our background image.
        X.set_mot_coil_I(0)
        X.wait_ms(20)

        # Take the background image
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('backgnd_%i')
        X.wait_ms(S.Pixelink.expTime_ms)  
        X.wait_ms(S.Pixelink.wait_ms)
    
    if S.bool_loaded_mot_flourescence_imaging_apogee:
        apogee_mot_floresence(X,S)
        X.wait_ms(S.Apogee.wait_ms) # to give the apogee time to finish
        apogee_mot_floresence(X,S)
        X.wait_ms(S.Apogee.wait_ms) # to give the apogee time to finish
        apogee_mot_floresence(X,S)
        X.wait_ms(S.Apogee.wait_ms) # to give the apogee time to finish
    
    # Here we change the field so that we can load a MOT again.
    X.set_mot_coil_I(S.Li6.mot_coil_gradient_load_A)

def take_dual_image(X,S):
    # Attempt to take an image of both Li and Rb sequentially. Written for IPG single arm to start ONLY.
    
    if S.bool_tweezer_load:                 
        t0 = X.labels.next()
        X.set_time_marker(t0)
        # print '******************************in Dual image'
        X.set_comp_coils_V(S.compx_zero,S.compy_zero,S.compz_zero)
        
        
        # Open shutters such that they are full open for atom picture
        # Use counterprop absorption beam (YES by default)
        X.goto_ms(S.Li_abs_imaging_delay_ms-S.Li_repump_abs_no_bounce_on_action_ms,t0) #5.38
        X.Li_repump_abs_shutter_open()      # On for both HF and 0F imaging
        X.goto_ms(S.Li_abs_imaging_delay_ms-S.Li_pump_abs_no_bounce_on_action_ms,t0) #4.06
        
        # Open the correct shutter for imaging light
        if not S.bool_high_field_imaging:
            X.Li_pump_abs_shutter_open()
        X.goto_ms(S.Li_abs_imaging_delay_ms-S.Li_high_field_imaging_no_bounce_on_action,t0)
        # if S.bool_high_field_imaging:
            #X.high_field_imaging_shutter_on()
        
        # Set imaging detunings
        if S.bool_high_field_imaging:
            X.set_Li_imaging_F(S.Li6.high_field_abs_F)
        else:             
            X.set_Li_pump_dF(S.Li6.pump_abs_dF)  
        X.set_Li_repump_dF(S.Li6.repump_abs_dF)

        # Turn off trapping lasers
        # NOTE: IPG shutter is left open, since we need to turn laser back on to recpature Rb
        # This does not allow for any ballistic expansion (or else we would not recpature Rb)
        if S.bool_SPI or S.bool_SPIPG:
            X.goto_ms(S.Li_abs_imaging_delay_ms-S.SPI_turnoff_ms,t0) 
            X.spi_control(0,0)    
        if S.bool_IPG or S.bool_SPIPG or S.bool_IPG_turnon_ramp or S.bool_special or S.bool_SPIPG_transfer:   
            X.goto_ms(S.Li_abs_imaging_delay_ms,t0) 
            if S.bool_evaporate_into_IPG_cross:
                X.set_IPG_cross_amplitude(0)                    
            X.set_IPG_AOM_driver_input_amplitude(0)
            
        ## Take Li Atom Image
        
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('image_%i')                       # trigger camera for image with atoms
        if S.bool_high_field_imaging:
            X.set_Li_imaging_amplitude(S.Li6.high_field_abs_amplitude)  
        else:
            X.set_Li_pump_amplitude(S.Li6.pump_abs_amplitude)              
        X.set_Li_repump_amplitude(S.Li6.repump_abs_amplitude)
        X.wait_ms(S.Pixelink.expTime_ms)
        # Turn off imaging light after image is taken, and turn back on dipole trap to recpature Rb
        # NOTE: We need to specify which IPG power to recapture that atoms at... same power as before? Or High power
        X.set_IPG_AOM_driver_input_amplitude(1)
        if S.bool_evaporate_into_IPG_cross:
            X.set_IPG_cross_amplitude(1)
            
        X.set_Li_pump_amplitude(0)
        X.set_Li_repump_amplitude(0)
        X.set_Li_repump_dF(-100)                
        X.set_Li_pump_dF(-100)
        if S.bool_high_field_imaging:
            X.set_Li_imaging_amplitude(0)  
            X.set_Li_imaging_F(0)
        
        # Wait for camera to readout. 
        X.goto_ms(S.Pixelink.wait_ms,t0)

        # try to finish Li imaging for now...

        # Dark Image is the same...

        ## Set up Rb Absorption Imaging
       
        # Make sure all light is off, shutters closed, magnetic field off
        X.Rb_repump_off()
        X.Rb_optical_pump_off()
        X.main_optical_pump_srs_shutter_closed()
        X.optical_depump_srs_shutter_closed()
        X.Rb_repump_mot_shutter_closed()
        X.Rb_repump_off()
        
        if S.bool_coil_turnoff:
            X.set_mot_coil_I(0)
            X.set_comp_coils_V(S.compx_zero,S.compy_zero,S.compz_zero)
        if S.bool_forced_depump_Rb:
            # If force depump was on, turn off light and close shutters
            # Need to open repump AOM shutter for pump imaging
            # if S.bool_pump_imaging:
                # X.Rb_repump_AOM_shutter_open()
            X.optical_depump_srs_shutter_closed()         # opens depumping shutter
            X.main_optical_pump_srs_shutter_closed()                     # opens main pumping shutter
            X.set_Rb85_optical_pump_dF(-100)    # sets the depumping light to the right frequency
            # X.Rb_optical_pump.set_amplitude(0)      # turns the depumping AOM to desired power
            # X.wait_ms(5)
        
        # Start pump imaging process 
        if S.bool_pump_imaging:
            if S.bool_pump_imagine_IPG_axis:
                X.wait_ms(4)
                if not S.bool_forced_depump_Rb:
                    X.main_optical_pump_srs_shutter_open()
                X.Rb_repump_AOM_shutter_open()
            else:
                X.Rb_repump_mot_shutter_open()
                X.wait_ms(4)   #shutter has a delay of about 3.5ms from signal to opening
                X.Rb_repump_AOM_shutter_open()
        
        if S.bool_forced_depump_Rb:
            if not S.bool_pump_imagine_IPG_axis:
                X.main_optical_pump_srs_shutter_closed()  
            X.optical_depump_srs_shutter_closed()         # opens depumping shutter
            X.set_Rb85_optical_pump_dF(-100)    # sets the depumping light to the right frequency
            # X.Rb_optical_pump.set_amplitude(0)      # turns the depumping AOM to desired power   
            
        # Start opening absorption shutter (has 5ms delays time)
        X.Rb_abs_shutter_on()
        X.wait_ms(S.abs_shutter_delay_ms - S.SPI_turnoff_ms)
        # Turn off dipole traps (if before pumping)  
        if not S.bool_pump_imaging_in_odt:
            if S.bool_SPI or S.bool_SPIPG:
                X.spi_control(0,0)                            # turning off SPI-beam (takes 15us)
                X.wait_ms(S.SPI_turnoff_ms)
            if S.bool_IPG or S.bool_SPIPG or S.bool_tweezer_load_Rb_on_Li:
                X.set_IPG_AOM_driver_input_amplitude(0)    # turning off IPG-AOM (less than 1us?)
                X.IPG_shutter_close()
            if S.bool_IPG_cross:
                X.set_IPG_cross_amplitude(0)
            
            
        # Pump atoms to F=3 state (pump imaging)
        if S.bool_pump_imaging:
            X.set_Rb85_repump_dF(S.Rb.repump_abs_dF)   
            X.Rb_repump.set_amplitude(S.Rb.repump_abs_ampl)
            X.wait_ms(S.pump_ms)
            X.Rb_repump_off()
            if S.bool_pump_imagine_IPG_axis:
                X.main_optical_pump_srs_shutter_closed()
            else:
                pass
                X.Rb_repump_mot_shutter_closed()   
            # Turn off dipole traps (if after pumping)
        if S.bool_pump_imaging_in_odt:
            if S.bool_SPI or S.bool_SPIPG:
                X.spi_control(0,0)                            # turning off SPI-beam (takes 15us)
                X.wait_ms(S.SPI_turnoff_ms)
            if S.bool_IPG or S.bool_SPIPG or (S.bool_Li and S.bool_tweezer_load_Rb_on_Li):
                X.set_IPG_AOM_driver_input_amplitude(0)    # turning off IPG-AOM (less than 1us?)
            if S.bool_IPG_cross:
                X.set_IPG_cross_amplitude(0)
                X.IPG_shutter_close()
        
        # Take Rb Image
        
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('image_%i')                       # trigger camera for image with atoms
        X.set_Rb85_pump_dF(S.Rb.pump_abs_dF)                # set pump AO to resonance
        X.Rb_pump.set_amplitude(S.Rb.pump_abs_ampl)
        X.wait_ms(S.Pixelink.expTime_ms)
        X.Rb_pumpAOM_off()                                    # turn off abs. beam
        X.Rb_abs_shutter_off()                                # close abs. beam shutter
        X.goto_ms(S.Pixelink.wait_ms,t0)
        
        ## Take Dark Image
        
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('dark_%i')                         
        X.goto_ms(S.Pixelink.wait_ms - S.abs_shutter_delay_ms - S.pump_ms,t0)
        X.Rb_abs_shutter_on()                                
        X.goto_ms(S.Pixelink.wait_ms,t0)        
        
        ## Take Rb Background Image
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('backgnd_%i')                     # trigger camera for background image
        X.set_Rb85_pump_dF(S.Rb.pump_abs_dF)                #set pump AO to resonance
        X.Rb_pump.set_amplitude(S.Rb85.pump_abs_ampl)
        X.wait_ms(S.Pixelink.expTime_ms)
        X.Rb_pumpAOM_off()                                    # turn off abs. beam
        X.Rb_abs_shutter_off()                                # close abs. beam shutter
        X.goto_ms(S.Pixelink.wait_ms,t0) 
        
        ## Take Li Background Image
        
        # For background image, set light to same conditions as atoms image
        if S.bool_high_field_imaging:
            X.set_Li_imaging_F(S.Li6.high_field_abs_F)
        else:             
            X.set_Li_pump_dF(S.Li6.pump_abs_dF)      
        X.set_Li_repump_dF(S.Li6.repump_abs_dF)  
        
        
        
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('backgnd_%i')                       # trigger camera for image with atoms
        if S.bool_high_field_imaging:
            X.set_Li_imaging_amplitude(S.Li6.high_field_abs_amplitude)  
        else:
            X.set_Li_pump_amplitude(S.Li6.pump_abs_amplitude)              
        X.set_Li_repump_amplitude(S.Li6.repump_abs_amplitude)
        # print '***setting abs values******',S.Li6.pump_abs_dF,S.Li6.repump_abs_dF,S.Li6.pump_abs_amplitude,S.Li6.repump_abs_amplitude
        X.wait_ms(S.Pixelink.expTime_ms)
        # #X.util_trig_low()
        # Turn off light after image is taken
        X.set_Li_pump_amplitude(0)
        X.set_Li_repump_amplitude(0)
        X.set_Li_repump_dF(-100)                # set pump AO to resonance
        X.set_Li_pump_dF(-100)
        if S.bool_high_field_imaging:
            X.set_Li_imaging_amplitude(0)  
            X.set_Li_imaging_F(0)
        X.goto_ms(S.Pixelink.wait_ms,t0)

        # Close absorption shutters and set MOT coils back to load setting
        X.Li_pump_abs_shutter_close()
        X.Li_repump_abs_shutter_close()
        X.set_mot_coil_I(S.Li6.mot_coil_gradient_load_A)
        # if S.bool_high_field_imaging:
            #X.high_field_imaging_shutter_off()
            #feshbach_field_disable(X,S)
        
def apogee_mot_floresence(X,S):
    t0 = X.labels.next()
    X.set_time_marker(t0)
    X.trigger_pixelink('motimage_%i')  #delay is around 10ms 
    # print '########triggered apogee -setting light'
    X.set_comp_coils_V(S.Li6.compx_fl,S.Li6.compy_fl,S.Li6.compz_fl)
    X.set_Li_pump_amplitude(S.Li6.pump_motfl_image_amplitude)
    X.set_Li_pump_dF(S.Li6.pump_motfl_image_dF)
    X.set_Li_repump_amplitude(S.Li6.repump_motfl_image_amplitude)
    X.set_Li_repump_dF(S.Li6.repump_motfl_image_dF)
    X.goto_ms(S.Apogee.shutterDelay_ms*2+S.Apogee.expTime_ms, t0)
    
    
    
def apogee_shutter_check(X,S):
    #turn off all rb light
    X.Rb_repump_off()   
    X.Rb_pumpAOM_off()
    #X.mot_shutter_off()
    X.wait_ms(S.mot_shutter_delay_ms)
    #trigger apogee
    t0 = X.labels.next()
    X.set_time_marker(t0)
    X.trigger_pixelink('image_%i')  #delay is around 10ms
    #wait for pulse_delay_ms then make repump pulse
    X.wait_ms(S.pulse_delay_ms)
    X.Rb_repump_on()    
    X.wait_ms(S.pulse_time_ms)
    X.Rb_repump_off()    
    
    X.wait_ms(500)
    t0 = X.labels.next()
    X.set_time_marker(t0)##mark start camera shutter open (full at ~10ms)
    X.trigger_pixelink('backgnd_%i')
    X.wait_ms(500) # to give the apogee time to finish

def pixelink_check(X,S):
    # Used to check reflections of SPI into Pixelink camera
    
    # print 'turning on SPI ***********************'
    X.spi_control(S.SPI_pixelink_check_power_set,1)
    X.wait_ms(5)
    t0 = X.labels.next()
    X.set_time_marker(t0)
    X.trigger_pixelink('image_%i')         # trigger camera for image with atoms
    X.wait_ms(S.Pixelink.expTime_ms)  
    X.wait_ms(5)
    X.spi_control(0,0)  
    X.wait_ms(S.Pixelink.wait_ms)
    t0 = X.labels.next()
    X.set_time_marker(t0)
    X.trigger_pixelink('image_%i')         # trigger camera for image with atoms
    X.wait_ms(S.Pixelink.expTime_ms)                          

def take_apogee_image(X,S):
    for nn in range(4):
        t0 = X.labels.next()
        X.set_time_marker(t0)
        X.trigger_pixelink('image_%i')  #delay is around 10ms
        X.wait_ms(1000)

def take_scope_recapture_trace(X,S):
    # Ensure light is off, then open shutters, if atoms were trapped not in MOT
    # If magnetically trapped, coils turned to MOT values here, to give enough time.
        ##open apogee shutter 
        ##turn off tweezer 
        ##but make sure mot light on first
        ##mark start camera shutter open (full at ~10ms)

        # Ensure light is off, then open shutters, if atoms were trapped not in MOT
        # If magnetically trapped, coils turned to MOT values here, to give enough time.
        if (S.bool_tweezer_load or S.bool_load_rb_magnetic_trap) and S.bool_recapture:
            X.Rb_repump_off()
            X.Rb_pumpAOM_off()
            X.mot_coil_enabled()
            #X.mot_shutter_on()
            X.wait_ms(S.mot_shutter_delay_ms)

        # Turn on lasers and coils to start image
        X.Rb_pump.set_amplitude(S.Rb.pump_fl_image_ampl) 
        X.Rb_repump_on()
        X.set_mot_coil_I(S.Rb.coil_fl_image_I)        
        
        # Image is now being taken, so turn off ODT (if on)
        if S.bool_tweezer_load :
            X.spi_control(0,0)
            X.set_IPG_AOM_driver_input_amplitude(0)
            X.IPG_shutter_close()
        
        # While camera is open, recapture atoms for specified time
        X.wait_ms(S.TekScope.scope_recapture_ms) #recapture finished

        # Turn light off to end recapture of MOT. Should happen just before camera shutter closes. 
        X.Rb_repump_off()    
        X.Rb_pumpAOM_off()
        #X.mot_shutter_off()
        X.set_mot_coil_I(0)
        
        ##Shutter Closed
        X.wait_ms(100) # to give the apogee time to finish
        
        
        ## Now take background image

        ##ensure all light off, then open MOT shuuter
        X.Rb_repump_off()
        X.Rb_pumpAOM_off()
        ## turn on lasers to start image
        X.Rb_pump.set_amplitude(S.Rb.pump_fl_image_ampl) 
        X.Rb_repump_on()
        X.wait_ms(100)
        X.set_mot_coil_I(S.Rb.coil_fl_image_I)
        ## now taking image
        X.wait_ms(S.TekScope.scope_recapture_ms)
        ## light off
        X.Rb_repump_off()    
        X.Rb_pumpAOM_off()
        #X.mot_shutter_off()

    
def set_fluorescence_imaging(X,S):
    # If MOT coils turned OFF during ODT trapping, turn them back on now. 
    if S.bool_tweezer_load and S.bool_coil_turnoff:
        X.mot_coil_enabled()
        X.set_mot_coil_I(S.Rb.coil_fl_image_I)
        
    # Open repump shutters. MOT shutter stays closed until image is ready to be taken
    # Give time for AOM shutter to fully open, and coils to turn on
    X.Rb_repump_mot_shutter_open()
    # commented out until nobounce controler in place X.Rb_repump_AOM_shutter_open()
    X.wait_ms(25)             
    
    # Set comp coils so image is taken in same place as MOT loading
    X.set_comp_coils_V(S.Rb.compx_load,S.Rb.compy_load,S.Rb.compz_load)
    
    # Set detunings to get ready for imaging
    X.set_Rb85_pump_dF(S.Rb.pump_fl_image_dF)
    X.set_Rb85_repump_dF(S.Rb.repump_fl_image_dF)


def set_Li_fluorescence_imaging(X,S):
    X.mot_coil_enabled()
    X.set_mot_coil_I(S.Li6.coil_fl_A)
    X.set_Li_pump_amplitude(S.Li6.pump_fl_image_amplitude)
    X.set_Li_pump_dF(S.Li6.pump_fl_image_dF)
    X.set_Li_repump_amplitude(S.Li6.repump_fl_image_amplitude)
    X.set_Li_repump_dF(S.Li6.repump_fl_image_dF)

def set_mot_imaging(X,S):
    # print S.Rb.pump_mot_image_dF
    # print S.Rb.repump_mot_image_dF
    X.set_Rb85_pump_dF(S.Rb.pump_mot_image_dF)
    X.set_Rb85_repump_dF(S.Rb.repump_mot_image_dF)
    
def take_mot_image(X,S,label):
    print 'triggering apogee with %d triggers'%X.apogee_triggers_count
    X.trigger_pixelink(label)
    X.wait_ms(S.Apogee.expTime_ms)

           
#######################################################################################
## Main Sequence for one mot loading
#######################################################################################
def sequence(X,S):
    '''
    define events for one experimental sequence like loading, interacting, imaging
    '''    
    if S.bool_Rb87:
        S.Rb = S.Rb87
    else:
        S.Rb = S.Rb85
    
    init_shutters(X,S)
    X.mot_coil_enabled()
    if S.bool_apply_electic_field:
        X.hv_supply_on()
        X.hv_set_output_voltage(0)
    X.set_LiSS_amplitude(0)

    #if S.bool_Li and S.Li6.bool_pixelink_flourescence_imaging and not (S.bool_tweezer_load or S.Li6.bool_Li_Magnetic_Trap):
    #    X.trigger_pixelink()                    # trigger camera to flush 
    #    X.wait_ms(S.Pixelink.wait_ms)           #time for camera to get ready for another    
    # If scanning the first TS with an AOM, change the frequency here
    if S.bool_scan_TS1_aom or S.change_ts1_aom:
        step = S.stepsize/2
        if S.stepsize <=2.5:
            if S.bool_change_inversion==1:
                X.set_TiSapph1_comb_lock_AOM_F(75.0+S.f1_set_freq/2.0)
                X.wait_s(1)
                X.set_TiSapph1_comb_lock_AOM_F(75.0)
                X.TS1_error_signal_inversion(S.error_signal_inversion)
                X.wait_s(1)
            elif S.bool_change_inversion==2:
                X.set_TiSapph1_comb_lock_AOM_F(75.0+S.f2_set_freq/2.0)
                X.wait_s(1)
                X.set_TiSapph1_comb_lock_AOM_F(75.0)
                X.TS1_error_signal_inversion(S.error_signal_inversion)
                X.wait_s(1)
            elif S.bool_change_inversion==0:
                X.TS1_error_signal_inversion(S.error_signal_inversion)   # 0=normal, 1= inverted
                X.set_TiSapph1_comb_lock_AOM_F(S.TS1_aom_freq)
                X.wait_s(1)
        if S.stepsize>2.5:
            numsteps = round(step/2.5)
            if S.bool_change_inversion==1:
                for n in range(int(round(step/2.5))):
                    X.set_TiSapph1_comb_lock_AOM_F(75.0+S.f1_set_freq/2.0-step+(n+1)*2.5)
                    X.wait_s(.5)
                X.set_TiSapph1_comb_lock_AOM_F(75.0+S.f1_set_freq/2.0)
                X.wait_s(.5)
                X.set_TiSapph1_comb_lock_AOM_F(75.0)
                X.TS1_error_signal_inversion(S.error_signal_inversion)
                X.wait_s(1)
            elif S.bool_change_inversion==2:
                for n in range(int(round(step/2.5))):
                    X.set_TiSapph1_comb_lock_AOM_F(75.0+S.f2_set_freq/2.0-step+(n+1)*2.5)
                    X.wait_s(.5)
                X.set_TiSapph1_comb_lock_AOM_F(75.0+S.f2_set_freq/2.0)
                X.wait_s(.5)
                X.set_TiSapph1_comb_lock_AOM_F(75.0)
                X.TS1_error_signal_inversion(S.error_signal_inversion)
                X.wait_s(1)
            elif S.bool_change_inversion==0:
                X.TS1_error_signal_inversion(S.error_signal_inversion)   # 0=normal, 1= inverted
                for n in range(int(round(step/2.5))):
                    X.set_TiSapph1_comb_lock_AOM_F(S.TS1_aom_freq-step+(n+1)*2.5)
                    X.wait_s(.5)            
                X.set_TiSapph1_comb_lock_AOM_F(S.TS1_aom_freq)

    # If scanning TS1 with its external cavity, set the thick etelon voltage here
    if S.bool_scan_TS1_cavity:
        X.set_tisapph_external_control_voltage(S.PA.TS1_voltage)
    

    if S.bool_dump_mot_at_start:
        if S.bool_Rb:            
            X.Rb_pump.set_amplitude(0)
            X.Rb_repump.set_amplitude(0)      
            set_magnetic_field_A(X,S,0)
            X.wait_ms(50)
            X.mot_coil_enabled()
            X.wait_ms(50)      
        elif S.bool_Li:    
            X.set_Li_pump_amplitude(0)
            X.set_Li_repump_amplitude(0)   
            set_magnetic_field_A(X,S,0)
            X.wait_ms(50)
            X.mot_coil_enabled()
            X.wait_ms(50)   

    ## Load MOT    
    if S.bool_Li and S.bool_Rb:
        set_magnetic_field_A(X,S,S.Li6.mot_coil_gradient_load_A) #start dual with Li
        X.Rb_repump_mot_shutter_open()
    
    elif S.bool_Rb:
        set_magnetic_field_A(X,S,S.Rb.mot_coil_gradient_load_A)
        if S.bool_zeeman_slower:  
            X.Zeeman_Slower_shutter_open()   
            X.set_zeeman_coil_I([1,2,3,4,5,6,7,8],[S.Rb85.zeeman_coil_1_I,S.Rb85.zeeman_coil_2_I,S.Rb85.zeeman_coil_3_I,S.Rb85.zeeman_coil_4_I,S.Rb85.zeeman_coil_5_I,S.Rb85.zeeman_coil_6_I,S.Rb85.zeeman_coil_7_I,S.Rb85.zeeman_coil_8_I])
            X.set_Rb85_zeeman_slower_dF(S.Rb.slowing_beam_dF)
            X.set_Rb85_zeeman_slower_amplitude(S.Rb.slowing_beam_ampl)
            X.wait_ms(10)

    elif S.bool_Li:
        X.Rb_repump_off() 
        X.Rb_pumpAOM_off()
        set_magnetic_field_A(X,S,S.Li6.mot_coil_gradient_load_A) 
        if S.bool_zeeman_slower:   
            X.Zeeman_Slower_shutter_open()   
            X.set_zeeman_coil_I([1,2,3,4,5,6,7,8],[S.Li6.zeeman_coil_1_I,S.Li6.zeeman_coil_2_I,S.Li6.zeeman_coil_3_I,S.Li6.zeeman_coil_4_I,S.Li6.zeeman_coil_5_I,S.Li6.zeeman_coil_6_I,S.Li6.zeeman_coil_7_I,S.Li6.zeeman_coil_8_I])
            X.set_Li_zeeman_Slower_F(S.Li6.slowing_beam_AOM_frequency)
            X.set_Li_zeeman_slower_amplitude(S.Li6.slowing_beam_AOM_amplitude)
            X.wait_ms(10)
    
    X.util_trig_high()
    load_atoms(X,S) # this loads the MOT
    X.util_trig_low()
    
    if S.bool_additional_load_time: #adds additional load time without dumping the MOT, on top of the time necessary for calculations
        X.wait_s(S.add_load_time_s) 

    #X.set_supply_max_current(S.max_fb_coil_supply_current) #remove this
    if  S.bool_Rb and S.Rb_pump_detuning_change:
        Rb_pump_detuning_change(X,S)
    if  S.bool_Rb and S.bool_mot_oscillation:
        mot_oscillation(X,S)
    if  S.bool_Rb and S.bool_cool_mot and (not S.bool_absorption_imaging or S.bool_Li or S.bool_tweezer_load):    #cool mot
        cool_mot(X,S)
        # print '################## in IF COOL STATEMENT #############'
        # set_Rb_cool(X,S)
        X.wait_ms(S.cool_Rb_mot_ms)
    if S.bool_Rb and  S.bool_move_Rb_mot:# and (not S.bool_absorption_imaging or S.bool_Li):
        # print '################## in MOVE RB MOT ###################'
        move_Rb_mot(X,S)
        X.wait_ms(S.Rb85.moved_Rb_mot_reload_ms)
    if S.bool_Rb and S.bool_molasses_cooling:
        molasses_cooling(X,S)
    if S.bool_Rb and S.Rb_MOT_stark_shift_detection and not (S.bool_load_Rb_MOT_in_EField): 
        # print '------------------------------------------------------'
        rb_mot_stark_shift_detection(X,S)
    if S.bool_load_rb_magnetic_trap:
        load_rb_magnetic_trap(X,S)
        if S.bool_Rb_magnetic_trap_ss_ramp:
            Rb_magnetic_trap_ss_ramp(X,S)
            X.wait_s(S.hold_rb_magnetic_trap_s-(S.Rb_magnetic_trap_ss_ramp_wait_ms+S.Rb_magnetic_trap_ss_time_ms)/1000.0)
        else:
            X.wait_s(S.hold_rb_magnetic_trap_s)
        
    if  (S.bool_Li and S.bool_cool_mot) and not S.bool_tweezer_load:    #cool mot
        set_Li_compress(X,S)
        X.wait_ms(S.Li_mot_compress_ms)
        X.util_trig_low()
        X.util_trig_high()
        X.util_trig_low()
    
    if S.bool_electric_field_during_Li_MOT_load:
        ###X.util_trig_high()
        X.set_hv_relay_polarity(S.hv_field_polarity) 
        X.wait_ms(50)
        #X.util_trig_low()
        # X.hv_voltage_control_on()
        X.set_high_voltage_kV(S.high_voltage_Li_MOT_kV)
        X.wait_ms(S.electric_field_turnon_delay_time_ms)
        X.wait_ms(S.electric_field_during_Li_MOT_load_wait_ms)
    
    #########################
    ## Rb Only Dipole Trap ##
    #########################
    
    if  S.bool_Rb and S.bool_tweezer_load and not (S.bool_tweezer_load_Rb_on_Li or S.bool_dual_SPIxfer):
        load_tweezer(X,S,enabled=True)
        # print '################# done loading Rb at',X.get_time()
        if (S.bool_SPIPG_transfer and S.bool_SPIPG) and not S.bool_Li:
            # ##X.util_trig_high()
            X.wait_ms(10)
            IPG_turnon_ramp(X,S)
            evaporative_cooling_SPI(X,S,S.power_cooling_SPI)
            # #X.util_trig_low()
        
            
        
        ## Things to do with atoms while in tweezer (for Rb)
        if S.bool_tweezer_molasses_cooling and S.bool_coil_turnoff:
            tweezer_molasses_cooling(X,S)
        if S.bool_forced_depump_Rb:
            forced_depump_Rb(X,S)
        if S.bool_Rb_out:
            Rb_res_out(X,S)
        if S.bool_PA_light:
            apply_PA_light(X,S,enabled=True)
        if S.bool_depump_along_xy:
            depump_along_xy(X,S)
        if S.bool_flash_ipg_off_on:
            ipg_flash_off_on(X,S)
            
        if S.bool_RB_D_line_meas:  
            # Insert PA Commands to check Abs. Accuaracy of Comb
            feshbach_field_disable(X,S)
            X.set_comp_coils_V(0,0,0)
            X.set_TiS_AOM_F(60)
            # X.set_tisapph_external_control_voltage(S.PA.scan_low_bound)
            X.MC_HP_8663A.set_ren(mode=1)
            X.MC_HP_8663A.set_freq(value=S.HP_freq_synth_freq)
            X.wait_ms(200)
            X.MOL_TiSapph_srs_shutter_open()
            X.wait_ms(5)
            
            for nn in range(300):
                pass
                X.set_IPG_AOM_driver_input_amplitude(0)
                X.wait_us(2)
                X.set_TiS_AOM_amplitude(0.1)
                # X.wait_us(.1)
                X.set_TiS_AOM_amplitude(0)
                X.wait_us(2)
                X.set_IPG_AOM_driver_input_amplitude(S.IPG_power_set)
                X.wait_us(5)
            
            X.MOL_TiSapph_srs_shutter_closed()
            X.wait_ms(5)

        # Electric Field turn on here so that the field will be on before optical pumping
        if S.bool_apply_electic_field and not S.bool_Li:
            turn_on_electic_field(X,S)
        if S.bool_optically_pump_Rb and not S.bool_Li:
            optically_pumping_Rb(X,S)
            # X.Rb_repump_AOM_shutter_closed()                                          
        if S.bool_hyperfine_pump_Rb and not S.bool_Li:
            hyperfine_pumping_Rb(X,S)
        if S.bool_raman_stage:
            raman_stage(X,S)
        if S.bool_drsc_loop:
            for nn in range(S.drsc_cycles):
                drsc_cycle_sequence(X,S)
        if S.bool_drsc_stage:
            drsc_stage(X,S)
            
        if S.bool_electric_field_Rb_ODT and not (S.bool_electric_field_Rb_MOT):
            pass
            #X.hv_relay_on()
            # X.wait_ms(100)
            #X.hv_voltage_control_on()
            # X.wait_ms(1250)
        
        if S.bool_spin_cleanup_with_Bield:
            spin_cleanup(X,S)
            
        # # After everything we want to do with the E field, turn it off

        if S.bool_feshbach_Rb_tweezer_only and not S.bool_Li:
            if S.bool_depump_off_before_FB_field:
                # turns off depump (repump already shuttered)
                X.main_optical_pump_srs_shutter_closed()
                # X.Li_slowing_beam_shutter_closed()      # replaced by SRS shutter
                X.optical_depump_srs_shutter_closed()
                # X.Rb_optical_pump_off()
            feshbach_field_enable_Gauss(X,S,S.feshbach_field_Rb_only_G)
            
        if S.bool_evaporative_cooling_SPI and (S.bool_SPI or S.bool_SPIPG) and not (S.bool_Li or S.bool_SPIPG_transfer):
            evaporative_cooling_SPI(X,S,S.power_cooling_SPI,S.ramp_duration_cooling_SPI_ms,S.SPI_power_set)
            
        if S.bool_mw_transfer and not S.bool_Li:
            # ##X.util_trig_high()
            mw_transfer(X,S)
            # #X.util_trig_low()
        if S.bool_feshbach_Rb_tweezer_only and not S.bool_Li:
            X.wait_ms(S.hold_time_feshbach_field_ms)
            # turn of main pump shutter after feshbach field
            if S.bool_depump_off_after_FB_field:
                X.main_optical_pump_srs_shutter_closed()
                # X.Rb_optical_pump_off()
            feshbach_field_disable(X,S)
        
        if S.bool_feshbach_Rb_tweezer_only_2 and not S.bool_Li:
            feshbach_field_enable_Gauss(X,S,S.feshbach_field_Rb_only_G_2)
            X.wait_ms(S.hold_time_feshbach_field_ms_2)
            feshbach_field_disable(X,S)
            
        if S.bool_cycle_fb_coil_supply_output_during_trapping:
            coil_supply_cycle(X,S)
            
        if S.bool_high_antihelmoltz_field_during_trapping:
            # print '############### AH RESET IN TRAP ACTIVE ################'
            high_anithelmoltz_field(X,S)
            
        # if S.bool_mw_transfer and not S.bool_Li:
            # mw_transfer(X,S)
      
        if S.bool_state_cleanup_cycle and not S.bool_Li:
            state_cleanup_cycle(X,S)
            
        if S.bool_IPG_mod and S.bool_IPG:
            ipg_mod(X,S)
        if S.bool_SPI_mod and S.bool_SPI:
            spi_mod(X,S)
        if S.bool_evaporative_cooling_IPG and S.bool_IPG:# or S.bool_SPIPG):# and not S.bool_Li:
            evaporative_cooling_IPG(X,S)
        if S.bool_ramp_IPG and S.bool_IPG:
            pass
            #ramp_IPG(X,S)
        if S.bool_evaporate_into_IPG_cross:
            # Uses a linear ramp to evaporate the first arm, while turning on the second arm.
            # ##X.util_trig_high()
            #X.set_supply_max_current(S.max_into_cross_evap_I)
            feshbach_field_enable_Gauss(X,S,S.max_gauss_into_cross_evap_G)
            X.wait_ms(S.evap_into_cross_wait_ms)
            IPG_evaporate_into_cross(X,S,S.IPG_first_arm_first_evap_into_cross_start_power_W,S.IPG_first_arm_evap_into_cross_power_end_W,0,S.IPG_second_arm_evap_into_cross_power_end_W,S.IPG_evap_into_cross_duration_ms)                
            X.wait_ms(S.wait_after_evap_into_cross_with_field_on_ms)
            # #X.util_trig_low()                
            # if S.bool_cross_IPG_exp_evap:
                #print '!!!!!!!!!!!###############!!!!!!!!!!!!!!!!################!!!!!!!!!!!!!!!!'
                #Evaporates both arms following an exponentional ramp
                # IPG_cross_evap(X,S,S.IPG_first_arm_evap_into_cross_power_end_W ,S.IPG_first_arm_cross_evap_ramp_stop_power,S.IPG_second_arm_evap_into_cross_power_end_W,S.IPG_second_arm_cross_evap_ramp_stop_power,S.IPG_cross_exp_ramp_duration_ms,S.cross_tau_ms)
        

        if S.bool_cross_IPG_exp_evap:
            if S.bool_FB_Rb_cross_IPG_evap:
                #X.set_supply_max_current(S.max_FB_Rb_cross_IPG_evap_current)
                feshbach_field_enable_Gauss(X,S,S.max_gauss_into_cross_evap_G)
                #print '!!!!!!!!!!!###############!!!!!!!!!!!!!!!!################!!!!!!!!!!!!!!!!'
                # Evaporates both arms following an exponentional ramp
                IPG_cross_evap(X,S,S.IPG_first_arm_evap_into_cross_power_end_W ,S.IPG_first_arm_cross_evap_ramp_stop_power,S.IPG_second_arm_evap_into_cross_power_end_W,S.IPG_second_arm_cross_evap_ramp_stop_power,S.IPG_cross_exp_ramp_duration_ms,S.cross_tau_ms)
                X.wait_ms(S.hold_time_after_FB_Rb_cross_IPG_evap_ms)
                feshbach_field_disable(X,S)
            else:
                IPG_cross_evap(X,S,S.IPG_first_arm_evap_into_cross_power_end_W ,S.IPG_first_arm_cross_evap_ramp_stop_power,S.IPG_second_arm_evap_into_cross_power_end_W,S.IPG_second_arm_cross_evap_ramp_stop_power,S.IPG_cross_exp_ramp_duration_ms,S.cross_tau_ms)
               
            
        ### Rb Ti Sapph 
        if S.bool_scan_TiSapph:
            #print '!!!! IN TISAPPH SCAN !!!'
            # #X.util_trig_high()
            X.set_tisapph_external_control_voltage(S.PA.scan_low_bound)
            X.wait_ms(50)
            X.MOL_TiSapph_srs_shutter_open()
            X.wait_ms(5)
            if S.bool_modulate_ipg_off_and_on:
                modulate_ipg_off_on(X,S,S.freq_IPG_off_on_modulation_kHz,S.duration_IPG_off_on_modulation_ms)
            else:
                #X.wait_ms(S.PA.scan_duration_ms)
                X.ramp_Ti_Sapph(S.PA.scan_duration_ms,S.PA.scan_low_bound,S.PA.scan_upper_bound,dt=S.PA.scan_dt_ms)
                X.set_tisapph_external_control_voltage(S.PA.scan_upper_bound)
            X.MOL_TiSapph_srs_shutter_closed()
            X.wait_ms(5)
            X.util_trig_low()
            
       
       ## Hold atoms in tweezer for specified time
        if not S.bool_Li:
                X.wait_ms(S.hold_ms)
        
    ###########################
    ## Li Only Magnetic Trap ##
    ###########################  
    
    if S.bool_Li and S.Li6.bool_Li_Magnetic_Trap:
        load_magnetic_trap_Li(X,S)
  
    #########################
    ## Li Only Dipole Trap ##
    #########################  

    if S.bool_Li and S.bool_tweezer_load:   
        
        S.bool_SPI_orig = S.bool_SPI
        S.bool_IPG_orig = S.bool_IPG

        if S.bool_electric_field_on_before_ODT_load:
            X.set_hv_relay_polarity(0) 
            X.wait_ms(50)
            # X.hv_voltage_control_on()
            X.set_high_voltage_kV(S.high_voltage_initial_set_kV)
            X.wait_ms(S.electric_field_turnon_delay_time_ms)
            X.wait_s(S.efield_on_before_Li_load)
        
        #X.util_trig_high()        
        load_tweezer_Li(X,S,bool_pump_lower = True, enabled=True)   # B Field changes inside this command
        # at end of loading, the field is disabled. 
        # putting the switch to hemholtz here seems to cause a lot of trouble... why??
        
        # print '################# done loading Li tweezer at',X.get_time()
        
        ###############
        ## Li In SPI ##
        ###############
        
        # Assumption here is that any field we turn on will be a hemholtz field configuration.
        # if not, we need to make the change back to AH in the code.
        #X.util_trig_high()
        
        set_field_config_hemholtz(X,S)   # *** we need to change back to helmholtz, for now, we are using a MT to test recpature... 
        X.util_trig_low()
        
        # Free evaporation
        if S.bool_feshbach_in_tweezer and (not S.bool_Li_mw_transfer):
            # If not using high field imaging, the FB field is turned off after other things could happen in the trap
            # #X.#set_gradient_coils_I(S.set_gradient_coil_current) 
            set_magnetic_field_G(X,S,S.feshbach_Li_in_SPI_G)
            X.wait_ms(S.hold_time_feshbach_field_ms)
                
        # Evaporate quickly down from the high loading power
        if S.bool_high_power_evap_SPI:
            if not S.bool_feshbach_in_tweezer:
                set_magnetic_field_G(X,S,S.feshbach_Li_evap_G)
            X.wait_ms(S.SPI_high_power_evap_wait)
            #X.util_trig_high()
            evaporative_cooling_SPI(X,S,S.SPI_high_power_evap_stop,S.high_power_evap_ramp_duration_ms,S.SPI_power_set)
            X.util_trig_low()
            
        # Evaporate in the SPI following an exp. ramp
        if S.bool_evaporative_cooling_SPI_exp:
            if not (S.bool_feshbach_in_tweezer or S.bool_high_power_evap_SPI):
                set_magnetic_field_G(X,S,S.feshbach_Li_evap_G)
            ramp_SPI_exp(X,S,S.SPI_power_start_W,S.SPI_exp_stop_power_W,S.exp_ramp_duration_SPI_ms)
                
        # Evaporate in the SPI following a linear ramp
        if S.bool_evaporative_cooling_SPI:
            if not (S.bool_feshbach_in_tweezer or S.bool_high_power_evap_SPI or S.bool_evaporative_cooling_SPI_exp):
                set_magnetic_field_G(X,S,S.feshbach_Li_evap_G)
            
            # Perform Initial Evap Ramp
            if S.bool_high_power_evap_SPI:
                evaporative_cooling_SPI(X,S,S.SPI_evaporation_Li_stop_W_1st,S.ramp_duration_cooling_SPI_ms,S.SPI_high_power_evap_stop)
            else:
                evaporative_cooling_SPI(X,S,S.SPI_evaporation_Li_stop_W_1st,S.ramp_duration_cooling_SPI_ms,S.SPI_power_set)
            
            # Perfrom second Evap Ramp if required (and if only is second stop power is lower then the first)
            if  S.bool_second_evaporative_cooling_SPI and (S.SPI_evaporation_Li_stop_W_1st>S.SPI_evaporation_Li_stop_W_2nd):           
                evaporative_cooling_SPI(X,S,S.SPI_evaporation_Li_stop_W_2nd,S.second_ramp_duration_cooling_SPI_ms,S.SPI_evaporation_Li_stop_W_1st)
        
        # TEMP TO LOOK AT HEATING RATE
        # set_magnetic_field_G(X,S,534.0)
        # X.wait_ms(S.temp_wait_time_ms)

        # If FB field not needed later, turn it off now
        if (S.bool_feshbach_in_tweezer or S.bool_high_power_evap_SPI or S.bool_evaporative_cooling_SPI_exp or S.bool_evaporative_cooling_SPI) and not (S.bool_SPIPG_transfer or S.bool_SPIPG or S.bool_high_field_imaging):
                X.wait_ms(S.SPI_evap_wait_before_field_off)
                feshbach_field_disable(X,S)
                ##X.#set_gradient_coils_I(0) 
                        
        # Ramp SPI back up to higher value
        if S.bool_ramp_SPI_up:
            evaporative_cooling_SPI(X,S,S.SPI_Li_ramp_up_to_W,S.ramp_up_duration_SPI_ms,S.SPI_exp_stop_power_W)
        
        if S.bool_PA_in_SPI and (not S.bool_SPIPG_transfer):
            if S.bool_PA_Bfield_change:
            #X.set_supply_max_current(S.max_fb_coil_PA_search)
            # feshbach_field_disable(X,S)
            # X.wait_s(4)
                if S.PA_gauss==0:
                    print 'FIELD IS DISABLED'
                    X.set_mot_coil_I(0)
                    X.mot_coil_disabled()
                    X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)
                else:
                    feshbach_field_enable_Gauss(X,S,S.PA_gauss)
                    X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)   
            ## Li Ti Sapph  (added by Magnus Haw 2012/03/13)
            if S.bool_scan_TiSapph:
                # print '!!!! IN TISAPPH SCAN !!!'
                # #X.util_trig_high()
                X.set_tisapph_external_control_voltage(S.PA.scan_low_bound)
                X.wait_ms(50)
                X.MOL_TiSapph_srs_shutter_open()
                X.wait_ms(5)
                if S.bool_modulate_ipg_off_and_on:
                    modulate_ipg_off_on(X,S,S.freq_IPG_off_on_modulation_kHz,S.duration_IPG_off_on_modulation_ms)
                if S.bool_scan_multiple_freq:
                    for nn in range(S.number_of_freq):
                        next_v = S.PA.scan_low_bound+S.step_size_V*nn
                        # print next_v
                        X.set_tisapph_external_control_voltage(next_v)
                        X.wait_ms(S.PA.scan_duration_ms)
                else:
                    X.wait_ms(S.PA.scan_duration_ms)
                X.MOL_TiSapph_srs_shutter_closed()
                X.wait_ms(5)
                X.util_trig_low()
                
        #############################################
        ## Transfer Li into the IPG (if requested) ##
        #############################################
        
        # Transfer Li atoms from the SPI into the IPG
        if (S.bool_SPIPG_transfer): 
            print '***** IN TRANSFER FROM SPI TO IPG *****'
            # Turn on FB field to help evaporation. IPG Shutter is already open
            set_magnetic_field_G(X,S,S.feshbach_Li_SPIPG_xfer_G)

            # If IPG has not already been turned on, turn it on.
            if not S.bool_load_SPI_and_IPG:
                IPG_turnon_ramp(X,S)    
            # Evaporate in the SPI - This is a linear ramp down to the set value, in set time
            if S.bool_evaporative_cooling_SPI and not S.bool_second_evaporative_cooling_SPI:
                # print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
                evaporative_cooling_SPI(X,S,0,S.ramp_duration_transfer_SPI_ms,S.SPI_evaporation_Li_stop_W_1st)
            if S.bool_evaporative_cooling_SPI and S.bool_second_evaporative_cooling_SPI:
                # print '#############################################'
                evaporative_cooling_SPI(X,S,0,S.ramp_duration_transfer_SPI_ms,S.SPI_evaporation_Li_stop_W_2nd)
            else:
                # print '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
                evaporative_cooling_SPI(X,S,0,S.ramp_duration_transfer_SPI_ms,S.SPI_power_at_transfer)
            
            # Ensure SPI is OFF after transfer
            X.spi_control(0,0)
            X.wait_ms(S.wait_after_transfer_ms)
            # If a Rb MOT will be loaded after the transfer, turn off Feshbach field
            if S.bool_IPG_into_cross_evap_before_Rb_load:
                # Uses an exponential ramp to evaporate the first arm, while turning on the second arm.
                # This lowers the trap depth of the IPG before we load  Rb MOT and transfer it into the ODT...
                ##X.util_trig_high()
                X.wait_ms(S.evap_into_cross_wait_bef_Rb_ms) 
                ##exponential evaporation into cross
                IPG_cross_evap(X,S,S.IPG_Li_load,S.IPG_first_arm_cross_evap_ramp_stop_power_bef_Rb,S.IPG_second_arm_evap_into_cross_power_start_W_bef_Rb,S.IPG_second_arm_cross_evap_ramp_stop_power_bef_Rb,S.IPG_cross_exp_ramp_duration_bef_Rb_ms,S.cross_tau_bef_Rb_ms)
                #IPG_evaporate_into_cross(X,S,S.IPG_first_arm_first_evap_into_cross_start_power_W,S.IPG_first_arm_evap_into_cross_power_end_W,0,S.IPG_second_arm_evap_into_cross_power_end_W,S.IPG_evap_into_cross_duration_ms)
                X.wait_ms(S.wait_after_evap_into_cross_with_field_on_bef_Rb_ms)
                #X.util_trig_low()                     
            
            # Turn off the B field if we need to load a Rb MOT next...
            if S.bool_tweezer_load_Rb_on_Li:
                feshbach_field_disable(X,S) 
                

        
        ## Load RB MOT and then transfer to Dipole Trap
        ###############################################
        
        # Load Rb MOT and then transfer into dipole trap while Li is held in ODT
        if S.bool_tweezer_load_Rb_on_Li:
            
            # print '!!!!!!!!!!!!!!!!!!!!!!! Loading Rb MOT on top of Li ODT !!!!!!!!!!!!!!!!!!!!!!!'
            if not S.bool_SPIPG_transfer:
                feshbach_field_disable(X,S) 
            
            # high_anithelmoltz_field(X,S)
            # X.wait_ms(50)
            
            # #X.util_trig_low()
        
            # if S.bool_AH_dual_reset:
                # high_anithelmoltz_field(X,S)
                ####might have to remove it###
            if S.bool_evaporate_after_dual_feshbach and not S.bool_LiRb_plain_evap:
                X.set_supply_max_current(S.max_fb_coil_supply_current_LiRb_feshbach)
            if S.bool_LiRb_plain_evap:
                X.set_supply_max_current(S.max_fb_coil_supply_current_LiRb_plain_evap)
                
            # else:
                # X.set_supply_max_current(S.max_fb_coil_supply_current_fb_search)
            # X.set_supply_max_current(S.Rb.mot_coil_gradient_load_A)   
            
            X.set_mot_coil_I(S.Rb.mot_coil_gradient_load_A)
            
            # ##X.util_trig_high()
            
            set_Rb_load(X,S)   # set detunings for MOT loading
            start_Rb_load(X,S) # turn on AOMs and open shutters
                

            X.wait_s(S.Rb.loadmot_s)
                # X.set_supply_max_current(S.Rb.coil_cool_I)
                # X.wait_ms(100)
            # if S.bool_mot_cooling_stage:
                # mot_cooling_stage(X,S)
            #X.LiRb_mot_shutter_off()
            # Load in to Dipole Trap
            # ##X.util_trig_high()
            
            set_Rb_cool(X,S)                  # Set detunings and powers for ODT loading.
            finish_Rb_tweezer_load(X,S)       # Since trap already on, just pump to the correct state. 
            
            # #now both should be in IPG with field off
            #X.wait_ms(S.tweezer_load_ms)
            #X.Rb_repump_off()
            #X.Rb_pumpAOM_off()
            # if S.bool_evaporate_after_dual_feshbach and not S.bool_LiRb_plain_evap:
                # X.set_supply_max_current(S.max_fb_coil_supply_current_LiRb_feshbach)
            # if S.bool_LiRb_plain_evap:
                # X.set_supply_max_current(S.max_fb_coil_supply_current_LiRb_plain_evap)
            

            X.set_mot_coil_I(0)
            
            ## Things to do with both Li and Rb in ODT
            ##########################################
            if S.bool_forced_depump_Rb:
                forced_depump_Rb(X,S)
            if S.bool_optically_pump_Rb:
                # #X.util_trig_high()
                optically_pumping_Rb(X,S)
                # X.util_trig_low()
            if S.bool_spin_cleanup_with_Bield:
                spin_cleanup(X,S)
            if S.bool_mw_transfer:
                mw_transfer(X,S)
            if S.bool_feshbach_in_dual_tweezer:
                feshbach_field_enable_Gauss(X,S,S.feshbach_in_tweezer_dual_G) 
            if S.bool_ramp_dual_IPG:
                pass
            if S.bool_flash_ipg_off_on:
                ipg_flash_off_on(X,S)
                
            if S.bool_LiRb_plain_evap:
                # #X.util_trig_high()
                #Also try turning on Electric Field during this time
                if S.bool_LiRb_plain_evap_electric_field_turnon:
                    X.set_hv_relay_polarity(0) 
                    X.wait_ms(50)
                    # X.hv_voltage_control_on()
                    X.set_high_voltage_kV(S.high_voltage_final_set_kV)
                    if (S.electric_field_turnon_delay_time_ms > S.duration_LiRb_plain_evap_ms):
                        S.wait_ms(S.electric_field_turnon_delay_time_ms - S.duration_LiRb_plain_evap_ms)
                feshbach_field_enable_Gauss(X,S,S.LiRb_plain_evap_G) 
                X.wait_ms(S.duration_LiRb_plain_evap_ms)
                if S.bool_LiRb_FB_after_plain_evap:
                    X.set_supply_max_current(S.max_fb_coil_supply_current_field_change_after_IPG_evap)
                    X.wait_ms(S.FB_scan_after_plain_evap_ms)

        ##########################
        ## Evaporate in the IPG ##
        ##########################

        # Just makes sure an attempt has been made to get Li into IPG
        # Field is left on from the transfer...
        if S.bool_evaporative_cooling_IPG and (S.bool_SPIPG or S.bool_IPG or S.bool_SPIPG_transfer):
            set_magnetic_field_G(X,S,S.Li_IPG_evap_G)
            if not S.bool_recycled_IPG:
                # Linear ramp to create a cross
                if S.bool_evaporate_into_IPG_cross:
                    # Uses a linear ramp to evaporate the first arm, while turning on the second arm.
                    X.wait_ms(S.evap_into_cross_wait_ms) 
                    IPG_evaporate_into_cross(X,S,S.IPG_first_arm_first_evap_into_cross_start_power_W,S.IPG_first_arm_evap_into_cross_power_end_W,6.0,S.IPG_second_arm_evap_into_cross_power_end_W,S.IPG_evap_into_cross_duration_ms)
                    X.wait_ms(S.wait_after_evap_into_cross_with_field_on_ms)
                  
                #Evaporates both arms following an exponentional ramp    
                if S.bool_cross_IPG_exp_evap:
                    IPG_cross_evap(X,S,S.IPG_first_arm_evap_into_cross_power_end_W,S.IPG_first_arm_cross_evap_ramp_stop_power,S.IPG_second_arm_evap_into_cross_power_end_W,S.IPG_second_arm_cross_evap_ramp_stop_power,S.IPG_cross_exp_ramp_duration_ms,S.cross_tau_ms)  
                    X.wait_ms(S.wait_after_cross_evap_ms) 
            
            else:
                #X.util_trig_high()
                # #X.set_gradient_coils_I(5)  
                # ramp_IPG_linear(X,S,2.,.03,2000)
                # ramp_IPG_linear(X,S,2,0.7,1000)
                # ramp_IPG_linear(X,S,.7,.3,1000)
                # ramp_IPG_linear(X,S,.3,.1,1000)
                if S.bool_linear_IPG_ramp:
                    #X.#set_gradient_coils_I(S.gradient_coil_create_mol_I)
                    X.wait_ms(S.wait_linear_ramp_IPG_ms)
                    ramp_IPG_linear(X,S,S.IPG_power_start,S.IPG_power_stop,S.linear_ramp_duration_ms)
                    final_IPG_power = S.IPG_power_stop
                   
                if S.bool_exp_IPG_ramp:
                    ramp_IPG_exp(X,S,S.IPG_power_start_exp,S.IPG_end_exp_ramp_power,S.exp_ramp_duration_ms)
                    final_IPG_power = S.IPG_end_exp_ramp_power
                X.util_trig_low()
           
            if S.bool_gradient_evap:
                X.wait_ms(S.gradient_coil_evap_wait_ms)
                if S.bool_ramp:
                    # print 'in ramped gradient coil'
                    step_size_us = 100  # in us
                    num_steps = round((S.gradient_coil_evap_time_ms)/(step_size_us*10**-3))
                    step_size_I = S.gradient_coil_current_I/num_steps
                    for nn in range(num_steps):
                        #X.#set_gradient_coils_I(nn*step_size_I)
                        X.wait_us(step_size_us)
                else:
                    #X.#set_gradient_coils_I(S.gradient_coil_current_I)  
                    X.wait_ms(S.gradient_coil_evap_time_ms)
                #X.#set_gradient_coils_I(0) 
            #X.#set_gradient_coils_I(0) 
            # #X.set_gradient_coils_I(5) 
            # print 'fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff I DID IT'
        #########################
        ## Things to do in IPG ##
        #########################
        
        # X.util_trig_high()
        if S.bool_flash_IPG:
            set_magnetic_field_G(X,S,0)
            #X.set_gradient_coils_I(0) 
            X.wait_ms(100)
            modulate_ipg_off_on_Li(X,S,S.Li_flash_time_us,S.Li_duration_ms,final_IPG_power)
        # X.util_trig_low()   
        
        if S.bool_create_molecules:
            # X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)
            # X.wait_ms(10)
            # ramp_IPG_linear(X,S,S.IPG_power_start,2,250)
            # ramp_IPG_linear(X,S,2.,1,200)
            # set_magnetic_field_G(X,S,S.Li_molecule_field_G)
            # #X.set_gradient_coils_I(-1.3) 
            # ramp_IPG_linear(X,S,1,.5,200)
            # ramp_IPG_linear(X,S,0.5,0.2,300)
            # ramp_IPG_linear(X,S,0.2,.1,200)
            # ramp_IPG_linear(X,S,.1,.05,100)
            # ramp_IPG_linear(X,S,.05,.03,200)
            # ramp_IPG_linear(X,S,.03,.02,100)
            # ramp_IPG_linear(X,S,.02,.01,100)
            X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)
            X.wait_ms(10)
            if S.IPG_evap_stop_W >= 2 and S.IPG_evap_stop_W < 12:
                ramp_IPG_linear(X,S,S.IPG_power_start,S.IPG_evap_stop_W,(((12-S.IPG_evap_stop_W)/10.0)*250))
                print '====================================================='
                print (((12-S.IPG_evap_stop_W)/10.0)*250)
                print '====================================================='
            elif S.IPG_evap_stop_W < 2:
                ramp_IPG_linear(X,S,S.IPG_power_start,2,250)
            
            if S.IPG_evap_stop_W >= 1 and S.IPG_evap_stop_W < 2:
                #X.set_gradient_coils_I(S.gradient_coil_create_mol_I)
                ramp_IPG_linear(X,S,2,S.IPG_evap_stop_W,(((2-S.IPG_evap_stop_W)/1.0)*200))
            elif S.IPG_evap_stop_W < 1:
                #X.set_gradient_coils_I(S.gradient_coil_create_mol_I)
                ramp_IPG_linear(X,S,2.,1,200)
            
            # if S.IPG_evap_stop_W >= 3 and S.IPG_evap_stop_W < 12:
                # ramp_IPG_linear(X,S,S.IPG_power_start,S.IPG_evap_stop_W,(((12-S.IPG_evap_stop_W)/10.0)*250))
            # elif S.IPG_evap_stop_W < 3:
                # ramp_IPG_linear(X,S,S.IPG_power_start,3,250)
            
            # if S.IPG_evap_stop_W >= 1 and S.IPG_evap_stop_W < 3:
                # set_magnetic_field_G(X,S,S.Li_molecule_field_G)
                # #X.set_gradient_coils_I(S.gradient_coil_create_mol_I)#-1.3) 
                # ramp_IPG_linear(X,S,3,S.IPG_evap_stop_W,(((3-S.IPG_evap_stop_W)/1.0)*250))
            # elif S.IPG_evap_stop_W < 1:
                # set_magnetic_field_G(X,S,S.Li_molecule_field_G)
                # #X.set_gradient_coils_I(S.gradient_coil_create_mol_I)#-1.3) 
                # ramp_IPG_linear(X,S,3.,1,250)
            
            if S.IPG_evap_stop_W >= 0.5 and S.IPG_evap_stop_W < 1:
                set_magnetic_field_G(X,S,S.Li_molecule_field_G)
                #X.set_gradient_coils_I(S.gradient_coil_create_mol_I)#-1.3) 
                ramp_IPG_linear(X,S,1,S.IPG_evap_stop_W,(((1-S.IPG_evap_stop_W)/0.5)*200)) 
            elif S.IPG_evap_stop_W < 0.5:
                set_magnetic_field_G(X,S,S.Li_molecule_field_G)
                #X.set_gradient_coils_I(S.gradient_coil_create_mol_I)#-1.3)
                ramp_IPG_linear(X,S,1,.5,200)
            
            if S.IPG_evap_stop_W >= 0.2 and S.IPG_evap_stop_W < 0.5:
                ramp_IPG_linear(X,S,0.5,S.IPG_evap_stop_W,(((0.5-S.IPG_evap_stop_W)/0.3)*300))             
            elif S.IPG_evap_stop_W < 0.2:
                ramp_IPG_linear(X,S,0.5,0.2,300)
   
            if S.IPG_evap_stop_W >= 0.1 and S.IPG_evap_stop_W < 0.2:
                ramp_IPG_linear(X,S,0.2,S.IPG_evap_stop_W,(((.2-S.IPG_evap_stop_W)/0.1)*200))    
            elif S.IPG_evap_stop_W < 0.1:
                ramp_IPG_linear(X,S,0.2,.1,400)

            if S.IPG_evap_stop_W >= 0.05 and S.IPG_evap_stop_W < 0.1:
                ramp_IPG_linear(X,S,0.1,S.IPG_evap_stop_W,(((.1-S.IPG_evap_stop_W)/0.05)*100)) 
            elif S.IPG_evap_stop_W < 0.05:
                ramp_IPG_linear(X,S,.1,.05,300)
            
            if S.IPG_evap_stop_W < 0.05:
                ramp_IPG_linear(X,S,0.05,S.IPG_evap_stop_W,(((.05-S.IPG_evap_stop_W)/0.04)*400)) 

            X.wait_ms(S.Li_molecule_wait_ms)


        if S.bool_tweezer_load_Rb_on_Li and S.bool_IPG_cross_FB:
            X.wait_ms(S.FB_wait_ms)

        if S.bool_PA_Bfield_change: # we should probably add/have/check some global PA boolean also here
            if S.PA_gauss==0:
                print 'FIELD IS DISABLED'
                feshbach_field_disable(X,S)
                X.set_comp_coils_V(S.compx_PA,S.compy_PA,S.compz_PA)
            else:
                set_magnetic_field_G(X,S,S.PA_gauss)
                X.set_comp_coils_V(S.compx_PA,S.compy_PA,S.compz_PA)
            X.wait_ms(S.after_cross_evap_wait_ms) #Kirk says this looks fucked up.......please comment further



        if S.bool_modulation_after_IPG_ramp_up:        
            ramp_IPG_linear(X,S,S.IPG_evap_stop_W,S.freq_mod_IPG_ramp_up_power,1000)    
       
        if S.bool_Li_spin_cleanup:
            X.Li_HF_imaging_shutter_open()
            X.wait_ms(S.Li_HF_imaging_shutter_open_delay_ms)
            X.set_Li_imaging_F(S.Li_spin_cleanup_AOM_F)
            X.set_Li_imaging_amplitude(S.Li_spin_cleanup_AOM_amp)
            X.wait_ms(S.Li_spin_cleanup_wait_ms)
            X.set_Li_imaging_amplitude(0)
            X.set_Li_imaging_F(0)
            X.Li_HF_imaging_shutter_closed()
            X.wait_ms(S.Li_HF_imaging_shutter_close_delay_ms)

        if S.bool_Li_mw_transfer:
            Li_mw_transfer(X,S)

        if S.bool_IPG_mod:
            IPG_aom_square_mod(X,S)

        ## LI Photoassociation Coding START ##
        if S.bool_set_DS345_sinewave_parameters:
            # print '!!!!!!!!!!!!!!!!#@$@#$@#$@$@#$!!!!!!!!!!!!!!!!!!!!!#$@#$!'
            # X.util_trig_high()
            # X.set_DS345_AM_off_analog()
            # X.wait_ms(100)
            X.set_Sinewave_parameters(S.DS345_frequency, S.DS345_amplitude, S.DS345_offset, S.DS345_comAddress)
            X.set_DS345_AM_on()
            X.wait_ms(S.DS345_mod_time)
            X.set_DS345_AM_off()
            X.util_trig_low()
        # Li TiSapph locked to frequency comb  (added by Mariusz 2012/08/20)
        # This changes the rep rate of the comb, to scan the TS frequency.
        # Used for high resolution single color PA scans
        # 
        if S.bool_modulation_after_IPG_ramp_up:
            X.wait_ms(50)
            ramp_IPG_linear(X,S,S.freq_mod_IPG_ramp_up_power,S.IPG_evap_stop_W,10) 
        if S.bool_set_freq_comb and not S.bool_STIRAP:
            # print '!!!! IN FREQUENCY COMB !!!'
            # #X.util_trig_high()
            X.MOL_TiSapph_srs_shutter_open()
            X.wait_ms(5)
            # If single color PA, set frequency by changing rep rate
            # If 2color PA, we dont change the rep rate, so it does nothing
            if not S.bool_2color_PA: #if 2-color PA rep rate doesn't change
                X.MC_HP_8663A.set_ren(mode=1)
                X.MC_HP_8663A.set_freq(value=S.HP_freq_synth_freq)
                X.wait_ms(10)
                if not S.bool_PA_with_shutter_closed:
                    X.set_TS1_main_AOM_F(80)
                    X.set_TS2_main_AOM_F(80)
                    X.wait_ms(5)
                    #X.util_trig_high()
                    # Pulse Sequence
                    X.set_TS2_main_AOM_amplitude(S.TS2_main_AOM_amplitude)
                    X.set_TS1_main_AOM_amplitude(S.TS1_main_AOM_amplitude)
                # X.wait_ms(2000)
                X.wait_ms(S.PA.scan_duration_ms)
                X.set_TS1_main_AOM_amplitude(0)
                X.set_TS2_main_AOM_amplitude(0)
                X.MOL_TiSapph_srs_shutter_closed()
                # X.util_trig_low()
                
        # Li Ti Sapph  (added by Magnus Haw 2012/03/13)
        # This changes the external voltage top TS1 to scan its frequency when locked to its external cavity
        # This is used for low res single color or 2 color PA when scanning is NOT done with comb
        if S.bool_scan_TS1_cavity and not S.bool_STIRAP:
            # print '!!!! IN TISAPPH SCAN !!!'
            # #X.util_trig_high()
            X.set_tisapph_external_control_voltage(S.PA.TS1_voltage)
            X.wait_ms(50)
            if not S.bool_PA_with_shutter_closed:
                X.MOL_TiSapph_srs_shutter_open()
                X.set_TS1_main_AOM_amplitude(S.TS1_main_AOM_amplitude)
                X.set_TS1_main_AOM_F(80)
                X.set_TS2_main_AOM_amplitude(S.TS2_main_AOM_amplitude)
                X.set_TS2_main_AOM_F(80)
            X.wait_ms(5)
            if S.bool_modulate_ipg_off_and_on:
                modulate_ipg_off_on(X,S,S.freq_IPG_off_on_modulation_kHz,S.duration_IPG_off_on_modulation_ms)
            if S.bool_scan_multiple_freq:
                for nn in range(S.number_of_freq):
                    next_v = S.PA.scan_low_bound+S.step_size_V*nn
                    X.set_tisapph_external_control_voltage(next_v)
                    X.wait_ms(S.PA.scan_duration_ms)
            else:
                X.wait_ms(S.PA.scan_duration_ms)
            X.MOL_TiSapph_srs_shutter_closed()
            X.set_TS1_main_AOM_amplitude(0)
            X.set_TS2_main_AOM_amplitude(0)
            X.wait_ms(5)
            # X.util_trig_low()
        
        # This changes the frequency of the first TS using the AOM
        # NOTE THE FREQUENCY CHANGE IS DONE AT THE BEGINNING OF THE MASTER RECIPE
        if (S.bool_scan_TS1_aom or S.bool_single_color_fixed_PA) and not S.bool_STIRAP:
                # frequency is already set
                # X.util_trig_high()
                if not S.bool_PA_with_shutter_closed:
                    X.MOL_TiSapph_srs_shutter_open()
                    X.wait_ms(20) # to let shutter open
                    X.set_TS1_main_AOM_F(80)
                    X.set_TS2_main_AOM_F(80)
                    X.set_TS2_main_AOM_amplitude(S.TS2_main_AOM_amplitude)
                    X.set_TS1_main_AOM_amplitude(S.TS1_main_AOM_amplitude) 
                    
                      
                #X.wait_ms(5)
                X.wait_ms(S.PA.scan_duration_ms)
                
                
                # step = S.TS2_main_AOM_amplitude/1000.0
                # for nn in range(1000):
                    # X.set_TS2_main_AOM_amplitude(S.TS2_main_AOM_amplitude-step*nn)
                X.set_TS1_main_AOM_amplitude(0)
                X.set_TS2_main_AOM_amplitude(0)
                # X.set_TS1_main_AOM_amplitude(0)
                X.MOL_TiSapph_srs_shutter_closed()
                # X.set_comp_coils_V(0,0,0)
                X.wait_ms(20)
                # X.util_trig_low()
        ## LI Photoassociation Coding STOP


            
        #ramp_IPG_linear(X,S,.03,.05,300)        
        if S.bool_cross_IPG_adiabatic_ramp_up and not S.bool_recycled_IPG:
            # Ramps up both arms in a linear fashion to break molecules (we hope)
            #X.set_supply_max_current(S.max_fb_coil_supply_current)
            X.wait_ms(S.adiabatic_cross_IPG_ramp_up_wait_ms)
            if S.bool_cross_IPG_exp_evap:# and (S.IPG_dual_evap_stop_W<S.adiabatic_cross_IPG_ramp_up_stop):
                X.wait_ms(S.evap_into_cross_wait_ms)
                IPG_evaporate_into_cross(X,S,S.IPG_first_arm_cross_evap_ramp_stop_power,S.adiabatic_cross_IPG_first_arm_ramp_up_stop,S.IPG_second_arm_cross_evap_ramp_stop_power, S.adiabatic_cross_IPG_second_arm_ramp_up_stop, S.adiabatic_cross_IPG_ramp_up_duration_ms)
            else:
                X.wait_ms(S.evap_into_cross_wait_ms)
                IPG_evaporate_into_cross(X,S,S.bool_high_power_evap_SPI,S.adiabatic_cross_IPG_first_arm_ramp_up_stop,S.IPG_second_arm_evap_into_cross_power_end_W, S.adiabatic_cross_IPG_second_arm_ramp_up_stop, S.adiabatic_cross_IPG_ramp_up_duration_ms)

        # if not (S.bool_high_field_imaging or S.bool_adiabatic_IPG_ramp_up):
            # X.set_gradient_coils_I(0)
            # feshbach_field_disable(X,S)  
            
        # Adiabatic ramp up in the IPG
        if (S.bool_adiabatic_IPG_ramp_up and S.bool_evaporative_cooling_IPG):
            set_magnetic_field_G(X,S,S.mag_field_adiabatic_ramp_G)
            X.wait_ms(50)
            if S.bool_disable_field_before_ramp:
                #X.set_gradient_coils_I(0)
                feshbach_field_disable(X,S)
            X.wait_ms(S.adiabatic_IPG_ramp_up_wait)
            #ramps up the IPG power if the evaporation stops below the power we want to ramp up to#
            if (final_IPG_power<S.adiabatic_IPG_ramp_up_stop):
                ramp_IPG_linear(X,S,final_IPG_power,S.adiabatic_IPG_ramp_up_stop,S.adiabatic_IPG_ramp_up_duration_ms)
            #if the above is not fulfilled it waits for the time needed for evaporation doing nothing#
            else:
                X.wait_ms(S.adiabatic_IPG_ramp_up_duration_ms)
            if not S.bool_high_field_imaging:
                #X.set_gradient_coils_I(0)
                feshbach_field_disable(X,S)
    
    
    # X.wait_ms(S.hold_ms/2.0)
    # X.set_Li_repump_amplitude(1)
    # X.wait_ms(2000)
    # X.set_Li_repump_amplitude(0)
    # X.wait_ms(20)
    if S.bool_tweezer_load or S.bool_load_rb_magnetic_trap or S.Li6.bool_Li_Magnetic_Trap:
        X.wait_ms(S.hold_ms)
    


    ## Done with Science. Collect Data / Take Pictures!
    
    # Take Rb recapture image of MOT only if a Rb MOT was loaded (and no ODT)
    if (S.bool_Rb and S.Rb85.bool_pixelink_flourescence_imaging) and not (S.bool_Li or S.bool_tweezer_load_Rb_on_Li or S.bool_tweezer_load):
        #X.util_trig_high()
        take_image(X,S) 
        print 'Triggers Count: ', X.pixelink_triggers_count 
        #X.util_trig_low()

    if S.bool_high_field_imaging:
        #X.set_supply_max_current(S.max_high_field_imaging_current)
        # X.util_trig_high()
        # set_magnetic_field_G(X,S,S.Li_molecule_field_G)
        # X.wait_ms(50)
        # #X.set_gradient_coils_I(S.gradient_coil_hfield_imag_I)#-1.3)
        X.set_Li_imaging_amplitude(0)  
        X.set_Li_imaging_F(0)
        # set_field_config_hemholtz(X,S)
        # X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)
        X.set_comp_coils_V(0,0,0)
        set_magnetic_field_G(X,S,S.high_field_imaging_field_G) 
        X.wait_ms(50)

        #X.set_gradient_coils_I(S.gradient_coil_hfield_imag_I)
        # X.util_trig_low()
    
    if S.bool_tweezer_load and not S.bool_high_field_imaging:
        # X.set_IPG_power_DDS_control_W(10)
        X.wait_ms(10) #<------------------------------------ WTF is this doing here -- Kahan 2015/02/22
        #X.set_gradient_coils_I(0)
        # X.set_comp_coils_V(S.compx_offset,S.compy_offset,S.compz_offset)
        # feshbach_field_disable(X,S)  *** # 20151110 disable to get magnetic trap working with dipole trap settings
        
        # X.wait_us(50)        

    
    # Recapture atoms, and collect data from scope
    if (S.bool_load_rb_magnetic_trap and S.TekScope.bool_recapture_trace) and not S.bool_Li: 
        set_fluorescence_imaging(X,S)
        take_scope_recapture_trace(X,S)

    # Take RB Absorption Image IF only Rb with loaded into the dipole trap.
    if (S.bool_Rb and S.bool_absorption_imaging) and not (S.bool_Li or S.Rb_MOT_stark_shift_detection):
        # #X.util_trig_high()
        take_image(X,S)
        # X.util_trig_low()
    
    # Take RB Fluorescence image. if only Rb was used.
    if S.bool_Rb and S.bool_fluorescence_imaging and not (S.bool_Li or S.Rb_MOT_stark_shift_detection or S.Rb85.bool_pixelink_flourescence_imaging):
        set_fluorescence_imaging(X,S)
        take_image(X,S)
    
    # Check shutter timings on Apogee... [unsure]
    if S.bool_Rb and S.bool_apogee_check:
        set_fluorescence_imaging(X,S)
        X.set_mot_coil_I(0)
        apogee_shutter_check(X,S)
        
    # Check Pixelink timings... [unsure]    
    if S.bool_Rb and S.bool_pixelink_check:
        pixelink_check(X,S)
    
    # Take Rb Image with Apogee
    if S.bool_Rb and S.bool_take_apogee_image:
        take_apogee_image(X,S)
    
    # Take Li Image if ONLY Li was loaded into the ODT
    if (S.bool_Li and S.bool_absorption_imaging) and not (S.bool_Rb or S.bool_tweezer_load_Rb_on_Li):
        # X.util_trig_high()
        take_Li_image(X,S) 
        
        
    # Take Li recapture image of Li ONLY IF Li was loaded into the ODT
    if (S.bool_Li and S.Li6.bool_pixelink_flourescence_imaging) and not (S.bool_Rb or S.bool_tweezer_load_Rb_on_Li):
        take_Li_image(X,S)
    
    #***# ------------------------------------------------------- NOT SURE WHY THIS IS HERE??? -- 2015/11/25 -- Kahan
    # Take Li recapture image of Li ONLY IF Li was loaded into the ODT
    #if (S.bool_Rb and S.Rb.bool_pixelink_flourescence_imaging) and not (S.bool_Li or S.bool_tweezer_load_Rb_on_Li): 
    #    take_image(X,S)
    
    # Take picture of both atoms in dipole trap sequentially
    if S.bool_dual_image:
        # #X.util_trig_high()
        X.wait_ms(5)
        # X.util_trig_low()
        take_dual_image(X,S)
        # X.util_trig_low()
    
    # Take Picture of atoms in DUAL Dipole Trap (select which atom)
    if S.bool_Li and S.bool_tweezer_load_Rb_on_Li and S.bool_absorption_imaging and not S.bool_dual_image:
        if S.bool_Li_absorption_image:
            take_Li_image(X,S)
        if S.bool_Rb_absorption_image:
            # ##X.util_trig_high()
            take_image(X,S)
            # #X.util_trig_low()
    
    # Make sure Electroc field is turned off before allowing next run to start
    if (S.bool_electric_field_Rb_ODT or S.bool_load_Rb_MOT_in_EField or S.Rb_MOT_stark_shift_detection or S.bool_electric_field_during_Li_MOT_load or S.bool_LiRb_plain_evap_electric_field_turnon or S.bool_electric_field_on_before_ODT_load or S.bool_electric_field_on_with_Li_in_ODT) and not S.bool_EField_after_recipe_run_sequence_during_MOT_reload:
        # X.hv_voltage_control_off()
        X.set_high_voltage_kV(0)
        if (S.Rb_MOT_stark_shift_detection and S.bool_field_disabled):
            X.wait_s(1)                
        elif (S.Rb_MOT_stark_shift_detection or S.bool_electric_field_during_Li_MOT_load):
            X.wait_s(10)                # Make sure voltage is low (<10kV) before flipping relays
        else:
            X.wait_s(10)
        if S.bool_auto_flip_polarity:
            X.set_hv_relay_polarity(1) 
            X.wait_ms(50)
            # X.hv_voltage_control_on()
            X.set_high_voltage_kV(S.high_voltage_final_set_kV)
            X.wait_ms(2000)
            # X.hv_voltage_control_off()
            X.set_high_voltage_kV(0)
            X.wait_s(10)
        if not S.Rb_MOT_stark_shift_detection:
            X.set_hv_relay_polarity(0)                 # Turns off relays...
      
    if S.bool_Li  and S.bool_tweezer_load:
        S.bool_SPI = S.bool_SPI_orig 
        S.bool_IPG = S.bool_IPG_orig
    if S.bool_zeeman_slower:
        X.set_zeeman_coil_I([1,2,3,4,5,6,7,8],[0,0,0,0,0,0,0,0])
#######################################################################################
## Run Recipe Funcion called by the Settings object
#######################################################################################
def run_recipe(S):
    '''
    Main event script for one run of the recipe
    '''
    ###################################################################################
    ## initialize any variables or devices needed for the recipe
    ## or run out of recipe scripts (like reading oscilloscope or something
    ###################################################################################
    

    ###################################################################################
    ## START RECIPE --  and initialize any utbus or recipe values
    ###################################################################################
    #string is not important -- just id's bytecode file
    #sampling_frequency_divider = 5 gives 4MHz card clock 
    #       ==> .75us per command ==> bus speed > 1MHz
    X = Recipe('master_bytecode',sampling_frequency_divider = 5)  
    X.start()

    #X.labels.init('mylabel___%d')  #this is optional if you want to change default
    
    ###################################################################################
    ## run sequence loop
    ###################################################################################
    # set freq before run starts so TS is "ready"
    # wavemeter = S.wavemeter

    

    for i in range(S.N):
    
        X.atom_shutter_open()

        if S.TekScope.bool_read_out_tek_scope:
            X.util_trig_low()
        S.set_sequence_values(i)  
        # Make sure High Field Imagine Light is not leaking through
        # This stuff should really be in an init function
        # S.Li6.mot_coil_gradient_load_A  = S.Li6.coil_load_I
        #X.high_field_imaging_shutter_off()
        X.hv_voltage_control_off()      
        X.set_Li_imaging_amplitude(0)
        
        # X.set_TS1_main_AOM_amplitude(0)
        # X.set_TS1_main_AOM_F(80)
        # X.set_TS2_main_AOM_amplitude(0)
        # X.set_TS2_main_AOM_F(80)
         
        X.LiSS.set_amplitude(0) 
        X.set_LiSS_dF(0)
        
        X.set_IGP_AOM_RF_Level_on_analog()

            

        ##################################################
        sequence(X,S) ####################################
        ##################################################
        
        if S.bool_loaded_mot_flourescence_imaging:
            X.set_mot_coil_I(S.mot_coil_gradient_off_A)
            X.wait_ms(100)
            load_atoms(X,S,.01,label='motbackgnd_%i')
            if S.bool_Rb and S.bool_Li:
                X.set_mot_coil_I(S.mot_coil_gradient_dualLoad_A)
            elif S.bool_Rb:
                X.set_mot_coil_I(S.Rb.mot_coil_gradient_load_A)
            elif S.bool_Li and S.bool_leave_mot_on:
                set_Li_load(X,S)
                X.set_mot_coil_I(S.Li6.mot_coil_gradient_load_A)  #leave mot on
            else:
                set_Rb_load(X,S)
                set_Li_load(X,S)
                X.set_mot_coil_I(0)#leave mot off
        
        # this is important to keep the magnetic field zeroed (so we think).
        if S.bool_high_antihelmoltz_field_after_sequence:

            X.set_supply_max_current(30)
            X.wait_ms(50)
            high_anithelmoltz_field(X,S)
            X.set_supply_max_current(0)
        
        if S.bool_cycle_mot_coils_supply_output:
            coil_supply_cycle(X,S)
        
        X.wait_s(.5)
        
        #########################################
        ## Only applies to Electric Field runs ##
        #########################################
        if (S.bool_electric_field_Rb_ODT or S.bool_load_Rb_MOT_in_EField or S.bool_electric_field_on_with_Li_in_ODT or S.Rb_MOT_stark_shift_detection or S.bool_electric_field_during_Li_MOT_load or S.bool_LiRb_plain_evap_electric_field_turnon or S.bool_electric_field_on_before_ODT_load) and S.bool_EField_after_recipe_run_sequence_during_MOT_reload and i<max(range(S.N)):
            X.mot_coil_enabled()
            if S.bool_Li and S.bool_Rb:
                set_Li_load(X,S)
                set_Rb_load(X,S)
                X.set_mot_coil_I(S.mot_coil_gradient_dualLoad_A)  #leave mot on
            elif S.bool_Rb:
                set_Rb_load(X,S)
                X.set_mot_coil_I(S.Rb.mot_coil_gradient_load_A)  #leave mot on
            elif S.bool_Li and S.bool_leave_mot_on:
                set_Li_load(X,S)
                X.set_mot_coil_I(S.Li6.mot_coil_gradient_load_A)  #leave mot on
            else:
                set_Rb_load(X,S)
                set_Li_load(X,S)
                X.set_mot_coil_I(0)#leave mot off
            init_shutters(X,S)
            X.set_comp_coils_V(0,-5.5,0)
            #X.set_gradient_coils_I(0) 
            X.set_supply_max_current(S.Li6.mot_coil_gradient_load_A)
            # X.set_supply_max_current(30)    # return to default
            load_atoms(X,S,set_only=True,takeimage=False)
            # X.hv_voltage_control_off()
            X.set_high_voltage_kV(0)
            if (S.Rb_MOT_stark_shift_detection and S.bool_field_disabled):
                X.wait_s(1)                
            else:
                X.wait_s(10)                # Make sure voltage is low (<10kV) before flipping relays
            if S.bool_auto_flip_polarity:
                X.set_hv_relay_polarity(1) 
                X.wait_ms(50)
                # X.hv_voltage_control_on()
                X.set_high_voltage_kV(S.high_voltage_final_set_kV)
                X.wait_ms(2000)
                # X.hv_voltage_control_off()
                X.set_high_voltage_kV(0)
                X.wait_s(10)
            X.set_hv_relay_polarity(0)                 # Turns off relays...
        
      
    ###################################################################################
    ## any post sequence UTbus stuff like leaving the MOT on
    ###################################################################################
    
    set_field_config_antihemholtz(X,S)
    if S.bool_Li and S.bool_Rb:
        set_Li_load(X,S)
        set_Rb_load(X,S)
        set_magnetic_field_A(X,S,S.mot_coil_gradient_dualLoad_A)  #leave mot on
    elif S.bool_Rb:
        set_Rb_load(X,S)
        set_magnetic_field_A(X,S,S.Rb.mot_coil_gradient_load_A)  #leave mot on
    elif S.bool_Li:
        set_Li_load(X,S)
        set_magnetic_field_A(X,S,S.Li6.mot_coil_gradient_load_A)  #leave mot on
        if S.bool_zeeman_slower:
            X.set_Li_zeeman_Slower_F(S.Li6.slowing_beam_AOM_frequency)
            X.set_Li_zeeman_slower_amplitude(S.Li6.slowing_beam_AOM_amplitude)
    else:
        set_Rb_load(X,S)
        set_Li_load(X,S)
        set_magnetic_field_A(X,S,0)
    init_shutters(X,S)
    
    X.set_Li_imaging_amplitude(0)
    # #X.set_gradient_coils_I(0)


    if S.bool_dump_mot_at_start:
        X.atom_shutter_close()
    else:
        X.atom_shutter_open()
        X.set_zeeman_coil_I([1,2,3,4,5,6,7,8],[S.Li6.zeeman_coil_1_I,S.Li6.zeeman_coil_2_I,S.Li6.zeeman_coil_3_I,S.Li6.zeeman_coil_4_I,S.Li6.zeeman_coil_5_I,S.Li6.zeeman_coil_6_I,S.Li6.zeeman_coil_7_I,S.Li6.zeeman_coil_8_I])
        X.set_Li_zeeman_slower_amplitude(S.Li6.slowing_beam_AOM_amplitude)
        X.set_Li_zeeman_Slower_F(S.Li6.slowing_beam_AOM_frequency) 
    load_atoms(X,S,set_only=True,takeimage=False)
    
    if (S.bool_electric_field_Rb_ODT or S.bool_load_Rb_MOT_in_EField or S.Rb_MOT_stark_shift_detection or S.bool_electric_field_on_with_Li_in_ODT or S.bool_electric_field_during_Li_MOT_load or S.bool_LiRb_plain_evap_electric_field_turnon or S.bool_electric_field_on_before_ODT_load) and S.bool_EField_after_recipe_run_sequence_during_MOT_reload:
        # X.hv_voltage_control_off()
        X.set_high_voltage_kV(0)
        if (S.Rb_MOT_stark_shift_detection and S.bool_field_disabled):
            X.wait_s(1)                
        else:
            X.wait_s(10)                # Make sure voltage is low (<10kV) before flipping relays
        if S.bool_auto_flip_polarity:
            X.set_hv_relay_polarity(1) 
            X.wait_ms(50)
            # X.hv_voltage_control_on()
            X.set_high_voltage_kV(S.high_voltage_final_set_kV)
            X.wait_ms(2000)
            # X.hv_voltage_control_off()
            X.set_high_voltage_kV(0)
            X.wait_s(10)
        X.set_hv_relay_polarity(0)                 # Turns off relays...

    ###################################################################################
    ## initialize cameras with proper number of images from trigger counts
    ## note the recipe doesn't start running until X.end() so we can do this
    ###################################################################################
    
    if S.TekScope.bool_read_out_tek_scope:
        S.TekScope.start()
        S.TekScope.auto_set_hor_scale(S.Rb.loadmot_s,S.bool_load_rb_magnetic_trap,S.hold_rb_magnetic_trap_s)
        S.TekScope.reset_single_seq_trigger()
        S.TekScope.turn_on_channel(S.TekScope.flr_trace_channel)
        S.TekScope.turn_on_channel(S.TekScope.ref_trace_channel)
        S.TekScope.invert_channel(S.TekScope.flr_trace_channel)
           
    if X.pixelink_triggers_count:
        print 'starting pix with %d triggers'%X.pixelink_triggers_count
        S.Pixelink.start(X.pixelink_triggers_count)
        
    if X.apogee_triggers_count:
        print 'starting apogee with %d triggers'%X.apogee_triggers_count
        S.Apogee.start(X.apogee_triggers_count)
        
    if X.pointgrey_triggers_count:
        print 'starting PointGrey with %d triggers'%X.pointgrey_triggers_count
        S.PointGrey.start(X.pointgrey_triggers_count)
    ###################################################################################
    ## END RECIPE -- starts utbus
    ###################################################################################
    
    # Why is this here? This must be turned off earlier...
    X.set_IPG_AOM_driver_input_amplitude(0)    
    X.IPG_shutter_close()      
    X.end()
    S.Pixelink.labels = X.pixelinkLabels.strings
    print 'Pixelink Labels: ', S.Pixelink.labels
    S.Apogee.labels = X.apogeeLabels.strings
    S.PointGrey.labels = X.pointgreyLabels.strings
    ###################################################################################
    ## Post Processing -- stop cameras, get images, get other data (scopes), process...
    ###################################################################################
    
    if S.TekScope.bool_read_out_tek_scope:
        S.TekScope.grab_inverted_scope_trace(S.TekScope.flr_trace_channel)
        S.TekScope.grab_normal_scope_trace(S.TekScope.ref_trace_channel)
        S.TekScope.save_tekscope_settings()
        # S.TekScope.reset_auto_trigger()
        S.TekScope.stop()
        
        
    if X.pixelink_triggers_count:
        print 'GETTING PIXELINK IMAGES'
        image_list = S.Pixelink.get_images()
        S.Pixelink.stop()
        
    if X.apogee_triggers_count:
        S.Apogee.get_images()
        S.Apogee.stop()
      
    if X.pointgrey_triggers_count:
        # Workaround. When _imagelist is not [], the Settings module will call the
        # save function of the PointGreySettings object which is what needs to happen.
        S.PointGrey._imagelist = ['Not Empty']
       	S.PointGrey.stop()
     
    if X.pixelink_triggers_count==0 and X.apogee_triggers_count==0 and X.pointgrey_triggers_count==0:
        print '!!! WARNING : NO CAMERA TRIGGERS RECIEVED !!!'
    
    ###################################
    ##Take Wavemeter reading after run
    ###################################
    if S.bool_read_freq_TS1_comb:
        # Decide whether beatnote is positive or negative (depends on lock position)
        beatnote = (-1)**(S.error_signal_inversion+1)*S.beatnote
        wavemeter = float(get_wavemeter_freq())
        wavemeter_aom = wavemeter-2*S.TS1_aom_freq/1000.0
        rep_rate = X.MC_AC_53132A.get_frequency(1)
        offset_beat = X.MC_AC_53132A.get_frequency(2)
        

        if S.comb_offset_gain=='positive':
            ceo = offset_beat-rep_rate # moves left with increasing AOM voltage. negative. for kahan. ceo=cheif exec officer OR carrier env. offset freq. in this case.
        if S.comb_offset_gain=='negative':
            ceo = 2*rep_rate-offset_beat # moves right with increasing AOM voltage. positive

        ####################################################
        # wavemeter = float(get_wavemeter_freq())-2*aom_freq/1000.  #actaul frequence used for the lock
        # rep_rate = X.MC_AC_53132A.get_frequency(1)
        # offset_beat = X.MC_AC_53132A.get_frequency(2)
        # offset = offset_beat-rep_rate  # moves left with increasing AOM voltage, -ve gain
        # # offset = 2*rep_rate-offset_beat  # moves right with increasing AOM voltage. +ve gain
        # f_n780 = float(wavemeter*1000+beatnote)   # freq of comb line that we are locked to.
        # m = (10**(6)*f_n780-2*offset)/rep_rate  # calc the comb tooth number
        # m=3063056
        # f_TiSapph = (10**(-6)*(round(m)*rep_rate+2*offset)-beatnote)/1000.0   # ts freq at the lock
        # f_TiSapph_AOM = f_TiSapph+2*aom_freq/1000.0 +TS_main_AOM_freq/1000.0 # actaul ts freq at the exp/
        # deltaf = f_TiSapph*1e3-wavemeter*1e3
        # f_synth = 3*rep_rate/1000000
        ####################################################


        f_n780 = float(wavemeter_aom*1000+beatnote)
        m = (10**(6)*f_n780-2*ceo)/rep_rate 
        # if S.inversion_set==0:
        #     m = S.tooth_number+S.n_comb_tooth+S.error_signal_inversion*6
        # if S.inversion_set==1:
        #     m = S.tooth_number+S.n_comb_tooth-(1-S.error_signal_inversion)*6
        # m = round((10**(6)*f_n780-2*ceo)/rep_rate)

        
        f_lock = (10**(-6)*(round(m)*rep_rate+2*ceo)-beatnote)/1000.0  # freq. of the laser at the lock.
        # f_aom = (10**(-6)*(m*rep_rate))#+2*ceo)-beatnote)/1000.0
        f_TiSapph1 = f_lock+2*S.TS1_aom_freq/1000.0+0.08  # 0.08 is adding 80 MHz for the single pass AOM on route to the exp.

        # print data
        # S.PA.freq.append(str(get_wavemeter_freq()))
        # S.PA.freq.append(f_TiSapph1)
        # S.PA.freq.append(S.f_TiSapph2)
        # S.PA.freq.append(wavemeter)
        # # S.PA.freq.append(wavemeter_aom)
        # S.PA.freq.append(S.deltaf)
        # S.PA.freq.append(S.TS1_aom_freq)
        # S.PA.freq.append(beatnote)
        # S.PA.freq.append(ceo)
        # S.PA.freq.append(rep_rate)
        # S.PA.freq.append(offset_beat)
        S.PA.freq.append([f_TiSapph1, S.f_TiSapph2, wavemeter, S.deltaf, S.TS1_aom_freq, beatnote, ceo, rep_rate, offset_beat]) #Appends all of the values to be printed to PA_freq.txt
        
    elif S.bool_PA_TS2_comb:
        # Decide whether beatnote is positive or negative (depends on lock position)
        wavemeter = float(get_wavemeter_freq())
        rep_rate = X.MC_AC_53132A.get_frequency(1)
        offset = X.MC_AC_53132A.get_frequency(2)
        if S.comb_offset_gain=='negative':
            ceo = offset-rep_rate # moves left with increasing AOM voltage. negative
        if S.comb_offset_gain=='positive':
            ceo = 2*rep_rate-offset # moves right with increasing AOM voltage. positive
        #f_n780 = float(wavemeter*1000+beatnote)
        # m = round((10**(6)*f_n780-2*ceo)/rep_rate)
        f_TiSapph2= (10**(-6)*(S.tooth_number*rep_rate+2*ceo)-S.beatnote)/1000.0+0.08

        # print'@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
        # print'@@@@@                                       @@@@@'
        # print'@@@@@  beatnote %f                  @@@@@'%S.beatnote
        #print'@@@@@  wavemeter %f                  @@@@@'%wavemeter
        # print '@@@@   %f                            @@@@' %m
        # print'@@@@@   %f GHz                  @@@@@'%f_TiSapph2
        # print'@@@@@                                       @@@@@'
        # print'@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
        # print data
        # S.PA.freq.append(str(get_wavemeter_freq()))
        # S.PA.freq.append(f_TiSapph2)
        # S.PA.freq.append(wavemeter)
        # #S.PA.freq.append(S.list_element)
        # S.PA.freq.append(S.beatnote)
        # S.PA.freq.append(ceo)
        # S.PA.freq.append(rep_rate)
        # S.PA.freq.append(offset)
        S.PA.freq.append([f_TiSapph2, wavemeter,S.beatnote, ceo, rep_rate, offset]) #Appends all of the values to be printed to PA_freq.txt
        
        
    elif S.bool_read_freq_TS1_wavemeter:
        wavemeter = float(get_wavemeter_freq())
        # S.PA.freq.append(wavemeter)
        # S.PA.freq.append(S.PA.TS1_voltage)
        S.PA.freq.append([wavemeter,S.PA.TS1_voltage]) #Appends all of the values to be printed to PA_freq.txt
        
    # X.MC_AC_53132A.close()
    # X.MC_HP_8663A.close()
        
if __name__ == "__main__":
    pass

