# -*- coding: utf-8 -*-
'''
This is meant to be run in the morning to test the MOT
'''

from UTBus_Recipesb.settings_files.settings_modules import settings_module as settings_module
import math
import sys,time
from numpy import arange,linspace,exp,log,loadtxt
import random

import UTBus_Recipesb.AOM_calibrations as C

'''
=============================
        Settings Module
=============================
'''
print 'file',__file__
for i in sys.path:
    print i
print 'settings_module',settings_module
S = settings_module.Settings(__file__)
'''
=============================
        Major Booleans
=============================
'''
S.N = 1  # what is this for???             
S.bool_Li = 1
S.bool_Rb = 0
S.bool_dump_mot_at_start = 1


if S.bool_dump_mot_at_start:
    S.Li6.loadmot_s = 5
    S.Rb85.loadmot_s = 1
else:
    S.Li6.loadmot_s = 0.1
    S.Rb85.loadmot_s = 0.1


# This needs work, now that we use the ZS
S.bool_additional_load_time = 0
S.add_load_time_s = 0

# Need to check what these do. Still needed? ###
S.bool_cycle_mot_coils_supply_output = 0    #option to cycle mot coils on/off before mot loading in order to "reset" coils
S.bool_AH_dual_reset = 0                    # reset mag field after li loaded in SPI, before Rb MOT loading

S.bool_high_antihelmoltz_field_after_sequence = 0
'''
=============================
        Rb Variables
=============================
'''
###################
## MOT Variables ##
###################
S.Rb85.compx_load = -.12
S.Rb85.compy_load = -5.3
S.Rb85.compz_load = 0.57

S.Rb85.pump_load_dF = -15
S.Rb85.repump_load_dF = 0
S.Rb85.repump_load_ampl = 1
S.Rb85.pump_load_ampl = 1

S.Rb85.slowing_beam_dF = -85
S.Rb85.slowing_beam_ampl = 1

