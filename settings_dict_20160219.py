# -*- coding: utf-8 -*-   
'''
These are default values to be imported by the settings modules used in the experimental scripts.
2009.06.11 bruce klappauf
- added 'bool_loaded_mot_flourescence_imaging'

- added optical pumping variables - 20090710

- forced_depump_Rb variables - 20090728

- added mot_oscillations variables - 20091006

- added Li cooling ramp variable and some other Li AOM variables - 20091028

- added ramp variables for the Rb IPG loading

- added bool_UV_lamp

20091215_1 
- added dual variables and coil variables and loadtime variables.

- 20100226_0 changed feshbach field variables to be consistent with currently used master recipe

- 20100311_0 bruce added another general dict because it seems each dict can only have 256 entries
            a new settings module was saved to unpack this dict as well.
            
- 20100322_0 -ben- added variables for field calibration, and polar coordinates for Raman field

- 20100325_0 -ben- added drsc_cycle variables

- 20100422_0 bruce added variables for calibrated feshbach field ending in _G using new function 
        in master recipe.  renamed feshbach_1 _2 in more meaningful way hopefully.  listed in 
        feshbach section
        
- 20100722_0 -ben- changed Rb coils for MOT loading at 1.8A and ODT loading at 5.5A
- 20110509_0 -bruce- added high_field_imaging bool and amplitude and F.
'''
import os
print '\n================================================'
print 'Settings Dictionary: ',os.path.basename(__file__)
print '================================================'

_Rb85_values_ = dict(
    ## """
    ## use _set_dict for simple values as before or make a method
    ## for more complex ones
    ## """    
    loadmot_s = 6,
    ## MOT Settings
    pump_load_dF = -15,
    pump_load_ampl = 1,
    repump_load_dF = 0,
    repump_load_ampl = 1,
    slowing_beam_dF = -85,
    slowing_beam_ampl = 1,
    mot_coil_gradient_load_A = 2.2,#2.5, 
    coil_load_I = 2.2,#2.5,

    ## Zeeamn Slower Currents
    zeeman_coil_1_I = 0.81,#1.13,  #closest to source side
    zeeman_coil_2_I = 0.61,#0.85,  
    zeeman_coil_3_I = 0.5,#0.70,  
    zeeman_coil_4_I = 0.43,#0.60, 
    zeeman_coil_5_I = 0.36,#0.50, 
    zeeman_coil_6_I = 0.28,#0.39, 
    zeeman_coil_7_I = 0.29,#0.41,
    zeeman_coil_8_I = 0.0,#0.4,#0.90, #closest to science side

    ## Comp Coil For MOT Loading
    compx_load = -0.33,#-.12,
    compy_load = -4.42,#-5.3,
    compz_load = 0.0,#0.57,

    ## Comp Coil For ODT Loading
    compx_cool = 0,
    compy_cool = 0,
    compz_cool = 0,

    compx_cool_IPG =  -1.4,            # set the X location of mot for dipole trapping in IPG beam
    compy_cool_IPG =  -.15,           # set the Y location of mot for dipole trapping in IPG beam
    compz_cool_IPG =  2.5,#           # set the Z location of mot for dipole trapping in IPG beam
       
    compx_cool_SPI = -.3,#              # set the X location of mot for dipole trapping in SPI beam (left arm)
    compy_cool_SPI = .15,#             # set the Y location of mot for dipole trapping in SPI beam (left arm)
    compz_cool_SPI = .1,#.5                # set the Z location of mot for dipole trapping in SPI beam (left arm)
    
    ## Comp Coil for Magnetics Trap Loading
    compx_magnetic_trap_load = 0,
    compy_magnetic_trap_load = 0,
    compz_magnetic_trap_load = 0,
    



    
    moved_Rb_mot_reload_ms = 100,
    
    #MOT coil settings
    # coil_load_I = 4,  % -not in use at the moment
    coil_cool_I = 3,#6,
    coil_fl_image_I =5.0,

    #AOM Settings
    pump_dual_load_ampl = 1,
    
    pump_mot_cooling_stage_dF = -15,
    pump_mot_cooling_stage_ampl = 1,
    repump_mot_cooling_stage_dF = 6,
    repump_mot_cooling_stage_ampl = .6,

    pump_cool_dF = -18,#
    pump_cool_ampl = .30,
    repump_cool_dF = 0,
    repump_cool_ampl = .1,#.08,#

    pump_cool_mot_dF = -50,#
    pump_cool_mot_ampl = 1,
    repump_cool_mot_dF = 0,
    repump_cool_mot_ampl = 1,#
    
    pump_rb_magnetic_trapping_dF = -35,
    pump_rb_magnetic_trapping_ampl = 1,
    repump_rb_magnetic_trapping_dF = 0,
    repump_rb_magnetic_trapping_ampl = 1,
    
    pump_molasses_dF = -26,
    pump_molasses_ampl = 1,
    repump_molasses_dF = 0,
    repump_molasses_ampl = 1,
    
    pump_molasses_compress_dF = -26,
    pump_molasses_compress_ampl = 1,
    repump_molasses_compress_ampl = 1,
    repump_molasses_compress_dF = 0,
    
    pump_tweezer_molasses_cooling_dF = -15,
    pump_tweezer_molasses_cooling_ampl = 1,
    repump_tweezer_molasses_cooling_dF = 0,
    repump_tweezer_molasses_cooling_ampl = 0.11,   
    
    pump_abs_dF = 0,
    pump_abs_ampl = .7,
    repump_abs_dF = 0,
    repump_abs_ampl = 1,
    
    pump_fl_image_dF = -8,                    # pump detuning during flourescence imaging
    pump_fl_image_ampl = 1,
    repump_fl_image_dF = 0,                    # repump detuning during flourescence imaging
    
    pump_mot_image_dF = -0,                    # pump detuning during mot imaging with pixelink
    repump_mot_image_dF = 0,                    # repump detuning during mot imaging with pixelink
    
    pump_dualLoad_amplitude = 1,
    pump_dualLoad_dF = -16,
    repump_dualLoad_amplitude = 1,
    repump_dualLoad_dF =   6,
    
    #EOM Settings
    eo_pump_load_v = -5.2,#
    eo_pump_dualLoad_v =  -5.2,
    eo_pump_mot_cooling_stage_v = -2,
    eo_pump_flr_v = -5.2,#                          # eo setting for flourescence imaging
    eo_pump_cool_v = -5.2,#for IPG trapping    -1.5,#for SPI trapping,  
    eo_rb_magnetic_trapping_v = -2,
    eo_pump_cool_mot_v = -5.2,
    eo_pump_molasses_v = -5.2,
    eo_pump_molasses_compress_v = -5.2,
    eo_pump_tweezer_molasses_cooling_v = -3,
    eo_pump_abs_v = -1,                         # what's this here for anyway??
    eo_pump_off_v = .6,#-5.3,
    
    ## Rb Pixelink Flourescence Variables
    bool_pixelink_flourescence_imaging = 0,
    coil_PL_fl_A = 2,
    compx_PL_fl = 0,
    compy_PL_fl = 0,
    compz_PL_fl = 0,
    pump_PL_fl_amplitude = 1,
    pump_PL_fl_F = -20,
    repump_PL_fl_amplitude = 1,
    repump_PL_fl_dF = 0,
    expTime_PL_fl_ms = 20,
    )

