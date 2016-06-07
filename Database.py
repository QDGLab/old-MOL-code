"""
This is a database of devices. The name of each device is unique in 
the QDG Lab.

experiment_devices maps experiment name to a dict that contains
all the devices used by that experiment. The devices fall in one 
of the following categories: 
  - DDS : address
  - DO (DigitalOutput) : (address,port)
  - AO (AnalogOutput) : address

The specialized Recipe has an instance with the same name for 
all the DDS and AO devices. The DO devices become functions which
accept a single argument treated as a bool (0 or 1). 
"""
__all__ = ['experiment_devices']

__MOL_devices = {
    'DDS' : {
        ## Top Rack LtoR
        'Rb_pump' : 20,
        'Li_pump' : 152,
        'Li_repump' : 156,
        'Rb_repump': 160,
        'Rb_zeeman_slower': 164,
        'RbSS_ref': 36, #168 
        'ipg_AOM_driver_input': 172,
        'TiSapph1_comb_lock_AOM': 88, #176
        
        ## Bottom Rack LtoR
        'TS2_main_AOM':120,
        'TS1_main_AOM':176,  #88
        # 'IPG_cross': 140,   ### can be removed
        'LiSS': 140, #36
        'Li_imaging': 128,
        'Li_zeeman_slower': 64,
        'SPI_AOM': 124
    },

    'DO' : {
    
        ## SRS Shutters
        'srs_main_optical_pump_shutter' : (251,0), # main optical pumping shutter using new SRS shutters
        'srs_optical_depump_shutter' : (251,9), # optical depumping pumping shutter using new SRS shutters
        'mol_tisapph_srs_shutter' : (251,10),
        
        ## iPod Shutters Rack 1
        'Li_MOT_shutter' :(251,1),                          # TTL 1 | NEW Li MOT Shutter             
        'Zeeman_Slower_shutter' :(251,2),                   # TTL 2 | NEW Zeeman Slower Shutter
        'Li_repump_abs_shutter' : (251,3),                  # ttl 4 | NEW Li repump abs. shutter 
        'Li_pump_abs_shutter' : (251,4),                    # TTL 4 | NEW Li pump abs. shutter
        'Li_HF_imaging_shutter': (251,8),                   # TTL 8 | NEW Li Hight Field Imaging Shutter


        'Rb_MOT_repump_shutter' : (251,5),                  # TTL 5 | Rb. MOT repump shutter
        'Rb_abs_shutter': (251,13),
        'Li_pump_shutter' : (251,6),                        # TTL 6 | Li MOT pump shutter  shutter
        'Li_slowing_beam_shutter' : (251,7),                # TTL 7 | Li slowing beam shutter
        'Li_HF_imaging_shutter': (251,8),                       # TTL 8 | Li MOT repump shutter
    
        ## Other Shutters
        'LiRb_mot_shutter' : (251,15),
        'Rb_repump_shutter' : (251,14),   
        # 'Li_repump_abs_shutter' : (251,13), 
        
        ## Misc.
        'lockbox_ttl' : (252,13),  # TTL signal for TiSaph lockbox
        'atom_shutter' : (251,11), # switch for the atom shutter.
        'TS1_error_signal_invert': (252,3),
        'apogee_trigger' : (252,7), 
        'mot_coil_HBridge_right' : (252,9),
        'mot_coil_HBridge_left' : (252,8),
        'fat_fiber_shutter' : (252,14),
        'pixelink_trigger' : (252,15),
        'pointgrey_trigger' : (252,4),
        'camera_trigger' : (252,15),
        'Utility_trigger' : (252,6),
        'RbSS_FSK' : (252,0), 
        # 'RbSS_sel' : (252,1),
        'RbSS_switch' : (252,2),
        'repump_shadow_only' : (251,5), #switched from (251,14)
        'spi_mod_control' : (252,12),
        'hv_relay_control' : (252,11),
        'hv_pot_control' : (252,10),
        'TS1_DS345_Trig' : (252,4),
        'TS2_DS345_Trig' : (252,1)
        
        

    },

    'AO' : {
        'hv_supply_voltage_set': 214,
        'comp_coil_x' : 227,
        # 'comp_coil_x_door' : 227, 
        'comp_coil_y_pump' : 224,  
        'comp_coil_y_oven' : 225,  
        'comp_coil_z_top'  : 228,
        'comp_coil_z_bot'  : 229,
        'mot_coil_plus'    : 230,
        'mot_coil_minus'   : 231,
        
        #blank : 224,
        #'gradient_coils' : 225, #curvature coils control
        #blank': 226,
        # 'comp_coil_z' : 227,
        # 'comp_coil_y' : 228,
        # 'comp_coil_x' : 229,
        # 'mot_coil_plus' : 230,
        # 'mot_coil_minus': 231,`0582
        
        'RbSS_setpoint' : 233,
        'spi_voltage_control' : 234,
        #'PA_AOM_amplitude' : 235,   not used-
        'Utility_voltage' : 215,
        'retroMirror_x' : 236,
        'retroMirror_y' : 237,
        'IPG_AOM_analog_in_V' : 208,  # used to be 238
        'fb_coil_supply_current_control' : 210,
        'fb_coil_supply_voltage_control' : 209,
        'TiSapph_scan_output' : 239,
        #'TS2_FM' : 211,
        'IGP_AOM_RF_Level' : 211,
        #zeeman coils: test hack
        'zeeman_coil_1'  : 220, #216
        'zeeman_coil_2'  : 218, #217
        'zeeman_coil_3'  : 219,
        'zeeman_coil_4'  : 221,
        'zeeman_coil_5'  : 217,
        'zeeman_coil_6'  : 223,
        'zeeman_coil_7'  : 216,
        'zeeman_coil_8'  : 222,

        'SPI_intensity_setpoint' : 212,
    },
    
    # Measurement and Control Devices : host should be 10.1.213.7, cause enut7 is better than enut1... 2015-05-27
    'MC' : {
        # 'HP_8663A' : dict(cls='HP_8663A',host='10.1.213.1',port=15000,address=20),#Ethernet previously used by the oscilloscope 
        # 'AC_53132A' : dict(cls='AC_53132A',host='10.1.213.7',port=15000,address = 8), #MUST FIX THE ETHERNUT BEFORE YOU USE THIS - Kahan 20150812
    },
}

experiment_devices = {
    'MOL' : __MOL_devices,
}