S.Rb85.mot_coil_gradient_load_A = 2.5  #6
'''
=============================
        Dipole Trap
=============================
'''  
if S.bool_Li:
    S.bool_tweezer_load = 1              # boolean variable for the loading of the optical tweezer
    S.Li6.bool_Li_Magnetic_Trap = 0
    S.Li6.MagneticTrapCurrent_Li_A = 10
    S.bool_SPI = 1                          # boolean variable for using SPI Laser for trapping
    S.SPI_settle_ms = 0
    
    S.bool_IPG = 0                          # boolean variable for using IPG Laser for trapping
    S.bool_SPIPG = 0                        # boolean variabele to use both lasers for trapping                  
    S.bool_dual_SPIxfer = 0
    S.bool_load_SPI_and_IPG = 0
     
    S.bool_coil_turnoff = 1                 # boolean variable for the turning off of the Mot and comp coils. I dont think this gets used for Li
    S.bool_pump_to_upper = 0                # pumps to upper state instead of lower before tweezer hold time

    
    S.IPG_power_set = 1                     # control voltage for IPG AOM. 0 = no light, 1 = max light
    
    S.IPG_power_set_W = 20.0                # actual output power of IPG, if IPG set to 20W, SPIPG transfer ramps IPG on to this value!
    S.SPI_power_set = 100.0                 # output power of SPI laser. Set to 100 to get full power (will clip at highest possible value)
    S.hold_ms = 50    #!!!!                   # hold time in the tweezer. must be > 25 if using PS to control current                   # wait time between turning on SPI and loading trap
    S.Li_hyperfine_pump_us = 500     #!!!!        #pump to lower state during end of tweezer loading, must be <600us

    
    S.bool_IPG_cross = 0   # NOTE: If turned on, and IPG transfer is selected, the atoms are transferred directly into the cross.    
    S.IPG_cross_AOM_amplitude = 0
       
    ################################
    ## SPI Evaporation and Fields ##
    ################################
    
    S.feshbach_Li_in_SPI_G =  350#800#350         # Field during intial plain evaporation
    S.feshbach_Li_evap_G = 350#800#350            # Field for evaporation in SPI only, used during high power evap
    S.wait_cooling_SPI_ms = 0             # Wait before any evaporation
    
    # Free Evaporation
    S.bool_feshbach_in_tweezer = 0
    S.hold_time_feshbach_field_ms = 100.0
    S.SPI_evap_wait_before_field_off = 0        # after all possible evaps, field is turned off unless transfer takes place         
    
    # High Power Evaporation
    S.bool_high_power_evap_SPI = 1#S.evap_SPI ******************
    S.SPI_high_power_evap_wait = 0
    S.SPI_high_power_evap_stop = 50
    S.high_power_evap_ramp_duration_ms = 100#25x

    # Variables for SPI Exponential Ramp
    S.bool_evaporative_cooling_SPI_exp = 0
    S.SPI_power_start_W = 50.0
    S.SPI_power_end_W = 10.0
    S.SPI_exp_total_ramp_duration_ms = 500.0
    S.SPI_exp_stop_power_W = 10.0
    S.tau_SPI_ms = -S.SPI_exp_total_ramp_duration_ms/(math.log(S.SPI_power_end_W/S.SPI_power_start_W))
    S.exp_ramp_duration_SPI_ms = -S.tau_SPI_ms*math.log(S.SPI_exp_stop_power_W/S.SPI_power_start_W)
    
    # Variables for initial SPI only linear evaporation
    S.bool_evaporative_cooling_SPI = 0#S.evap_SPI
    S.SPI_evaporation_Li_stop_W_1st = 1
    S.ramp_duration_cooling_SPI_ms = 2000
    
    # Variables for second linear evap ramp (SPI only)
    S.bool_second_evaporative_cooling_SPI = 0
    S.SPI_evaporation_Li_stop_W_2nd = 10
    S.second_ramp_duration_cooling_SPI_ms = 300

    # Variables for SPI Ramp Up
    S.bool_ramp_SPI_up = 0
    S.SPI_Li_ramp_up_to_W = 10
    S.ramp_up_duration_SPI_ms = 50

    # S.temp_wait_time_ms = 1250
    
    #########################
    ## Things to do IN SPI ##
    #########################
    
    S.bool_PA_in_SPI = 0  # Note: Not fully fleshed out yet... 
    S.SPI_power_at_transfer = 50.0
    
    ###################################
    ## SPI to IPG Transfer Variables ##
    ###################################
    
    S.feshbach_Li_SPIPG_xfer_G = S.feshbach_Li_evap_G     # Field used during transfer to IPG
    S.bool_SPIPG_transfer = 1 # **************************
    S.SPIPG_transfer_wait_ms = 10
    S.wait_after_transfer_ms = 10
    S.wait_IPG_turnon_ramp_ms = 0       # NA if S.bool_load_SPI_and_IPG
    S.duration_IPG_turnon_ramp_ms = 1   # NA if S.bool_load_SPI_and_IPG
    
    S.ramp_duration_transfer_SPI_ms = 500#2100#1000 #2.1s instead of 1s increased the atom number from 43k to 68k
    
    if S.bool_SPIPG_transfer:
        total_ramp_time_ms = S.ramp_duration_transfer_SPI_ms
        SPI_power_at_IPG_turnon = 50.0
        S.SPI_load_power = S.SPI_power_at_transfer

        S.SPI_evaporation_Li_stop_W_1st = SPI_power_at_IPG_turnon
        S.ramp_duration_transfer_SPI_ms = (SPI_power_at_IPG_turnon/S.SPI_load_power)*total_ramp_time_ms
        S.ramp_duration_cooling_SPI_ms = total_ramp_time_ms-S.ramp_duration_transfer_SPI_ms
    
    ########################
    ## Evaporation in IPG ##
    ########################
    
    # Either we have a recycled trap or we have a cross trap with the 0th order from first AOM. choose!
    
    S.bool_recycled_IPG = 0
    S.bool_evaporative_cooling_IPG = 0   
    S.Li_IPG_evap_G = 350#350
        
    ## [WITH recycled beam] ##

    S.IPG_evap_stop_W = 2#2.6#2.6#.5##2.6#2.6 #when boolean 'create molecules' is on
    # Linear
    S.bool_linear_IPG_ramp = 0
    S.wait_linear_ramp_IPG_ms = 10
    S.linear_ramp_duration_ms = 1500
    S.IPG_power_start = S.IPG_power_set_W
    S.IPG_power_stop = 0.5

    # Exponential
    S.bool_exp_IPG_ramp = 0
    S.wait_exp_ramp_IPG_ms = 0
    S.IPG_power_start_exp = S.IPG_power_set_W
    S.IPG_end_exp_ramp_power = .15
    S.exp_ramp_duration_ms = 4500
        
    # Exponential
    S.IPG_power_final_exp = .1# to set time constant
    S.total_exp_ramp_duration_ms = 4500
    # Exponential Timing
    S.tau_ms = -S.total_exp_ramp_duration_ms/(math.log(S.IPG_power_final_exp/S.IPG_power_start_exp))
    S.exp_ramp_duration_ms = -S.tau_ms*math.log(S.IPG_end_exp_ramp_power/S.IPG_power_start_exp)
    
    # Gradient Coil Evap
    S.bool_gradient_evap = 0            # boolean
    S.bool_ramp = 0                    # will perform linear ramp from 0 to max in set time
    S.gradient_coil_current_I = 0       # currrent though coil. 5 A max
    S.gradient_coil_evap_wait_ms = 10    # wait before coil on
    S.gradient_coil_evap_time_ms = 2000    # wait with coil on
    
    ## [WITH 0th AOM beam] ##
    
    # Variables for evaporation into IPG Cross 
    S.bool_evaporate_into_IPG_cross = 0
    S.evap_into_cross_wait_ms = 0.0
    S.IPG_first_arm_first_evap_into_cross_start_power_W = S.IPG_power_set_W #if done after exp evap ramp then set to S.IPG_end_exp_ramp_power value (line 385 or around)
    S.IPG_first_arm_evap_into_cross_power_end_W = 0.15         # Final power of first arm after evap.
    S.IPG_second_arm_evap_into_cross_power_end_W = 7.0    # Final power of cross beam after ramp up
    S.IPG_evap_into_cross_duration_ms = 1000       # Total time for evaporation into cross
    S.wait_after_evap_into_cross_with_field_on_ms = 100
    
    # Variables for DUAL IPG Evap 
    # This ASSUMES that the dual ramp starts at the end powers from the evaporation into the cross (above)
    S.bool_cross_IPG_exp_evap = 0  
    S.IPG_first_arm_crossed_exp_ramp_final_power = .15   # used to define time constant ONLY
    S.total_cross_exp_ramp_duration_ms = 3000            # used to define time constant ONLY
    S.IPG_first_arm_cross_evap_ramp_stop_power = .15#.4#.2#1. #0.2                         # Actaul Stop Power of first beam
    S.IPG_second_arm_cross_evap_ramp_stop_power = .1#.3#.3#.5   #0.5            # Actual stop power of cross beam
    S.wait_after_cross_evap_ms = 100
    
    if S.bool_cross_IPG_exp_evap:
        S.cross_tau_ms = -S.total_cross_exp_ramp_duration_ms/(math.log(S.IPG_first_arm_crossed_exp_ramp_final_power/S.IPG_first_arm_evap_into_cross_power_end_W ))
        S.IPG_cross_exp_ramp_duration_ms = -S.cross_tau_ms*math.log(S.IPG_first_arm_cross_evap_ramp_stop_power /S.IPG_first_arm_evap_into_cross_power_end_W)
    

    # Temp Hold Time for ODT Osc.
    S.hold_us = 1
    S.period_us = 1000
    
    #########################
    ## Things to do in IPG ##
    #########################
    
    # Flash IPG Off/On
    S.bool_flash_IPG = 0
    S.Li_flash_time_us = 10    # so IPG is OFF for half this time
    S.Li_duration_ms = 100
    
    # Create molecules?
    S.bool_create_molecules = 0
    S.Li_molecule_field_G = 350#680#759#809#759
    S.gradient_coil_create_mol_I = -1.43# -1.43 good for 759 G. sets gradient coil to reduce gradient at Li_molecule_field_G for evaporation
    S.Li_molecule_wait_ms = 10
    
    
    # Feshbach Variables
    S.bool_IPG_cross_FB = 0
    S.FB_wait_ms = 50
    
    # Spin Cleanup
    # Uses HF Imaging setup, occurs after PA_B_Field_Change
    S.bool_Li_spin_cleanup = 0
    # S.Li_spin_cleanup_AOM_F = 100.0 #|1> state
    # S.Li_spin_cleanup_AOM_amp = .15
    S.Li_spin_cleanup_AOM_F = 60.0 # |2> state
    S.Li_spin_cleanup_AOM_amp = .15
    S.Li_spin_cleanup_wait_ms = .1
    
    # Photassociation (See Below)
    # Li MW Transfer (See Below)
    # Second Arm MOD (See Below)    # Ramp Up to Break Molecules
    
    # Tweezer Modulation Variables [Trap Freq. Measurements] 

    S.bool_IPG_mod = 0                       # boolean variable to modulate IPG trap
    S.mod_offset_W = 2
    S.IPG_mod_amplitude_W = S.mod_offset_W*.02               # amplitude of modulation in W
    S.mod_freq_kHz = 10                    # frequency of modulation in kHz                   # offset of IPG AO used during modulation. Do not set > 1.5V.
    S.mod_time_ms = 200                        # time for modulation. occurs in last 'S.mod_time_ms' of hold time. S.mod_time_ms > S.hold                 
    S.mod_wait_ms = 10                            #time to hold trap  
    
    # Sinewave Output with  Stanford Research Function Generator used to modulate RF power (Added by W.Bowden 18/10/13)
    S.bool_set_DS345_sinewave_parameters = 0
    S.DS345_frequency = 1 #sinewave frequency in khertz
    S.DS345_amplitude = 0  #sinewave peak to peak amplitude in V
    DS345_amplitude_memory=0;
    S.DS345_offset = 0 #sinewave offset amplitude in V
    S.DS345_mod_time = 30000 #modulation time in ms 
    S.bool_modulation_after_IPG_ramp_up = 0
    S.freq_mod_IPG_ramp_up_power = 0.1
    
    # Ramp Up to Break Molecules
    
    # [With 0th Order]
    S.bool_cross_IPG_adiabatic_ramp_up = 0
    S.adiabatic_cross_IPG_ramp_up_wait_ms = 50
    S.adiabatic_cross_IPG_first_arm_ramp_up_stop = 5.
    S.adiabatic_cross_IPG_second_arm_ramp_up_stop = 5.
    S.adiabatic_cross_IPG_ramp_up_duration_ms =500
   
    # [With recycled trap]
    S.bool_adiabatic_IPG_ramp_up = 0
    S.adiabatic_IPG_ramp_up_wait = 10
    S.adiabatic_IPG_ramp_up_stop = 5
    S.adiabatic_IPG_ramp_up_duration_ms = 200
    S.bool_disable_field_before_ramp = 0
    S.mag_field_adiabatic_ramp_G = 770

    # Timing
    # Standard
    S.wait_ramp_IPG_ms = 0

    ###############################################################################
    ## Tweezer Modulation Variables [Trap Freq. Measurements] for second IPG arm ##
    ###############################################################################
    S.bool_IPG_second_arm_mod = 0
    S.IPG_second_arm_mod_wait_ms = 100
    S.IPG_second_arm_mod_time_ms = 1000
    S.IPG_second_arm_freq_kHz = 1
    S.IPG_secomd_arm_mod_amp_W = 0.25
    S.IPG_second_arm_offset_W = 4.5