_Rb87_values_ = dict(
    ## """
    ## use _set_dict for simple values as before or make a method
    ## for more complex ones
    ## """    
    loadmot_s= 6,
    #comp coil settings
    compx_load = .6,#
    compy_load = -1.1,#
    compz_load = 0,#

    compx_cool = 1.15,
    compy_cool = -1.2,
    compz_cool = -.85,

    compx_cool_IPG =  1.15,#        # set the X location of mot for dipole trapping in IPG beam
    compy_cool_IPG = -1.2,#          # set the Y location of mot for dipole trapping in IPG beam
    compz_cool_IPG = -.85,#        # set the Z location of mot for dipole trapping in IPG beam
       
    compx_cool_SPI = .8,#      # set the X location of mot for dipole trapping in SPI beam (left arm)
    compy_cool_SPI = -1.3,#   # set the Y location of mot for dipole trapping in SPI beam (left arm)
    compz_cool_SPI = -.9,#     # set the Z location of mot for dipole trapping in SPI beam (left arm)

    # Values for ODT Loading [SPI or IPG]
    
    #MOT coil settings
    coil_load_I = 5,
    coil_cool_I = 4,
    coil_fl_image_I =4.0,
    mot_coil_gradient_load_A = 5,
    
    #AOM Settings
    pump_load_dF = -18,
    pump_load_ampl = 1,
    repump_load_dF = -2,
    repump_load_ampl = 1,

    pump_cool_dF = -17,#-10,#
    pump_cool_ampl = 1,
    repump_cool_dF = 0,
    repump_cool_ampl = .23,#.12,#

    pump_cool_mot_dF = -17,#
    pump_cool_mot_ampl = 1,
    repump_cool_mot_dF = 0,
    repump_cool_mot_ampl = .23,#
    
    pump_tweezer_molasses_cooling_dF = -15,
    repump_tweezer_molasses_cooling_dF = 0,
    repump_tweezer_molasses_cooling_ampl = 0.11,   
    
    pump_abs_dF = 0,
    pump_abs_ampl = 1,
    repump_abs_dF = 0,
    repump_abs_ampl = 1,
    
    pump_fl_image_dF = -6,                    # pump detuning during flourescence imaging
    repump_fl_image_dF = 0,                    # repump detuning during flourescence imaging
    pump_mot_image_dF = -0,                    # pump detuning during mot imaging with pixelink
    repump_mot_image_dF = 0,                    # repump detuning during mot imaging with pixelink
    
    pump_dualLoad_amplitude = -.15,
    pump_dualLoad_dF = -54,
    repump_dualLoad_amplitude = .085,
    repump_dualLoad_dF =   -34,
    
    pump_detuning_check = -20,                  # detuning to change flr of MOT to check response of PD
    #EOM Settings
    eo_pump_load_v = .4,
    eo_pump_dualLoad_v =  .4,
    eo_pump_flr_v = .4,                          # eo setting for flourescence imaging
    eo_pump_cool_v = -2.6,# 
    eo_pump_cool_mot_v = -2.6,#-2.5,#
    eo_pump_tweezer_molasses_cooling_v = -3,
    eo_pump_abs_v = -1,                         # what's this here for anyway??
    eo_pump_off_v = -5.3,
    
    # #AOM Settings

    # pump_abs_dF = 5,
    # pump_abs_ampl = 1,
    # repump_abs_dF = 6,
    # repump_abs_ampl = 5,

    # #EOM Settings
    # eo_pump_cool_v = -1,
    # eo_pump_abs_v = -1,
    # eo_pump_off_v = -6.5,
            )

