"""
"""
import os
import os.path

bus_driver_path = r"C:\UTBUS\V1\BusDriver\bin\Release\bus_driver_v1.exe"
state_folder = r"C:\Temp\UTBUS\state"
bytecode_folder = r"C:\Temp\UTBUS\bcode"

for d in (state_folder,bytecode_folder):
    if not os.path.isdir(d):
        os.makedirs(d)
        
Hz = 1
kHz = 1000*Hz
MHz = 1000*kHz
GHz = 1000*MHz

COMPCOIL_COVERSION_V_PER_A = 2.0

zeeman_coil_current_calib = {
    "COIL1"   : {
            "SLOPE_V_PER_A" :    0.2,
            "intercept"    :    -0.001 }, 
    "COIL2"   : {
            "SLOPE_V_PER_A" :    0.204,
            "intercept"    :    -0.001 }, 
    "COIL3"   : {
            "SLOPE_V_PER_A" :    0.3356,
            "intercept"    :    -0.0016 }, 
    "COIL4"   : {
            "SLOPE_V_PER_A" :    0.3339,
            "intercept"    :    -0.0007 }, 
    "COIL5"   : {
            "SLOPE_V_PER_A" :    0.5041,
            "intercept"    :    -0.0011 }, 
    "COIL6"   : {
            "SLOPE_V_PER_A" :    0.504,
            "intercept"    :    -0.0007 }, 
    "COIL7"   : {
            "SLOPE_V_PER_A" :    0.7557,
            "intercept"    :    -0.0021 }, 
    "COIL8"   : {
            "SLOPE_V_PER_A" :    0.7542,
            "intercept"    :    -0.0009 }, 
    }

# this is the internal reference sampling rate of all DDSes
DDS_reference_sampling_rate = 20*MHz

bus_address = {
    # master setup
    "master_dds" : 48,
    "utbus_external_clock_dds" : 28,
    "brunette" : 16,
    "blonde" : 40,
    "Li" : 8,
    "jet_black" : 32,
    "dirty_blonde" : 56,

    # mat setup
    "mat_repump" : 124,
    "mat_cooling" : 136,
    }

master_DDS_params = {
    "ampl" : 0.7,
    "freq" : 15*MHz,
    "refclock" : 10*MHz,
    }

utbus_external_clock_DDS_params = {
    "ampl" : 0.7,
    }

lock_DDS_params = {
    "brunette" : {"f0" : 94*MHz,
                  "df" : 14*MHz,
                  "D" : 1.0/(2.0*.177*MHz),
                  "ampl" : 0.7},
    "blonde" : {"f0" : 103*MHz, 
                "df" : 5*MHz,
                "D" : 1.0/(2.0*.177*MHz),
                "ampl" : 0.7},
    "Li" : {"f0" : 100*MHz, #change to -100 for new setup 20091010# this wuz 88 as of 02/02/2009
            "f1" : 108*MHz, #AOM1 shift freq for second TA
            "df" : 5*MHz,
            "D" : 1.0/(2.0*.177*MHz),
            "ampl" : 1.0},
    "dirty_blonde" : {"f0" : 122.25*MHz,
                      "df" : 8*MHz,
                      "D" : 1.0/(2.0*.177*MHz),
                      "ampl" : 0.7},
    "jet_black" : {"f0" : 103.7*MHz,
                   "df" : 13*MHz,
                   "D" : 1.0/(2.0*.177*MHz),
                   "ampl" : 0.7},
    "LiSS" : {"f0" : .8*MHz,
              "df" : 5*MHz,
              "D" : 1.0/(2.0*.177*MHz),
              "ampl" : 0.7},
    }

                  