'''
=============================
        Li MW-Transfer
=============================
'''
S.bool_Li_mw_transfer = 0               # boolean variable for MW-transfer
S.Li_mw_amplitude = 1#.3
S.wait_Li_mw_transfer_ms = 10                   # time in tweezer before MW-transfer
# S.Li_mw_start_dF = -228.205+80+2.25-35*1e-3#-10*1e-3        # start dF in MHz from 228Mhz for MW-transfer
# S.Li_mw_end_dF   = -228.205+80+2.25-35*1e-3    # end dF in MHz from 228Mhz for MW-transfer
span=1.0
S.Li_mw_start_dF = -228.205+80-3.9+(47.0 - 0.5*span)*1e-3      # start dF in MHz from 228Mhz for MW-transfer
S.Li_mw_end_dF   = -228.205+80-3.9+(47.0 + 0.5*span)*1e-3
S.Li_mw_scan_dur_s = 1.0                      # duration of MW-scan (holdtime) in s
S.Li_mw_tot_time_s = 0.0
Bfield_angle = 90
negative_pumping = 1
S.compx_offset = 0.12#0.160
S.compy_offset = 0.12#0.198
S.compz_offset = 0.075#-1.115
S.bool_skip_Li_mw_xfer = 0
S.bool_mw_pump_back_up = 0     #RF pulse pumping from lower ground state to the upper ground state. Default from +1/2 up
S.bool_Li_pumpdown = 0         #opens the pump shutter to pump atoms to +-1/2 in the ground state 
S.bool_repeat_mw_pump = 0       #repeats RF pumping done by Li_mw_transfer, to check if the considered state was cleaned