_Li6_values_ = dict(
    ## """
    ## use _set_dict for simple values as before or make a method
    ## for more complex ones
    ## """    
    
    # General MOT Settings
    loadmot_s = 5,

    # Zeeman Coil Currents and AOM Settings
    zeeman_coil_1_I = 6.9, #6.7, #closest to source side
    zeeman_coil_2_I = 4.2, 
    zeeman_coil_3_I = 3.8, 
    zeeman_coil_4_I = 3.2,
    zeeman_coil_5_I = 3,
    zeeman_coil_6_I = 2.45, #2.35, #2.27,
    zeeman_coil_7_I = 2.5, #2, 
    zeeman_coil_8_I = 3.5, # 2.95, #3.2,#,3.5, #closest to science side
    slowing_beam_AOM_frequency=63,
    slowing_beam_AOM_amplitude=1,

    # Coil Settings for MOT
    compx_load = -0.25, #0,
    compy_load = -7.1,#-2,#-4.5,#-6,
    compz_load = 0.7, #0,
    mot_coil_gradient_load_A = 11.5,

    #AOM Settings For Li MOT
    pump_load_dF = -41,#-45.5, #-45,
    pump_load_amplitude = 0.52,#1,
    repump_load_dF = -28,#-18.5,#-40,
    repump_load_amplitude = 1,

    # Coil Settings for ODT   
    compx_compress_SPI = 0, # 0.55,
    compy_compress_SPI = 0, # 1.0,
    compz_compress_SPI = 0, #0.19,

    compx_cool_SPI = 0, # 0.2,
    compy_cool_SPI = 0, # 2.0,
    compz_cool_SPI = 0, # 0.1,#.14,#.11,

    coil_compress_I =  15,

    # Timings of ODT
    tweezer_load_Li_ms = 15,
    mot_cool_ms  = 3.0,#2.0,
    ODT_Bfield_stabilization_time_ms = 30, #0,

    # AOM Settings for ODT
    pump_compress_dF = -30,
    repump_compress_dF = -30,
    pump_compress_amplitude = 0.4,#.5,
    repump_compress_amplitude = .7,

    pump_cool_dF = -5,#-4, #-4.5,
    repump_cool_dF = -4.5,
    pump_cool_amplitude = 0.17,#.14,
    repump_cool_amplitude = 0.145, #0.38,#.16,  

    # Absorption Imaging Settings
    pump_abs_amplitude = .33,
    repump_abs_amplitude = 1,
    pump_abs_dF = 0,
    repump_abs_dF = 0,

    # Flourescence Imaging Settings

    # Magnetic Trap
    bool_Li_Magnetic_Trap = 0,
    MagneticTrapCurrent_Li_A = 30,
    bool_PumpLower = 1,
    bool_PumpUpper = 0,
    hyperfine_Pump_time_ms = 1,






    pump_dualLoad_amplitude = .15,
    pump_dualLoad_dF = -30,
    repump_dualLoad_amplitude = .085,
    repump_dualLoad_dF =   -30,




    pump_fl_image_dF = -45,#-60
    pump_fl_image_amplitude = .05,
    repump_fl_image_dF = -30,
    repump_fl_image_amplitude = .09,#.04,
    
    pump_motfl_image_amplitude = .05,
    pump_motfl_image_dF =  -45,
    repump_motfl_image_amplitude =  .09,
    repump_motfl_image_dF =  -30,
    
    IPG_cross_fixed_F = 80, #frequency (fixed) of the AOM used to create a crossed IPG trap
    IPG_cross_amplitude = 0.6, #amplitude of the AOM used for crossed IPG
    

    high_field_abs_F = 100, #high field aom setting in MHz

    repump_abs_fiber_amplitude = .1,#.1,#
    high_field_abs_amplitude = 0.6, #high field aom setting in MHz
    
    #EOM Settings
    eo_pump_load_v = -0.5,
    eo_repump_load_v = -1.0,

    eo_pump_cool_v = -3.0,
    eo_repump_cool_v = -3.7,

    eo_pump_abs_v = -0.5,
    eo_repump_abs_v = -1.0,

    eo_pump_off_v = -5.5,
    eo_repump_off_v = -6.0,
    
    ## Li Pixelink Flourescence Variables
    bool_pixelink_flourescence_imaging = 0,
    coil_PL_fl_A = 4,
    compx_PL_fl = 0,
    compy_PL_fl = 0,
    compz_PL_fl = 0, #-1.7, # changed from 0 11/08/2015
    pump_PL_fl_amplitude = .12,
    pump_PL_fl_F = -20,
    repump_PL_fl_amplitude = .08,
    repump_PL_fl_dF = -22,
    expTime_PL_fl_ms = 100,

    # Misc settings
    cooling_ramp_ms = 5,
    coil_fl_A = 6,  # for fl. imaging
    compx_fl = 2,
    compy_fl = 2.5,
    compz_fl = 0,
    
        )
        
_PA_values_ = dict(
    ## """
    ## use _set_dict for simple values as before or make a method
    ## for more complex ones
    ## """    
    sign_lock = -1,                         # sign of f_lock = f_PA - f_comb
    sign_0 = -1,                            # sign of f_0
    f_lock = 8.599e6*68,                    # fixed offset lock freq for PA laser to comb
    tolerance_MHz = .1,                     # tolerance for PA laser freq setting
    max_iteration = 3,                      # maximum tries to get PA laser set error below tolerance
    setfrequency = 384229241700000,         # Rb85 F=3 to F=4 transition
    freq=[],                                #array for wavemeter readings
    
    ### Scan variables ###          Updated march7,2012 Magnus Haw
    scan_duration_ms = 1500,        # duration in ms of the scan
    scan_low_bound=0,          # lower bound of the scan [-5,5)
    scan_upper_bound=0,        # upper bound of the scan (-5,5]
    scan_dt_ms=.1                   # minimum time step size
    )
    
_apogee_values_ = dict(
    ## """
    ## use _set_dict for simple values as before or make a method
    ## for more complex ones
    ## """    
    #ROI_left = 1049 ,
    #ROI_top = 1145,
    #ROI_width = 23,
    #ROI_height = 22,
    ROIcenter_default = (0, 0, 1280, 1024), #(X,Y,w,h)(1065, 1213, 11, 8) # we are actually triggering pixelink here.......
    # ROIcenter_default = (1160, 788, 50, 50),  
	gain = 0,                #NA for apogee I think
    expTime_ms = 20,
    shutterDelay_ms = 9,
    triggerMode = 3,
    wait_ms = 400,           # wait time between two pixelink triggers in ms (>20 for repumping)
    pulse_delay =0,
    HOST = "LOCALHOST" ,   
        )
        
_pixelink_values_ = dict(
    ## use _set_dict for simple values as before or make a method
    ## for more complex ones
    gain = 0 ,              # possible values 0, 1.5, 3.1, 4.6
    expTime_ms = .08,      #exposure time ms
    wait_ms = 100,#30,           # wait time between two pixelink triggers in ms (>20 for repumping)

    #ROIcenter_default = (712, 492, 800, 464), #L,T,W,H
    ## pixelink ROI for dipole trap
    ROI_left = 320,          
    ROI_top = 280,
    ROI_width = 600,
    ROI_height = 280,
    ROIcenter_default = (637,380,200,200),#for SPI cross 20100429
    
    ## SPI cross trap settings
    image_detail_width = 50,
    image_detail_height = 50,
    image_detail_centre_x = 638,
    image_detail_centre_y = 361,
        )

_pointgrey_values_ = dict(
    gain = 0,
    expTime_ms = 5,
    wait_ms = 30.0,
    
    useROI = True,			# Use Region of Interest
    useROICenter = False,	# Use Region of Interest based on center point.
    
    ROI_left = 200,
    ROI_top = 400,
    ROI_width = 200,
    ROI_height = 500,
    ROI_center = (430, 640),	# (x,y)
    boostFramerate = False,
    
    saveImage = True,
    saveData = True,
    )

_tek_scope_values_ = dict(
        ## use for TEK scope variables
        SCOPEHOST = '172.16.1.106',
        bool_read_out_tek_scope = 0,
        flr_trace_channel = 'CH1',
        ref_trace_channel = 'CH2',
        scope_recapture_ms =200,
        bool_recapture_trace=0,
        )
        