S.Li_mw_pump_back_up_dF = 1.490
S.Li_pumpdown_ampl = 0.008#.045
S.Li_pumpdown_dF = 0#0          
'''
=============================
        Li PA and STIRAP
=============================
'''

S.bool_STIRAP = 0
S.bool_DS345_pulse_sequence = 0
S.bool_RF_STIRAP = 0                 # if on, RF spec. takes place during "STIRAP", and time is conrolled by RF pulse length. this isnt confusing at all...
S.bool_RSTIRAP = 0
S.reverse_STIRAP_delay_us = 0    # 1.5us + time entered here....

###############################
### General Li PA Variables ###
###############################
S.bool_write_Wavemeter = 0          # Needs to be on to write frequency data to a text file!! Necessary for runs with either TS 
S.bool_read_freq_TS1_comb = 0       # read out TS1 when using ratchet lock
S.bool_PA_TS2_comb = 0                # for PA with the TS2, the rep rate changes 
S.bool_read_freq_TS1_wavemeter = 0    #for PA when locked to the cavity and only wavemeter's readout is saved
S.comb_offset_gain = 'negative'  # moves left, -ve gain; moves right, +ve gain;
S.beatnote = 345.400        #beatnote for PA with either of TSs, should always be postive.  
# S.beatnote = -659.03       #beatnote for PA with either of TSs      
#--------------------------------------------- these are just placeholders. changing them wont do anything ---------
S.error_signal_inversion = 1  #zero for negative, 1 for positive, ONLY for TS1
S.TS1_aom_freq = 84.5#98#103.75       #ONLY for TS1
S.bool_change_inversion = 0
S.n_comb_tooth = 0
S.deltaf = 0
#--------------------------------------------------------------------------------------------------------------------

S.PA.scan_duration_ms = 2000#2.9*1e-3          # duration in ms of the scan when S.bool_scan_TS1_aom on ,there is a built in time min of 2.1 us, so set time is what you want  MINUS 2.1 us ## 

S.TS1_main_AOM_amplitude = 0.235
S.TS2_main_AOM_amplitude = 0.04
S.pulse_on_time_us = 1*1e6#37.9#22.9#2.9# # there is a built in time min of 2.1 us, so set time is what you want  MINUS 2.1 us ## 
        
## temp
S.change_ts1_aom = 0

####################################
### PA Scan variables TS1 Cavity ###
##################################2##

S.bool_scan_TS1_cavity = 0        # Boolean for changing external voltage to TS1 to scan frequency
S.PA.TS1_voltage = 0
S.PA.scan_dt_ms= 0.025                    # minimum time step size (ms)  THIS IS IN RB SECTION. NOT USED FOR LI

# Option to scan multiple frequencies
S.bool_scan_multiple_freq = 0
S.number_of_freq = 1
S.step_size_V = .002

# Option to modulate IPG off/on
S.bool_modulate_ipg_off_and_on = 0      # Boolean for modulating the IPG off/on during PA. 
S.freq_IPG_off_on_modulation_kHz = 25
S.duration_IPG_off_on_modulation_ms = S.PA.scan_duration_ms

################################
## PA Scan variables TS1 AOM ###
################################
S.bool_scan_TS1_aom = 0
S.bool_single_color_fixed_PA = 0
S.frep = 125.608
S.aom_lock = 75.0           # where the default lock position is. this should be FIXED. 
S.aom_start = 95.5          # aom freq where the current run is starting.
S.inversion_set = 0        # inversion setting for the start of the run

###################################
### PA Scan variables with Comb ###
###################################
S.bool_set_freq_comb =0     # allows program to change the rep rate of the comb. for single color PA
S.tooth_number = 666 # do not need to change this (not used)
S.HP_freq_synth_freq = 376.8178280
HP_freq_synth_freq_start = 376.8178280
S.f_TiSapph2 = 371598.920835 #TS2 frequency used in experiments involving two lasers
#TS1 =  372782.804546
S.bool_2color_PA = 0 # when this is on the PA with the comb section doesn't do anything except saving counters' readouts
S.bool_PA_with_shutter_closed = 0 #this is to test PA with comb such that the shutter doesn't open



#######################################
### PA at Magnetic Field Variables ####
#######################################
# option to do PA at some magnetic field, changes just before PA shutter opens
# this also sets the comp coils to the zero offset value (see Li MW section)
S.bool_PA_Bfield_change = 0
S.compx_PA = 0#0.12
S.compy_PA = 0#0.12
S.compz_PA = 0#0.075

S.after_cross_evap_wait_ms = 100 #waits after magnetic field is changed for PA
S.PA_gauss =750#759      # limits ps for FB search. Changed to this value BEFORE IPG EVAP INTO CROSS COMMAND

'''
=============================
            Imaging
=============================
'''
########################################
## Li Pixelink Flourescence Variables ##
######################################## 

S.Li6.bool_pixelink_flourescence_imaging = 0

S.Li6.coil_PL_fl_A = 8
S.Li6.compx_PL_fl = 0
S.Li6.compy_PL_fl = 0
S.Li6.compz_PL_fl = 0
S.Li6.pump_PL_fl_amplitude = 0.3
S.Li6.pump_PL_fl_F = -15
S.Li6.repump_PL_fl_amplitude = 1
S.Li6.repump_PL_fl_dF = -15