_general_values_1 = dict(
    ## """
    ## use _set_dict for simple values as before or make a method
    ## for more complex ones
    ## NOTE: these dict's can only hold 256 entries so if adding entry gives this error then
    ##      moves some entries to next dictionary.
    ## """    
    
    # MAJOR BOOLEANS
    bool_PS_current_control = 1,            # If 1, the current stabalization for the MOT coils is done by the power supply (not the coil driver)
    bool_zeeman_slower = 1,                 # Turns on the Zeeman slower for MOT loading. 
    bool_Li = 1,                            # Run Li
    bool_Rb = 0,                            # Run Rb
    ## misc boolean values
    # bool_Rb85 = 1,                        # not in use at the moment, might come in handy one day
    bool_Rb87 = 0,
    
    bool_frequency_comb = 0,                # boolean variable to set comb settings
    bool_dump_mot_at_start = 0,
    bool_leave_mot_on =1,
    bool_Li_absorption_image = 0,
    bool_Rb_absorption_image = 0,
    bool_loaded_mot_flourescence_imaging_apogee = 0,
    
    # here are a bunch of numbers that has been added to master/personal scripts but not settings dict. this should be cleaned up
    bool_additional_load_time = 0,
    bool_scan_TS1_aom = 0,
    change_ts1_aom = 0, # why is this not named like a boolean? koko
    bool_scan_TS1_cavity = 0,
    bool_read_freq_TS1_wavemeter = 0,
    bool_read_freq_TS1_comb = 0,
    bool_PA_TS2_comb = 0,
    bool_write_Wavemeter = 0,

    bool_special = 0,
    bool_Li_pump_imaging2 = 0,
    bool_high_field_imaging = 0,
    
    bool_RB_D_line_meas =0,
    
    ## molasses cooling variables
    bool_molasses_cooling = 0,
    bool_molasses_initial_compression = 0,
    duration_molasses_cooling_ms = 3,
    molasses_coil_gradient_A = 0,
    compx_molasses = 0.1801,
    compy_molasses = -0.0145,
    compz_molasses = -0.1003,
    
    molasses_compress_coil_gradient_A = 5,
    duration_molasses_compress_cooling_ms = 3,
    
    
    
    ## mot coil current values
    compx_load = 0,
    compy_load = 0,
    compz_load = 0,
    
    mot_coil_gradient_dualLoad_A = 5.0,
    mot_coil_gradient_off_A = 0,#.1,
    mot_coil_turnon_wait_ms = 10,
    
    compx_dualLoad = 0,
    compy_dualLoad = 0,
    compz_dualLoad = 0,

    ##Apogee shutter check values
    bool_apogee_check =0,
    pulse_delay_ms = 1,
    pulse_time_ms = 1,

    ## shutter timing
    Li_pump_shutter_on_delay_ms = 3.50,
    Li_pump_shutter_on_duration_ms = .16,
    Li_pump_shutter_off_delay_ms = 4.64,
    Li_pump_shutter_off_duration_ms = .16,
    
    Li_repump_shutter_on_delay_ms = 3.9,
    Li_repump_shutter_on_duration_ms = .60,
    Li_repump_shutter_off_delay_ms = 5.68,
    Li_repump_shutter_off_duration_ms = .4,   
    
    Li_pump_abs_shutter_on_delay_ms = 4.25,#small changes on this affect pump 
    Li_pump_abs_shutter_on_duration_ms = .50,
    Li_pump_abs_shutter_off_delay_ms = 5.6,
    Li_pump_abs_shutter_off_duration_ms = .46,
    
    Li_repump_abs_shutter_on_delay_ms = 6.8,#6.6
    Li_repump_abs_shutter_on_duration_ms = .64,
    Li_repump_abs_shutter_off_delay_ms = 6.34,
    Li_repump_abs_shutter_off_duration_ms = 1.2,
    
    LiRb_mot_shutter_on_delay_ms = 7.2,
    LiRb_mot_shutter_on_duration_ms = 1.0,
    LiRb_mot_shutter_off_delay_ms = 15.2,
    LiRb_mot_shutter_off_duration_ms = 1.4,
    LiRb_mot_shutter_off_nobounce_duration_ms = 25.1,
    
    
    ## misc times
    SPI_settle_ms = 0,           #time for thermal lensing of SPI beams to stabalize.
    loadtime = 1,
    depump_ms = 5,                            # time to pump into lower hyperfine state

    mot_shutter_delay_ms = 4.14,    #delay time for opening/closing of mot shutter. Shutter is already/still open after this time, and opened/closes just before/after this time
    mot_shutter_delay_Li_ms = 6.4,    #delay time for opening of mot shutter using a nobounce sequence
    expansion_ms = 0,            # time of ballistic expansion in ms
    abs_shutter_delay_ms = 4.06,  # time for the absorption shutter to open
    Rb_mot_shutter_delay_no_bounce_first = 2,
    Rb_mot_shutter_delay_no_bounce_second = 2,
    Li_mot_compress_ms = 5,
    Li_hyperfine_pump_us = 400,
    Li_hyperfine_pumpdown_us = 0,
    Li_hyperfine_pumpup_us = 0,
    ODT_hyperfine_pump_time_us = 10,
    
    ## Tweezer - variables
    bool_pump_to_upper = 0,          # pumps to upper state instead of lower before tweezer hold time
    pump_to_upper_dF = 0,
    bool_tweezer_load = 0,                # boolean variable for the loading of the optical tweezer
    bool_SPI = 0 ,                           # boolean variable for using SPI Laser for trapping
    bool_IPG = 1  ,                          # boolean variable for using IPG Laser for trapping
    bool_SPIPG = 0 ,                       # boolean variabele to use both lasers for trapping
    IPG_power_set = 1.3,                     # control voltage for IPG AOM. 0 = no light, 2 = max light
    SPI_power_set = 30  ,               # output power of SPI laser. Not >50W!
    SPI_AOM_F = 110,                    #MHz 
    SPI_AOM_amplitude = 1,                 
    tweezer_load_ms = 50,#for SPI trapping,  90,#for IPG trapping                   # time to load tweezer
    tweezer_load_Li_ms = 8,
    IPGhold_ms = 500        ,                    # hold time in the tweezer
    SPIhold_ms = 500        ,                    # hold time in the tweezer
    compx_offset = 0.1801 ,                     # current through x-offset coils to compensate ambient magnetic field while holding in dipole trap
    compy_offset = -0.0145 ,                      # current through y-offset coils to compensate ambient magnetic field while holding in dipole trap
    compz_offset = -0.2803   ,                # current through z-offset coils to compensate ambient magnetic field while holding in dipole trap
    hold_ms = 0,                   # hold time in the tweezer
    bool_coil_turnoff = 1  ,                  # boolean variable for the turning off of the Mot and comp coils
    IPG_shutters_turnoff_ms = 7.8,#8.4            # time it takes to close the IPG tweezer shutter
    SPI_turnoff_ms = 0.015  ,              # time it takes to fully turn off SPI beam, 15us
    bool_SPIPG_transfer = 0,
    bool_tweezer_load_Rb_on_Li = 0,
    bool_ramp_dual_IPG = 0,
    bool_dual_IPGxfer = 0,
    bool_dual_SPIxfer = 0,
    
    ## variables for feshbach field (Li & dual)
    ###########################################
    #calibration assumes Bfield(G) = Current(A)*Slope(G/A) + Offset(G)
    #helmholtz_cal_slope = 32.0973,   #Gauss per amp for helmholtz field calibration (old coils)
      ##these values come from high field imaging calibration 15 Dec 2011##  
    #helmholtz_cal_slope = 28.02237,   #Gauss per amp for helmholtz field calibration (new coils)
    #helmholtz_cal_offset = 1.29372,  #Gauss offset for helmholtz field calibration
      ##these values come from Li pwave FR measurement on 24/April/2013, calibration needs to be improved##  
    helmholtz_cal_slope = 25.2177,#25.5897,#28.65596,#26.592,   #Gauss per amp for helmholtz field calibration (new coils)
    helmholtz_cal_offset = 1.5742,#43.6326,#3.38506,  #Gauss offset for helmholtz field calibration 
    # helmholtz_cal_slope = 27.31685,   #Gauss per amp for helmholtz field calibration (new coils)
    # helmholtz_cal_offset = -1.7935,  #Gauss offset for helmholtz field calibration
    wait_feshbach_ms = 1,
    
    #old variables
    bool_feshbach_in_tweezer = 0,
    bool_feshbach_in_tweezer2 =0,
    feshbach_current_1_A = 0,
    hold_time_feshbach_field_ms = 0,
    feshbach_current_2_A = 0,
    feshbach_Li_xfer_A = 23.8,  #=gauss/31.8
    
    #new variables
    feshbach_Li_in_SPI_G = 0,   #field in Gauss after Li loads in SPI, held for fesh_hold
    feshbach_Li_SPIPG_xfer_G = 840, #field in Gauss for all Li and dual SPIPG transfer to IPG
    feshbach_Li_evap_G = 840,  #field in Gauss for Li evap in SPI
    bool_feshbach_in_dual_tweezer = 0, #field in Gauss after any dual tweezer load 
    feshbach_in_tweezer_dual_G = 0,#field in Gauss for for any dual tweezer feshbach field
    feshbach_dual_evap_G = 0,  #field in Gauss dual evaporation after dual load
    
    ## variables for the IPG turn on ramp
    #####################################
    bool_IPG_turnon_ramp = 0,
    wait_IPG_turnon_ramp_ms = 10,
    duration_IPG_turnon_ramp_ms = 5,
    
    ## variables for IPG power ramp while loading into IPG
    ######################################################
    bool_IPG_load_ramp = 0,
    bool_load_power_ramp = 1,
    bool_load_freq_ramp = 0,
    wait_IPG_load_ramp_ms = 10,
    power_IPG_load_ramp = 0.7,
    freq_IPG_load_ramp = -30,
    repump_ampl_IPG_load_ramp = 0.1,
    eo_pump_IPG_load_ramp = -3,
    duration_IPG_load_ramp_s = 0.01,
    
    ## mot cooling stage variables
    ##############################
    bool_mot_cooling_stage = 0,
    mot_cooling_stage_coil_gradient_A = 3,
    duration_mot_cooling_stage_s = 2,
    
    ## molasses cooling in tweezer variables
    ########################################
    bool_tweezer_molasses_cooling = 0,
    wait_tweezer_molasses_cooling_ms = 10,
    duration_tweezer_molasses_cooling_ms = 1,
    
    ## Tweezer Modulation Variables [Trap Freq. Measurements]
    #####################################
    bool_IPG_mod = 0,                        # boolean variable to modulate IPG trap
    IPG_mod_amplitude = 1,                   # modulation strength
    mod_freq_kHz = 3,                    # frequency of modulation in kHz
    mod_offset_V = 1.3,                    # offset of IPG AO used during modulation. Do not set > 1.5V.
    mod_time_ms = 3000,                        # time for modulation. occurs in last 'S.mod_time_ms' of hold time. S.mod_time_ms > S.hold
    bool_mod_ramp_before = 0,                         # boolean to ramp down power of Trap over a certain time scale
    bool_mod_ramp_after = 0,                        
    mod_ramp_ms = 200,                         # total time to ramp trap down to min power and back up
    mod_wait_ms = 1000,                            #time to hold trap before ramp or modulation
    IPG_min_power_V = .4,                            # minimum power of IPG during ramp
    # Note the amplitude of the modulation is NOT a variable we can set. It ranges between 0 and 250mV depening on osc. frequency.

    ## Tweezer Modulation Variables [Trap Freq. Measurements] for SPI Laser
    #####################################
    mod_wait_SPI_ms = 500,
    mod_time_SPI_s = 1,
    mod_freq_SPI_kHz = 1,
    mod_amp_p = 3,
    bool_SPI_mod = 0,
    
    ## Detuning check variables
    Rb_pump_detuning_change = 0,
    pump_detuning_check_wait_ms = 10,
    ## separated depumping stage - variables
    bool_forced_depump_Rb = 0,
    detuning_forced_depump_Rb_MHz = 0,
    wait_forced_depump_Rb_ms = 6,              # time before opening shutter needed for repump shutter rto be closed. additional 14ms of pumping time for the pumping shutterd to open an close.
    power_forced_depump_Rb = 1,
    duration_forced_depump_Rb_ms = 0.1,
        
    ## resonant removal of atoms - variables
    bool_Rb_out = 0,
    hold_Rb_out_ms = 50,
    
    ## Photo Association - variables
    bool_PA_light = 0      ,                  # boolean variable for PA-light
    wait_PA_light_on= 200   ,              # wait time before turning on PA-light in ms
    PA_light_hold_ms = 2    ,                # time the PA-light is on in ms
    
    ## optical pumping - variables
    bool_optically_pump_Rb = 0,                 # boolean variable, if optical pumping shall be
    bool_opt_pump_with_ipg_off = 0,
    compx_pump = -5.16 ,                        # current through x-offset coils for optical pumping along dipole trap axis
    compy_pump = -1.68 ,                        # current through y-offset coils for optical pumping along dipole trap axis
    compz_pump = 0   ,                          # current through z-offset coils for optical pumping along dipole trap axis
    wait_pump_Rb_ms = 6,                        # time before opening shutter needed for repump shutter rto be closed. additional 14ms of pumping time for the pumping shutterd to open an close.
    duration_pump_Rb_ms = .1,                   # duration of  optical pumping
    detuning_pump_Rb_MHz = -25,                 # detuning of repumper for optical pumping (70MHz ac-stark - 63.4 F2-3 - 29.4 F1-2)
    detuning_depump_Rb_MHz = 0,                 # detuning of pump/depumping AOM (70MHz ac-stark - 63.4 F2-3)
    power_pump_Rb = .1,                         # power set at repump AOM (between 0 and 1)
    power_depump_Rb = .01,                      # power set at depump AOM (between 0 and 1)  if set to 0 the shutter is closed as well!
    pump_angle_theta = 0,                      # angle between xy plane and z axis, 0 is xy plane!
    pump_angle_phi = 29,
    ## hyperfine pumping - variables
    bool_hyperfine_pump_Rb = 0,                 # boolean variable, if optical pumping shall be
    wait_hyperfine_pump_Rb_ms = 6,                        # time before opening shutter needed for repump shutter rto be closed. additional 14ms of pumping time for the pumping shutterd to open an close.
    duration_hyperfine_pump_Rb_ms = .1,                   # duration of  optical pumping
    detuning_hyperfine_pump_Rb_MHz = -25,                 # detuning of repumper for optical pumping (70MHz ac-stark - 63.4 F2-3 - 29.4 F1-2)
    detuning_hyperfine_depump_Rb_MHz = 0,                 # detuning of pump/depumping AOM (70MHz ac-stark - 63.4 F2-3)
    power_hyperfine_pump_Rb = .1,                         # power set at repump AOM (between 0 and 1)
    power_hyperfine_depump_Rb = .01,                      # power set at depump AOM (between 0 and 1)  if set to 0 the shutter is closed as well!
        # microwave removal
    bool_mw_removal = 0,
    mw_removal_start_freq = 3035732439 + 500e3,
    mw_removal_end_freq = 3035732439 + 500e3,
    mw_removal_dur_ms = 100,
    
    ## Raman transition stage variables
    bool_raman_stage = 0,                       # boolean variable for Raman tansition stage
    # wait_raman_stage = 10,                      # time before coils are set to raman transition field
    duration_raman_stage = 200,                 # duration of Raman transition stage (holdtime) in ms
    raman_stage_field_strength_G = .45,
    raman_stage_angle_theta = 0,                      # angle between xy plane and z axis, 0 is xy plane!
    raman_stage_angle_phi = 130,                       # angle in xy plane, 0 is along chamber pointing towards oven

    ## DRSC Cooling stage variables
    bool_drsc_stage = 0,
    wait_drsc_Rb_ms = 10,
    duration_drsc_Rb_ms = 200,
    drsc_detuning_pump_Rb_MHz = -40,                  # detuning of repumper for optical pumping (70MHz ac-stark - 63.4 F2-3 - 29.4 F1-2)
    drsc_detuning_depump_Rb_MHz = -23,    # detuning of pump/depumping AOM (70MHz ac-stark - 63.4 F2-3)
    drsc_power_pump_Rb = .15,                             # power set at repump AOM (between 0 and 1)
    drsc_power_depump_Rb = 0.015, 
    drsc_field_strength_G = 1,
    drsc_angle_theta = 0,
    drsc_angle_phi = 36+45,
    
    ## MW-transfer variables
    bool_mw_transfer = 0,                    # boolean variable for MW-transfer
    wait_mw_transfer = 100,                    # time in tweezer before MW-transfer
    Rb_mw_transfer_MOT_coil_A = 0,
    mw_start_freq = 3035732439 - 500e3,        # start frequency for MW-transfer
    mw_end_freq = 3035732439 + 500e3,        # end frequency for MW-transfer
    mw_scan_dur = 100    ,                    # duration of MW-scan (holdtime) in ms
    
    compx_mw_offset = 1,
    compy_mw_offset = 1,
    compz_mw_offset = 1,
    
    
    compx_transient = .4,
    compy_transient = .5,
    compz_transient = .6,
    ## Li MW-transfer variables
    bool_Li_mw_transfer = 0,                    # boolean variable for MW-transfer
    wait_Li_mw_transfer = 30,                    # time in tweezer before MW-transfer
    Li_mw_start_dF = 0,        # start dF in MHz from 228Mhz for MW-transfer
    Li_mw_end_dF   = 0 ,       # end dF in MHz from 228Mhz for MW-transfer
    Li_mw_scan_dur_s = .020 ,  # time to scan from start dF to end dF in sec
    Li_pumpdown_dF = 0,
    Li_pumpdown_ampl = .15,
    Li_mw_amplitude = .3,       # dds amplitude to amplifier chain to mw antenna
    bool_Li_pumpdown = 0,        #opens the pump shutter to pump atoms to +-1/2 in the ground state
    bool_mw_pump_back_up = 0,     #RF pulse from lower ground state to the upper ground state. Default from +1/2 up
    bool_repeat_mw_pump = 0,       #repeats RF pumping done by Li_mw_transfer, to check if the considered state was cleaned
    Li_mw_pump_back_up_dF = 1.490,  #position of the +1/2 resonance in IPG
    bool_skip_Li_mw_xfer = 0,
    
    ## evaporative cooling variables
    ####################
    bool_evaporative_cooling_SPI = 0 ,          # boolean variable for evaporative cooling in (SPI-) dipole trap,
    bool_pre_evaporative_cooling_SPI = 0,
    bool_evaporate_after_dual_feshbach = 0,     #ramps down SPI after both Rb and Li loaded
    SPI_final_dual_evap_pwr_W = 8,              #final pwr for dual evap ramp
    wait_cooling_SPI_ms = 10,
    power_cooling_SPI = 5  ,                    # output power of SPI laser at end of cooling ramp
    SPI_pre_evaporation_Rb_stop_W = 20,         # stop power for pre transfer evaporation
    SPI_evaporation_Li_stop_W = 0,             #stop power for Li evaporation
    ramp_duration_cooling_SPI_s = 0.2 ,         # time for the evaporative cooling ramp in s
    ramp_duration_cooling_SPI_s_xfer = .05,     # duration for SPI rampdown for IPG xfer.
    ramp_duration_cooling_LiRb_SPI_s = 0.1,     #time for dual evap ramp
    
    bool_evaporative_cooling_IPG = 0,           # boolean variable for evaporative cooling in (SPI-) dipole trap,
    wait_cooling_IPG_ms = 10,
    IPG_power_cooling_1 = 1,                      # IPG AOM set voltage at end of cooling ramp
    ramp_duration_cooling_IPG_s_1 = .1,
    IPG_power_cooling_2 = 1,                      # IPG AOM set voltage at end of cooling ramp
    ramp_duration_cooling_IPG_s_2 = .1,
    IPG_power_cooling_3 = 1,                      # IPG AOM set voltage at end of cooling ramp
    ramp_duration_cooling_IPG_s_3 = .1,
    IPG_power_cooling_4 = 1,                      # IPG AOM set voltage at end of cooling ramp
    ramp_duration_cooling_IPG_s_4 = .1,
    IPG_power_cooling_5 = 1,                      # IPG AOM set voltage at end of cooling ramp
    ramp_duration_cooling_IPG_s_5 = .1,
    IPG_power_cooling_6 = 1,                      # IPG AOM set voltage at end of cooling ramp
    ramp_duration_cooling_IPG_s_6 = .1,
    
    

        )
        
        