S.Li_PL_fl_imaging_delay_ms = 10   # used for FL of dipole trap
if S.Li6.bool_pixelink_flourescence_imaging:
    S.Pixelink.expTime_ms = 10#50              # NOTE: Make sure hold time is > Exposure Time+20ms

########################################
## Rb Pixelink Flourescence Variables ##
########################################

S.Rb85.bool_pixelink_flourescence_imaging = 0

S.Rb85.coil_PL_fl_A = 2.5 #2.5
S.Rb85.compx_PL_fl = 0
S.Rb85.compy_PL_fl = 1.7#-.5 #-0.25 #5
S.Rb85.compz_PL_fl = 0
S.Rb85.pump_PL_fl_F = -15 #-20
S.Rb85.repump_PL_fl_dF = 0 #-20
S.Rb85.pump_PL_fl_amplitude = 1

S.Li_PL_fl_imaging_delay_ms = 10   # used for FL of dipole trap
if S.Rb85.bool_pixelink_flourescence_imaging:
    S.Pixelink.expTime_ms = 10             # NOTE: Make sure hold time is > Exposure Time+20ms

###################################
##Li High Field Imaging Variables##
###################################

S.bool_high_field_imaging = 0
S.high_field_imaging_field_G = 750.0
S.gradient_coil_hfield_imag_I = 0

# High Field Imaging at 750G
# To Image |2>, ADF = 1231, BN = 1136
# S.Li6.high_field_abs_F = 60
# S.Li6.high_field_abs_amplitude = 0.15

# To Image |1>, ADF = 1231, BN = 1136
S.Li6.high_field_abs_F = 100
S.Li6.high_field_abs_amplitude = 0.15

# High Field Imaging at 350G
# |1>
# S.Li6.high_field_abs_F = 106
# S.Li6.high_field_abs_amplitude = 0.125

# |2>
# S.Li6.high_field_abs_F = 68
# S.Li6.high_field_abs_amplitude = 0.090

##########################
## Absorption Variables ##
##########################

S.Li6.pump_abs_amplitude = .19
S.Li6.repump_abs_amplitude = 1
S.Li6.pump_abs_dF = 0
S.Li6.repump_abs_dF = 0

###########################
##       Expansion       ##
###########################

if (S.Li6.bool_pixelink_flourescence_imaging and S.bool_Li) or (S.Rb85.bool_pixelink_flourescence_imaging and S.bool_Rb):
    S.bool_absorption_imaging = 0          # boolean variable for absorption imaging
    S.bool_fluorescence_imaging = 0        # boolean variable for fluorescence imaging
else:
    S.bool_absorption_imaging = 1          # boolean variable for absorption imaging
    S.bool_fluorescence_imaging = 0        

S.Rb85.repump_abs_ampl = 1
S.Rb85.pump_abs_dF =0
S.pump_ms = .01

S.bool_pump_imaging = 0
S.bool_pump_imagine_IPG_axis = 0
S.bool_pump_imaging_in_odt = 0

if (S.bool_Rb and S.bool_absorption_imaging) and not (S.Rb_MOT_stark_shift_detection or S.Rb85.bool_pixelink_flourescence_imaging):
    S.expansion_ms = 0.0                 # time of ballistic expansion in ms
    S.Pixelink.expTime_ms = .08
else:
    S.expansion_ms =0.0             # time of ballistic expansion in ms
    if not (S.Li6.bool_pixelink_flourescence_imaging or S.Rb_MOT_stark_shift_detection or S.Rb85.bool_pixelink_flourescence_imaging):
        S.Pixelink.expTime_ms = .05
        S.Pixelink.expTime_ms_override = 1

############################
## PixelLink ROI Settings ##
############################

if S.bool_tweezer_load and not S.Li6.bool_pixelink_flourescence_imaging:
    if S.bool_IPG or S.bool_SPIPG:
        S.Pixelink.ROI_left = 408    
        S.Pixelink.ROI_top = 376
        S.Pixelink.ROI_width = 848
        S.Pixelink.ROI_height = 168
        S.Pixelink.image_detail_width = 760
        S.Pixelink.image_detail_height =45
        S.Pixelink.image_detail_centre_x = 820
        S.Pixelink.image_detail_centre_y = 444
    
    if S.bool_SPI or S.bool_dual_SPIxfer:
        
        ## Good for Li SPI at High Powers (LARGE ROI)...
        if not S.bool_SPIPG_transfer:
            S.Pixelink.ROI_left = 312#200#16      
            S.Pixelink.ROI_top = 556#24 
            S.Pixelink.ROI_width = 760#1240 648
            S.Pixelink.ROI_height = 232#968
            S.Pixelink.image_detail_width = 670
            S.Pixelink.image_detail_height =60
            S.Pixelink.image_detail_centre_x = 650#650#610
            S.Pixelink.image_detail_centre_y = 630#640#610#630  
            # S.Pixelink.ROI_left = 312#200#16      
            # S.Pixelink.ROI_top = 556#24 
            # S.Pixelink.ROI_width = 760#1240 648
            # S.Pixelink.ROI_height = 232#968
            # S.Pixelink.image_detail_width = 650
            # S.Pixelink.image_detail_height = 60
            # S.Pixelink.image_detail_centre_x = 700#650#610
            # S.Pixelink.image_detail_centre_y = 640#610#630      


        ## Good for Li SPI at High Powers (CROSS ROI)...
        # S.Pixelink.ROI_left = 264#16      
        # S.Pixelink.ROI_top = 512#24 
        # S.Pixelink.ROI_width = 704#1240 648
        # S.Pixelink.ROI_height = 256#968
        # S.Pixelink.image_detail_width = 560
        # S.Pixelink.image_detail_height =60
        # S.Pixelink.image_detail_centre_x = 630
        # S.Pixelink.image_detail_centre_y = 645   
          

        ## LiRb IPG Cross at Low Powers
        else:
            print "\n\n\n"
            print "This is running!"
            print "\n\n\n"
            S.Pixelink.ROI_left = 456#192#16      
            S.Pixelink.ROI_top = 590#540#24 
            S.Pixelink.ROI_width = 400#824#1240 648
            S.Pixelink.ROI_height = 144#256#968
            S.Pixelink.image_detail_width = 150#60#560
            S.Pixelink.image_detail_height =60
            S.Pixelink.image_detail_centre_x = 650#678#592
            S.Pixelink.image_detail_centre_y = 630#640  

            # S.Pixelink.ROI_left = 312#200#16      
            # S.Pixelink.ROI_top = 556#24 
            # S.Pixelink.ROI_width = 760#1240 648
            # S.Pixelink.ROI_height = 232#968
            # S.Pixelink.image_detail_width = 650
            # S.Pixelink.image_detail_height =60
            # S.Pixelink.image_detail_centre_x = 700#650#610
            # S.Pixelink.image_detail_centre_y = 640#610#630      

        ## LiRb IPG Cross at Low Powers, with HF imag.
        # S.Pixelink.ROI_left = 296#16      
        # S.Pixelink.ROI_top = 536#24 
        # S.Pixelink.ROI_width = 592#1240 648
        # S.Pixelink.ROI_height = 256#968
        # S.Pixelink.image_detail_width = 50#560
        # S.Pixelink.image_detail_height =40
        # S.Pixelink.image_detail_centre_x = 611
        # S.Pixelink.image_detail_centre_y = 626    


elif S.bool_tweezer_load and S.Li6.bool_pixelink_flourescence_imaging:
    # For Li
    S.Pixelink.ROI_left = 0#272      
    S.Pixelink.ROI_top = 0#304
    S.Pixelink.ROI_width = 1280#736
    S.Pixelink.ROI_height = 1024#720
    S.Pixelink.image_detail_width = 400
    S.Pixelink.image_detail_height =400
    S.Pixelink.image_detail_centre_x = 600
    S.Pixelink.image_detail_centre_y = 500

    S.Pixelink.ROI_left = 424#288#272      
    S.Pixelink.ROI_top = 440#290#304
    S.Pixelink.ROI_width = 296#496#736
    S.Pixelink.ROI_height = 296#496#720
    S.Pixelink.image_detail_width = 400
    S.Pixelink.image_detail_height =400
    S.Pixelink.image_detail_centre_x = 400
    S.Pixelink.image_detail_centre_y = 400

else: 
    # For Rb
    S.Pixelink.ROI_left = 0      
    S.Pixelink.ROI_top = 300 
    S.Pixelink.ROI_width = 736
    S.Pixelink.ROI_height = 720
    S.Pixelink.image_detail_width = 360
    S.Pixelink.image_detail_height =40
    S.Pixelink.image_detail_centre_x = 635
    S.Pixelink.image_detail_centre_y = 524 

    # For Li
    S.Pixelink.ROI_left = 0#272      
    S.Pixelink.ROI_top = 0#304
    S.Pixelink.ROI_width = 1280#736
    S.Pixelink.ROI_height = 1024#720
    S.Pixelink.image_detail_width = 400
    S.Pixelink.image_detail_height =400
    S.Pixelink.image_detail_centre_x = 600
    S.Pixelink.image_detail_centre_y = 500    