_general_values_2 = dict(
    ## """
    ## use _set_dict for simple values as before or make a method
    ## for more complex ones
    ## NOTE: these dict's can only hold 256 entries so if adding entry gives this error then
    ##      moves some entries to next dictionary.
    ## """    
    ## IPG power ramp variables
    ###########################
    bool_ramp_IPG = 0,           # boolean variable for evaporative cooling in (SPI-) dipole trap,
    wait_ramp_IPG_ms = 10,
    power_ramp_IPG_1 = 1,                      # IPG AOM set voltage at beginning of ramp
    power_ramp_IPG_2 = 1,                      # IPG AOM set voltage at end of ramp
    duration_ramp_IPG_s = .1,
    
        ## Imaging variables
    ####################
    bool_recapture = 1  ,                  # boolean variable for recapture of atoms from tweezer
    recapture_time_ms = 18,
    bool_pump_imaging = 1  ,                  # pump in upper state before imaging
    bool_pump_imagine_IPG_axis = 1,
    bool_pump_imaging_in_odt = 0,
    bool_Li_pump_imaging = 0  ,                  # pump in upper state while in tweezer before imaging
    pump_ms = .01,#.06,                          # time for hyperfine pumping before absorption imaging in ms
    bool_absorption_imaging = 0  ,          # boolean variable for absorption imaging
    bool_fluorescence_imaging = 1 ,           # boolean variable for fluorescence imaging
    fluorescence_calibration_factor = 1,#0.81, # calibration factor between pixel counts and atoms for Rb
    bool_loaded_mot_flourescence_imaging = 0,
    bool_loaded_mot_flourescence_imaging_pixelink = 0,
    bool_Li_absimage_absrepump_on = 1,
    bool_Li_absimage_motrepump_on = 0,
    Li_repump_pump_up_amplitude = 0.007,
    
    
    ## Admin
    N = 1  ,                             #number of times to run sequence with S.sequence_list
    sequence_list = [] ,      #can be list of pairs [('setting1',[val1,val2...]),('setting2',[val1,val2...])]
    printout_list = ['place strings to print here'],  #for showing data on image processor outputs
    datafolder = "C:\DATA",
    reference_settings = [],
    ## DRSC loop
    bool_drsc_loop = 0,
    drsc_cycles = 1,
    duration_drsc_cycle_field_ms = 100,
    power_pump_Rb_drsc_cycle = .3,
    power_depump_Rb_drsc_cycle = .2,
    duration_pump_Rb_drsc_cycle_ms = .5,
    
    ## LIAD variables
    
    ## mot oscillation variables
    bool_mot_oscillation = 0,
    wait_mot_oscillation_ms = 10,
    repump_mot_oscillation_dF = -30,
    # compy_mot_oscillation = 1,
    repetitions_mot_oscillation = 100,
    offtime_mot_oscillation_ms = 10,
    ontime_mot_oscillation_ms = 40,
    
    ## Rb FB In Tweezer Only
    bool_feshbach_Rb_tweezer_only = 0,
    hold_time_feshbach_field_ms = 0,
    feshbach_field_Rb_only_G = 0,
    
    ## magnetic field ring down
    bool_field_ring_down = 0,
    field_ring_down_duration_ms = 1,
    
    ## Compensation coils
    compx_calibration = 0.807,
    compy_calibration = 1.75,
    compz_calibration = -1.33,
    
    ## compensation coil settings for zero magnetic field 
    ## not using the Feshbach coils
    # ## compensation coil settings for zero magnetic field 
    # ## using Li trapping and precooling with 840G field
    compx_zero =  0,#0.148,#0.159,
    compy_zero =  0,#0.180,#0.015,
    compz_zero = 0,#-1.079,#-1.33,
    
    bool_cycle_mot_coils_supply_output = 0,
    bool_cycle_fb_coil_supply_output_during_trapping = 0,
    bool_depump_off_before_FB_field = 0,
    bool_depump_off_after_FB_field = 0,
    bool_high_antihelmoltz_field_after_sequence = 1,
    bool_high_antihelmoltz_field_during_trapping = 0,
    bool_AH_dual_reset = 0,
    
    current_high_antihelmoltz_field_A = 20,
    hold_high_antihelmoltz_field_ms = 10,
    wait_after_high_antihelmoltz_field_ms = 10,
    
    ## magnetic trap 
    bool_load_rb_magnetic_trap = 0,
    hold_rb_magnetic_trap_s = 10,
    compress_magnetic_trap_coil_gradient_A = 5,
    initial_magnetic_trap_coil_gradient_A = 10,
    hold_magnetic_trap_coil_gradient_A = 10,
    Rb_magnetic_trap_pump_ms = 1,
    bool_pump_rb_magnetic_trap_F2 = 0,
    bool_pump_rb_magnetic_trap_F3 = 0,    
    
    ## Magnetic Trap SS Ramp
    ############################3
    bool_Rb_magnetic_trap_ss_ramp = 0,
    Rb_magnetic_trap_ss_time_ms = 100,
    Rb_magnetic_trap_ss_ramp_wait_ms = 1000,
    Rb_magnetic_trap_ss_ramp_gradient_A = 5,
    #################
    bool_take_apogee_image = 0,
    bool_depump_along_xy = 0,
    
    ####################
    bool_flash_ipg_off_on = 0,
    ipg_flash_off_time_ms = 0,
    SRS_shutter_open_delay_ms = 2.9,
    SRS_shutter_close_delay_ms = 2.3,
    
    ## Electric Field Variables
    ###########################
    bool_electric_field_during_LiRb_feshbach = 0,
    wait_electric_field_LiRb_feshbach_ON_ms = 500,
    
    ## No Bounce Shutter Timings
    ############################
    Li_pump_no_bounce_on_delay_ms = 2.38,
    Li_pump_no_bounce_on_action_ms = 3.50,
    Li_pump_no_bounce_off_delays_ms = 4.76,
    
    Li_repump_no_bounce_on_delay_ms = 3.22,
    Li_repump_no_bounce_on_action_ms = 3.80,
    Li_repump_no_bounce_off_delays_ms = 4.09,
    
    Li_pump_abs_no_bounce_on_delay_ms = 3.06,
    Li_pump_abs_no_bounce_on_action_ms = 4.06,
    Li_pump_abs_no_bounce_off_delay_ms = 5.08,
    
    Li_repump_abs_no_bounce_on_delay_ms = 4.65,
    Li_repump_abs_no_bounce_on_action_ms = 7,#5.38,
    Li_repump_abs_no_bounce_off_delay_ms = 11.6,
    
    Li_slowing_beam_no_bounce_on_delay_ms = 2.66,
    Li_slowing_beam_no_bounce_on_action_ms = 4.32,
    Li_slowing_beam_no_bounce_off_delay_ms = 4.64,
    Li_slowing_beam_no_bounce_off_action_ms = 6.12,
    
    Li_high_field_imaging_no_bounce_on_action = 2.74,
    
    Li_abs_imaging_delay_ms = 15,  #15
    Li_PL_fl_imaging_delay_ms = 15,

    ## Pixelink SPI Check
    ######################
    bool_pixelink_check = 0,
    SPI_pixelink_check_power_set = 0,
    
    ####
    max_fb_coil_supply_current = 30,
    
    ### Photoassociation variables
    bool_read_Wavemeter = False,                           # Boolean for taking wavemeter readings before and after each run
    bool_scan_TiSapph = False,                           # Boolean for whether to scan the Tisapph during each sequence

    ## spin cleanup
    bool_spin_cleanup_with_Bield = 0,
    spin_clean_grad_I = 20,
    spin_cleanup_duration_ms =1000,
    
    ## MISC things that were never added before
    bool_IPG_into_cross_evap_before_Rb_load = 0,
    
    ## IPG MOD OFF/ON
    bool_modulate_ipg_off_and_on = 0,
    freq_IPG_off_on_modulation_kHz = 0,
    duration_IPG_off_on_modulation_ms = 0,
    
    ## Second arm mod for trap freq
    bool_IPG_second_arm_mod = 0,
    IPG_second_arm_mod_wait_ms = 100,
    IPG_second_arm_mod_time_ms = 1000,
    IPG_second_arm_freq_kHz = 10,
    IPG_secomd_arm_mod_amp_W = 1.0,
    IPG_second_arm_offset_W = 6.0,
    
    # mult freq tis
    bool_scan_multiple_freq = 0,
    number_of_freq = 0,
    step_size_V = 0,
    
    ## misc variables
    bool_apply_PA_light_during_FB_scan = 0,
    feshbach_LiRb_in_IPG_G = 0,
    set_gradient_coil_current = 0,
    bool_LiRb_FB_after_plain_evap = 0,
    FB_scan_after_plain_evap_ms = 0,
    bool_before_IPG_evap = 0,
    bool_after_IPG_evap = 0,
    bool_create_molecules = 0,
    Li_molecule_field_G = 300,
    Li_molecule_wait_ms = 100,
    bool_RF_STIRAP = 0,
    ODT_Bfield_stabilization_time_ms = 10,
    
    ## gradient coil
    bool_gradient_evap = 1,            # boolean
    gradient_coil_current_I = 0,       # currrent though coil. 5 A max
    gradient_coil_evap_wait_ms = 0,   # wait before coil on
    gradient_coil_evap_time_ms = 0,    # wait with coil on
    
    ## COMP COILS FOR PA
    compx_PA = -3.5497,
    compy_PA = -0.1758,
    compz_PA = -1.65,
        
    ##Zeeman Slower Beam Parameters

    
    ## Standford Research DS345 Function Generator
    bool_set_DS345_sinewave_parameters=0,
    bool_modulation_after_IPG_ramp_up=0, 
    DS345_comAddress=3,
    DS345_frequency=0,
    DS345_amplitude=0,
    DS345_offset=0,
    DS345_mod_time=0,
    freq_mod_IPG_ramp_up_power = 0,
    
    ## missing misc stuff
    Rb_MOT_stark_shift_detection = 0,
    bool_apply_electic_field = 0,
    bool_electric_field_during_Li_MOT_load=0,
    bool_electric_field_on_before_ODT_load=0,
    bool_electric_field_Rb_ODT=0,
    bool_load_Rb_MOT_in_EField=0,
    bool_LiRb_plain_evap_electric_field_turnon=0,
    bool_electric_field_on_with_Li_in_ODT=0,

    bool_Li_spin_cleanup =0,
    Li_spin_cleanup_AOM_F = 99.0,
    Li_spin_cleanup_AOM_amp = .15, 
    Li_spin_cleanup_wait_ms = 1,
    
    ## NEW SHUTTER TIMINGS
    Li_MOT_shutter_open_delay_ms = 5.8,
    Li_MOT_shutter_close_delay_ms = 3.65, # from 2016_05_11 with SRS shutter, old value (iShutter) 4.8
    
    Zeeman_Slower_shutter_open_delay_ms = 7.6,
    Zeeman_Slower_shutter_close_delay_ms = 3.5,
    
    Li_repump_abs_shutter_open_delay_ms = 7.6, #6.6
    Li_repump_abs_shutter_close_delay_ms = 3.4,
    
    Li_pump_abs_shutter_open_delay_ms = 7.3, # 6.3
    Li_pump_abs_shutter_close_delay_ms = 3.6,

    Li_HF_imaging_shutter_open_delay_ms = 9.0,
    Li_HF_imaging_shutter_close_delay_ms = 7.0,

    # Things Will needs to look up and figure out... eventually
    bool_loaded_mot_fluorescence = 0,
    bool_cool_mot = 0,
    cool_mot_ms = 75,                        # time to leave MOT in cool settings before imagining   NOT USED???
    cool_Rb_mot_ms = 10,                        # time to leave MOT in cool settings before imagining 
    Li_mot_cool_ms = 2,                        # time to leave MOT in cool settings before imagining 
    cool_Li_mot_ms = 2,
    bool_move_Rb_mot = 0,
    bool_dual_image =0,  
    )