'''
=============================
        Experiment
=============================
'''
S.foldername ='test'
S.sequence_list=[]
S.reference_settings = ['S.compx_load= 0', 'S.compz_load=0']
S.plotvalue = ''
S.legendlabel = '.'
S.plotcolor = 'g'
S.marker = 'd'

#S.Li6.compx_cool_SPI = 0, # 0.2,
#S.Li6.compy_cool_SPI = 0, # 2.0,
#S.Li6.compz_cool_SPI = 0, # 0.1,#.14,#.11,

#S.list1=[0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.5,2,2.5,3,4,5,10,15,20,30,60,90] 
#S.list1 = range(1)

#For x= 0: y= 0  , z= 0
#For x=-1: y=-0.5, z=-0.15
#For x=-2: y=-0.8,   z=-0.125

#S.list1 = linspace(-1.,1,20)#linspace(-0.25,0.25,5)#linspace(-1,1,5)
#pump_A,pump_dF,repump_A,repump_dF = [0.163,-4.5,0.16,-4.5] -->~800k

################################################

# S.Li6.pump_compress_amplitude = 0.4
# S.Li6.repump_compress_amplitude = 0.4
# S.Li6.pump_compress_dF = -30
# S.Li6.repump_compress_dF = -30

# S.Li6.pump_cool_amplitude = 0.14#0.163#0.11
# S.Li6.repump_cool_amplitude = 0.16#0.12
# S.Li6.pump_cool_dF = -4
# S.Li6.repump_cool_dF = -4

# S.Li6.compy_cool_SPI = -1.0 #2016_05_10
# S.Li6.compx_cool_SPI = 0.25 #2016_05_10

# S.Li6.compz_compress_SPI = 0.5 #2016_05_11 


# S.Li6.mot_cool_ms = 3
# S.Li6.tweezer_load_Li_ms = 15
# S.Li6.ODT_Bfield_stabilization_time_ms = 30
# S.expansion_ms = 0.1
# S.list1 = [5,10,15,20]# S.list1 = 15

################################################

# min_par=1
# max_par=50
# log_par_space = linspace(log(max_par),log(min_par),60)
# S.list1 = exp(log_par_space)
# S.list1 = arange(0,1,.05)
#S.list1 = arange(-0.2,0,0.01)
#25 looked good -- Here now
# At 21 now

S.list1 = arange(10)

for t in range(len(S.list1)):
    if S.stop_file_exists(remove=False):
        break
    #S.Li6.pump_cool_dF = S.list1[t]
    #S.Li6.loadmot_s = S.list1[t]
    # S.SPI_evaporation_Li_stop_W_1st = S.list1[t]
    # S.ramp_duration_cooling_SPI_ms = ((51-S.list1[t])/50.0)*2000.
    # # S.IPG_evap_stop_W = S.list1[t]    
    # S.expansion_ms = S.list1[t]
    # S.Li6.compx_cool_SPI = S.list1[t]
    # S.Li6.tweezer_load_Li_ms = S.list1[t]
    # S.Li_hyperfine_pump_us = S.list1[t]
    # S.Li6.compy_cool_SPI = S.list1[t]
    # S.Li6.compy_compress_SPI = S.list1[t]
    # S.Li6.pump_compress_amplitude = S.list1[t]
    # S.Li6.repump_compress_amplitude = S.list1[t]
    # S.Li6.pump_compress_dF = S.list1[t]
    #S.Li6.repump_compress_dF = S.list1[t]
    # S.Li6.compy_cool_SPI = S.list1[t]
    #S.Li6.pump_cool_amplitude = S.list1[t]
    # S.Li6.repump_cool_amplitude = S.list1[t]
    #S.Li6.pump_cool_dF = S.list1[t]
    #S.Li6.repump_cool_dF = S.list1[t]
    #S.Li6.coil_compress_I = S.list1[t]
    #S.Li6.compy_cool_SPI = S.list1[t]
    #S.Li_hyperfine_pump_us = S.list1[t]
    #S.Li6.compz_cool_SPI = S.list1[t]
    savesettings = dict(suffix=S.foldername,camerasuffix = '%.6f' %S.list1[t],tekscope=S.TekScope.bool_read_out_tek_scope) # 1d
    print '/n==================================='
    print   'Current List Value = %F'%S.list1[t]
    print '/n==================================='
    S.run_recipe(**savesettings)
    S.save(**savesettings)

execfile('C:/UTBus_Recipesb/tool_scripts/shutdown.py')
S.stop_file_exists(remove=True)
#