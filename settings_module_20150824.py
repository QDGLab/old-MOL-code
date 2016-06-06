#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2009.06.12 by Bruce Klappauf
- Added 'camera_labels' option for 'filenames' keyword for the camera image saving.
- Changed name of 'check_stop' function to 'stop_file_exists' to make it more intuitive to use.

2009.11.05 by bruce klappauf
- changed save function so that it correctly attaches subsuffix to the sequence_dir
- annotated create_path function a little better.
2009.11.16 by bruce klappauf
- try to fix bug where suffix could not be added to folder if root existed.  seems to work.

- 20100311_0 bruce added another general dict to settings file because it seems each dict can 
        only have 256 entries. This settings module was updated to unpack this dict as well.
        we now have general_1 and general_2.
"""
#standard library imports
import socket                   #for apogee
import time                     #for timestamp
import os                       #for path operations
import sys                      #for args
import numpy                    #for some math/array functions
from PIL import Image
from inspect import ismethod    #for making list of attributes and methods
from shutil import copyfile
import cPickle                  #for saving settings output as py dictionary
import pylab as py

#3rd party imports
    #None
#local package imports
from UTBus_Recipesb.recipe_libs.PixeLINK import CameraController as Pixelink_Controller
from UTBus_Recipesb.recipe_libs.PixeLINK import FramesHandler
from UTBus_Recipesb.recipe_libs.Apogee import Apogee_controller
# from UTBus_Recipesb.recipe_libs.PointGrey.PointGreyControllerBuilder import PointGreyBuilder
from UTBus_Recipesb.recipe_libs.tekscopes import tekScope_v2 as ts
from UTBus_Recipesb.recipe_libs.PAHardware import PAHardware,AgilentCounter,HP8663Asyn,Wavemeter
from UTBus1.Globals import Hz,MHz,GHz,kHz
#from UTBus_Recipesb.recipe_libs.genetic_algorithm import GeneticAlgorithm

# todo:
# change settings file save to have same suffix options as folders 

#######################################################################################
## Decorators for the Settings Class
#######################################################################################
def not_setting(method):
    '''
    decorator for methods that are not to be included in settings list
    '''
    method.notsetting = True
    return method

#######################################################################################
## Categoriezed Container Classes used in the Settings class
## Special methods are defined in these and the default values are imported from 
## the settings_dict module when Settings is instantiated
#######################################################################################
class Rb85Settings(object):
    """
    use _set_dict for simple values as before or make a method
    for more complex ones
    """
    @not_setting    
    def __init__(self,values):
        for (k,v) in values.items():
            setattr(self,k,v)
        
class Rb87Settings(object):
    """
    use _set_dict for simple values as before or make a method
    for more complex ones
    """
    @not_setting    
    def __init__(self,values):
        for (k,v) in values.items():
            setattr(self,k,v)

class Li6Settings(object):
    """
    use _set_dict for simple values as before or make a method
    for more complex ones
    """
    @not_setting    
    def __init__(self,values):
        for (k,v) in values.items():
            setattr(self,k,v)

class PASettings(object):
    """
    use _set_dict for simple values as before or make a method
    for more complex ones
    relevant numbers for the PA laser are 
    -- f_0              = offset of first comb line
    -- f_rep            = rep rate of comb laser
    -- f_lock           = difference of Actual_PA_f and Locked combline
    -- delta_f_synth    = Desired_PA_f - Actual_PA_f
    """
    @not_setting    
    def __init__(self,values):
        # self.cntr = AgilentCounter()
        # self.meter = Wavemeter()
        # self.synth = HP8663Asyn()
        for (k,v) in values.items():
            setattr(self,k,v)
   
    @not_setting   
    def get_synth_tolerance(self):
        self.synth_tol = self.tolerance_MHz*MHz/float(self.n)
        
    @not_setting   
    def get_frequency(self):
        """
        reads counter to get the beat freq from the comb to get the rep rate and from
        the comb with the freq-doubled comb to get the offset freq.
        this defines the f0 and frep
        -- self.f_rep_      ## rep rete freq = combline separation
        -- self.f_0         ## offset freq of first comb line from 0
        """
        # print '*********in get freq'
        self.cntr.run('FREQ 1')
        f_0_ = self.cntr.get_measurements(1)
        self.f_0 = f_0_[0]
        self.cntr.run('FREQ 2')
        f_rep_ = self.cntr.get_measurements(1)
        self.f_rep = f_rep_[0]
        
    @not_setting   
    def get_combLine(self):
        """
        figures out which comb line the TiSaph is locked to from a wavemeter
        measurement. This usually doesn't change as long as we don't break the lock.
        fcomb = f_0 + n*f_rep
        fpa = fcomb + flock =  f_0 + n*f_rep + flock
        ==>  n = (fpa - flock - f_0)/frep
        f_0 and f_lock actually have sign options as well as shown below
        This sets value:
        -- self.n    ## combline number ~3,000,000
        -- self.synth_tol    ## combline number ~3,000,000
        """
        # print '*********in get comline'
        self.get_frequency()
        ## Wavemeter measurements
        #########################
        f_wavem_ = []
        #averages 20 wavemeter readings
        for nn in range(20): 
            self.meter.set_lambda_units('GHz')  # set measurement unit ('nm', 'GHz' or 'cm')
            lam = self.meter.get_lambda()       # gets the current Wavelength
            if lam > 1:
                f_wavem_.append(lam*1e9)
        f_wavem_avg = numpy.mean(f_wavem_)
        f_wavem = round(f_wavem_avg,0)
        ## calculation of locking mode number
        #####################################
        n = (f_wavem-self.sign_lock*self.f_lock-self.sign_0*self.f_0)/self.f_rep
        self.n = round(n,0)
        self.get_synth_tolerance()
        
        # print 'f_0 = %.0f Hz'%self.f_0
        # print 'f_rep = %.0f Hz'%self.f_rep
        # print 'f_wavem = %.0f Hz'%f_wavem
        # print 'f_lock = %.0f Hz'%self.f_lock
        # print 'n = %.2f'%n
        
    @not_setting   
    def set_frequency(self):
        """
        Given a desired PA freq this calculated the required f_rep needed to move the 
        locked n'th combline to the position to get that freq.
        """
        def move_synth(delta_f_synth):
            sign_delta_f_synth = int(delta_f_synth/abs(delta_f_synth))
            stepsize_Hz = int(10)
            num_steps = int(abs(delta_f_synth)/stepsize_Hz)
            remainder_Hz = round(abs(delta_f_synth)%stepsize_Hz,1)
            self.synth.set_incr(stepsize_Hz, 'Hz')
            for nn in range(num_steps):  # slowly move the synth by delta_f_synth in stepsize steps
                self.synth.walk(sign_delta_f_synth)
                time.sleep(0.1)
            self.synth.set_incr(remainder_Hz, 'Hz')
            self.synth.walk(sign_delta_f_synth)
            time.sleep(0.1)
        
        def get_delta_f_synth():
            #get latest f_rep,f_0
            self.get_frequency()  
            #calculate required f_rep to get desired PA_freq.  switches n and frep in above eq.
            f_rep_goal = (self.setfrequency - self.sign_lock * self.f_lock - self.sign_0 * self.f_0) / self.n
            # print 'f_rep_goal = %.0f Hz'%f_rep_goal
            # lock uses 3rd harmonic so synth must be set to *3
            delta_f_synth = (f_rep_goal - self.f_rep)*3  
            delta_f_synth = round(delta_f_synth,1)
            # print 'delta_f_synth = %.1f Hz'%delta_f_synth
            return delta_f_synth
            
        iteration = 0
        delta_f_synth = get_delta_f_synth()
        while abs(delta_f_synth) > self.synth_tol:
            move_synth(delta_f_synth)
            delta_f_synth = get_delta_f_synth()
            iteration += 1
            if iteration > self.max_iteration:
                # print 'REACHED MAX ITERATION: delta_f_synth = %.1f'%delta_f_synth
                break
    
class ApogeeSettings(object):
    """
    use _set_dict for simple values as before or make a method
    for more complex ones.
    ROI settings:
        ROI settings are stored in left,top,w,h values. 2184 x 1472 max. 
        ROI can be changed either by changing one of these or by using 
        setROI(ROI) with a set (L,T,W,H) or setROIcenter(ROIc) with a 
        set (Cx,Cy,W,H). ROI or ROIcenter attributes return the current set.
        init with update the actual camera with the current settings.
        his allows restrictions to be put on ROI settings via setROI
        
        setting the ROIcenter_default in the settings dict will override
        other settings.  
    """
    @not_setting    
    def __init__(self,values):
        #we do not connect the camera here because the server may not be running 
        #if we are doing just absorption images
        self.datafolder = 'apogee_images'
        self.labels = []
        self._imagelist = []
        self.ROIcenter_default = None
        for (k,v) in values.items():
            setattr(self,k,v)
        if self.ROIcenter_default is not None:
            self.setROIcenter(self.ROIcenter_default)
            
    @not_setting    
    def setROI(self,ROI):
        self.ROI_left,self.ROI_top,self.ROI_width,self.ROI_height = ROI
        self.checkROI()
        
    @not_setting    
    def setROIcenter(self,ROIc):
        cx,cy,w,h = ROIc
        # print 'new',cx,cy,w,h
        self.ROI_left = cx-w/2
        self.ROI_top = cy-h/2
        self.ROI_width = w
        self.ROI_height = h
        # print self.ROI
        self.checkROI()
        
    @property
    def ROI(self):
        ROI = (self.ROI_left,self.ROI_top,self.ROI_width,self.ROI_height)
        return ROI
        
    @property
    def ROIcenter(self):
        L,t,w,h = self.ROI
        cx = L + w/2
        cy = t + h/2
        return (cx,cy,w,h)

    @not_setting    
    def checkROI(self):
        self.ROI_left = numpy.clip(self.ROI_left,0,2184)
        self.ROI_top = numpy.clip(self.ROI_top,0,1472)
        self.ROI_width = numpy.clip(self.ROI_width,1,2184-self.ROI_left)
        self.ROI_height = numpy.clip(self.ROI_height,1,1472-self.ROI_top)
        # print self.ROI
        
    @not_setting    
    def label_indices(self,string='image_%i'):
        list =[]
        for i in range(len(self.labels)):
            s = string%i
            try:
                list.append(self.labels.index(s))
            except ValueError:
                break
        return list
        
    @not_setting    
    def start(self,N):
        # should check that the connection works -  otherwise send triggers
        if not hasattr(self,"_Camera"): # if have not instantiated the camera, do so
            self._Camera=Apogee_controller(host = self.HOST)
        self._Camera.getstat()
        self._Camera.set_roi(self.ROI)
        self._Camera.set_trigger_mode(self.triggerMode)
        self._Camera.set_exposure(N=N,time=self.expTime_ms/1000.0,light=1)#starts waiting for N triggers
        self._imagelist = []
        self.N = N
        print 'Apogee camera set: Waiting for %d triggers'%N
    
    @not_setting    
    def stop(self):
        #must get images before stopping
        if hasattr(self,"_Camera"): # if camera connected, close it.
            self._Camera.close()
            del self._Camera

    @not_setting    
    def get_images(self,float=True):
        ims = []
        if float:
            for frame in self.__get_images():
                ims.append(frame.astype('float'))
        else:
            ims = self.__get_images()
        return ims
        
    @not_setting    
    def __get_images(self):
        '''
        called once per run to download images to list.  list is used for all else.
        '''
        if len(self._imagelist) == 0:
            self._Camera.flush_buffer()
            for i in range(self.N):
                    self._imagelist.append(self._Camera.get_array().astype('uint16'))
            self._imagelist.reverse()
        return self._imagelist

    @not_setting    
    def save_image(self,array,fname='image.png'):
        Z=array.astype('int32')
        im = Image.fromarray(Z,mode='I')
        im.save(fname,bits = 16) #I don't think bits=16 actually changes anything
        return fname
        
    @not_setting
    def save_images(self,folder = None,filenamebase = None, filenames = None, data = True,suffix='',**kw):
        if data:
            subfolder = 'apogee_image_data'+suffix
        else:
            subfolder = 'apogee_images'+suffix
        if filenames:
            if len(filenames) < self.N:
                filenames = None
                print 'there were not enough filenames; using default names'
        #get datafolder
        if folder is None:
            d = self.datafolder
        else:
            if os.path.isdir(folder):
                d = folder
            else:
                print "folder %s doesn't exist.  Writing to %s"%(folder,self.data_folder)
                d = self.datafolder
        #get frames and make image data folder
        frames = self.get_images(float=False)
        print "Saving %d images" % len(self._imagelist)
        frames_folder= os.path.join(d,subfolder)
        if not os.path.isdir(frames_folder):
            os.makedirs(frames_folder)
        #write data to files 
        for (i,frame) in enumerate(frames):
            if filenamebase:
                fname = os.path.join(frames_folder,filenamebase%i)
            if filenames:
                fname = filenames[i]
            else:
                if data:
                    fname = 'imagedata_%06d'%i
                else:
                    fname = 'image_%06d'%i
            if data:
                (w,h) = frame.shape
                fpath = os.path.join(frames_folder,(fname+"_%04dx%04d.txt")%(w,h))
                numpy.savetxt(fname,frame,fmt='%d',delimiter=',')
                # print 'IMAGE DATA FILE NAME IS ',fpath
            else:
                fpath = os.path.join(frames_folder,fname+'.png')
                self.save_image(frame,fname = fpath)
                # print 'IMAGE FILE NAME IS ',fpath
        return frames_folder

class PixelinkSettings(object):
    """
    use _set_dict for simple values as before or make a method
    for more complex ones
    ROI settings:
        ROI settings are stored in left,top,w,h values. 1280 x 1024 max. 
        ROI can be changed either by changing one of these or by using 
        setROI(ROI) with a set (L,T,W,H) or setROIcenter(ROIc) with a 
        set (Cx,Cy,W,H). ROI or ROIcenter attributes return the current set.
        init with update the actual camera with the current settings.
        his allows restrictions to be put on ROI settings via setROI
        
        setting the ROIcenter_default in the settings dict will override
        other settings.  
    """
    @not_setting    
    def __init__(self,values): 
        self._Camera = Pixelink_Controller()
        self.datafolder = 'pixelink_data'
        self.labels = []
        self._imagelist = []
        self.ROIcenter_default = None
        for (k,v) in values.items():
            setattr(self,k,v)
        if self.ROIcenter_default is not None:
            self.setROIcenter(self.ROIcenter_default)
            
    @not_setting    
    def setROI(self,ROI):
        self.ROI_left,self.ROI_top,self.ROI_width,self.ROI_height = ROI
        self.checkROI()
    
    @not_setting    
    def setROIcenter(self,ROIc):
        cx,cy,w,h = ROIc
        self.ROI_left = cx-w/2
        self.ROI_top = cy-h/2
        self.ROI_width = w
        self.ROI_height = h
        self.checkROI()
        
    @property
    def ROI(self):
        ROI = (self.ROI_left,self.ROI_top,self.ROI_width,self.ROI_height)
        return ROI
        
    @property
    def ROIcenter(self):
        L,t,w,h = self.ROI
        cx = L + w/2
        cy = t + h/2
        return (cx,cy,w,h)

    @not_setting    
    def checkROI(self):
        self.ROI_left = numpy.clip(self.ROI_left,0,1272)
        self.ROI_left = int(self.ROI_left/8)*8
        self.ROI_top = numpy.clip(self.ROI_top,0,1016)
        self.ROI_width = numpy.clip(self.ROI_width,8,1280-self.ROI_left)
        self.ROI_width = int(self.ROI_width/8)*8
        self.ROI_height = numpy.clip(self.ROI_height,8,1024-self.ROI_top)
        self.ROI_height = int(self.ROI_height/8)*8
       
    @not_setting    
    def label_indices(self,string='image_%i'):
        list =[]
        for i in range(len(self.labels)):
            s = string%i
            try:
                list.append(self.labels.index(s))
            except ValueError:
                break
        return list
             
    @not_setting    
    def start(self,N):
        self.framesHandler = FramesHandler(folder=self.datafolder)
        self._Camera.set_roi(*self.ROI)
        self._Camera.set_exposure_time_ms(self.expTime_ms)
        self._Camera.set_gain(self.gain)
        self._Camera.set_external_trigger()
        self._Camera.start(N,self.framesHandler)
        self._imagelist = []
        self.N = N
        self.framesHandler.N = N
        print 'Pixelink camera set: Waiting for %d triggers'%N

    @not_setting    
    def stop(self):
        self._Camera.stop()
  
    @not_setting    
    def get_images(self,float=True):
        self._imagelist = self.framesHandler.generate_frames_array(float=float)
        return self._imagelist
        
    @not_setting    
    def save_images(self,folder=None,filenamebase=None, filenames=None,data=True,suffix='',**kw):
        self.framesHandler.set_datafolder(self.datafolder)
        self.framesHandler.save_frames(folder = folder,filenamebase = filenamebase,\
                filenames = filenames,data=data,suffix=suffix)
        return self.framesHandler.frames_folder

class PointGreySettings(object):
	
	@not_setting
	def	__init__(self, values):
		self.datafolder = 'pointgrey_data'
		self.labels = []
		self._imagelist = []
		for (k, v) in values.items():
			setattr(self, k, v)
		
	@not_setting
	def start(self, numOfImages):
		updateValues = dict(
							gain = self.gain,
							expTime_ms = self.expTime_ms,
							useROI = self.useROI,			# Use Region of Interest
							useROICenter = self.useROICenter,	# Use Region of Interest based on center point.
							ROI_left = self.ROI_left,
							ROI_top = self.ROI_top,
							ROI_width = self.ROI_width,
							ROI_height = self.ROI_height,
							ROI_center = self.ROI_center,	# (x, y)
							boostFramerate = self.boostFramerate
							)
		self._Camera = PointGreyBuilder(updateValues).buildController()
		self._Camera.setDataBuffers(numOfImages)
		self._Camera.enableHardwareTrigger()
		self._Camera.start()
		print 'Point Grey Camera Set: Waiting for %d triggers' % numOfImages
	
	@not_setting
	def stop(self):
		if hasattr(self,'_Camera'):
			self._Camera.stop()
		
	@not_setting
	def save_images(self,folder=None,filenamebase=None, filenames=None,data=True,suffix='',**kw):
		if data:
			subfolder = 'pointgrey_image_data' + suffix
		else:
			subfolder = 'pointgrey_images' + suffix
		if filenames:
			if len(filenames) < self._Camera.numOfImages:
				filenames = None
				print 'there were not enough filenames; using default names'
        # Get datafolder
		if folder is None:
			d = self.datafolder
		else:
			if os.path.isdir(folder):
				d = folder
			else:
				print "folder %s doesn't exist.  Writing to %s"%(folder,self.data_folder)
				d = self.datafolder
		#get frames and make image data folder
		print "Saving %d images" % self._Camera.numOfImages
		imageFolder= os.path.join(d,subfolder)			
		if not os.path.isdir(imageFolder):
			os.makedirs(imageFolder)
        #write data to files 
		if self.saveData:
			fpathDat = os.path.join(imageFolder,('imagedata_%03d.txt'))
			self._Camera.saveRAWImages(fpathDat)  
			print 'POINT GREY IMAGE DATA SAVED'
		if self.saveImage:
			fpathIm = os.path.join(imageFolder, 'image_%03d.png') 
			self._Camera.savePNGImages(fpathIm)
			print 'POINT GREY IMAGES SAVED'
		fpathLog = os.path.join(imageFolder, 'PGLog.txt')
		self._Camera.saveLog(fpathLog)
		if self.saveImage:
			return imageFolder     
            
class TekScopeSettings(object):
    """
    use _set_dict for simple values as before or make a method
    for more complex ones
    ROI settings:
        ROI settings are stored in left,top,w,h values. 1280 x 1024 max. 
        ROI can be changed either by changing one of these or by using 
        setROI(ROI) with a set (L,T,W,H) or setROIcenter(ROIc) with a 
        set (Cx,Cy,W,H). ROI or ROIcenter attributes return the current set.
        init with update the actual camera with the current settings.
        his allows restrictions to be put on ROI settings via setROI
        
        setting the ROIcenter_default in the settings dict will override
        other settings.  
    """
    @not_setting    
    def __init__(self,values,settings_dict = 'settings_dict'):
        for (k,v) in values.items():
            setattr(self,k,v)
        self.storage={}
    
    @not_setting 
    def start(self):
        self.T = ts.TekScope(host = self.SCOPEHOST, port = 15000, address = 1)
        self.T.send_request('TRIG:STATE?')
        self.ans = self.T.get_reply()
        print 'Connection Established. Current Trigger State:', self.ans
    
    @not_setting 
    def stop(self):
        self.T.close()
     
    @not_setting
    def invert_channel(self,channel):
        self.channel = channel
        self.T.send_request('%s:INV ON'%self.channel)
        print '%s Invert ON'%self.channel
    
    @not_setting 
    def reset_single_seq_trigger(self):
        self.T.send_request('HOR:TRIG:POS 0')
        self.T.send_request('TRIG:A:MOD NORM')
        self.T.send_request('ACQ:STOP SQE')      # stop after single trigger event
        self.T.send_request('ACQ:STATE RUN')     # set scope to accept triggers
        self.T.send_request('TRIG:STATE?')
        self.ans = self.T.get_reply()
        print 'Trigger State Reset. Current Trigger State:'
        print self.ans
    
    @not_setting
    def turn_on_channel(self,channel):
        self.channel = channel
        self.T.send_request('SEL:%s ON'%self.channel)
        print '%s turned on'%self.channel
    
    @not_setting
    def reset_auto_trigger(self):
        # self.channel = channel
        self.T.send_request('TRIG:A:MOD AUTO')
        self.T.send_request('ACQ:STATE RUN')     # set scope to accept triggers
        # self.T.send_request('SEL:%s ON'%self.channel)        
        self.T.send_request('TRIG:STATE?')
        self.ans = self.T.get_reply()
        print 'Trigger State Reset. Current Trigger State:'
        print self.ans
    
    @not_setting
    def auto_set_hor_scale(self,mot_load_time,bool_mag_trap,mag_hold_time):
        if bool_mag_trap:
            self.total_time = mot_load_time+mag_hold_time+2
        else:
            # self.total_time = mot_load_time+.5
            self.total_time = 9
            
        if self.total_time<=1:
            self.T.send_request('HOR:MAI:SCA 100E-3')
        elif self.total_time<=2:
            self.T.send_request('HOR:MAI:SCA 200E-3')
        elif self.total_time<=4:
            self.T.send_request('HOR:MAI:SCA 400E-3')
        elif self.total_time<=10:
            self.T.send_request('HOR:MAI:SCA 1')
        elif self.total_time<=20:
            self.T.send_request('HOR:MAI:SCA 2')
        elif self.total_time<=40:
            self.T.send_request('HOR:MAI:SCA 4')
        else:
            self.T.send_request('HOR:MAI:SCA 10')
        
        self.T.send_request('HOR:MAI:SCA?')
        self.scale = self.T.get_reply()
        print 'Horizonatal Scale AutoSet To [s/div]:'
        print self.scale
    
    @not_setting
    def grab_normal_scope_trace(self,channel):
        nn=0
        self.channel = channel
        
        # Initially check to make sure scope has finished triggering and is ready to send data
        self.T.send_request('TRIG:STATE?')
        self.trig_state = self.T.get_reply()
        print '########## Checking Trigger Status #########'
        if 'SAVE' in self.trig_state:
            print 'Trigger Status is %s. OK!'%self.trig_state
        while 'TRIGGER' in self.trig_state:
            if nn==0:
                print 'Trigger Status is %s '%self.trig_state+'Waiting for Scope to Finish Triggering'
            time.sleep(.001)    
            nn=nn+1
            self.T.send_request('TRIG:STATE?')
            self.trig_state = self.T.get_reply()
            
        # Now grab data from selected channel on scope
        print 'getting scope trace from %s'%self.channel
        self.T.send_request('DAT:SOU %s'%self.channel)
        self.T.send_request('WFMP?')
        self.settings = self.T.get_reply()
        self.T.send_request('CURV?')
        self.values = self.T.get_reply(10008)
        (self.time, self.voltage) = self.T.all_data_values(self.settings, self.values)
        self.storage[channel]= [self.time,self.voltage]
        # py.plot(self.time, self.voltage, 'r.')
        # py.show()
    
    @not_setting
    def grab_inverted_scope_trace(self,channel):
        nn=0
        self.channel = channel
        
        # Initially check to make sure scope has finished triggering and is ready to send data
        self.T.send_request('TRIG:STATE?')
        self.trig_state = self.T.get_reply()
        print '########## Checking Trigger Status #########'
        if 'SAVE' in self.trig_state:
            print 'Trigger Status is %s. OK!'%self.trig_state
        while 'TRIGGER' in self.trig_state:
            if nn==0:
                print 'Trigger Status is %s '%self.trig_state+'Waiting for Scope to Finish Triggering'
            time.sleep(.001)    
            nn=nn+1
            self.T.send_request('TRIG:STATE?')
            self.trig_state = self.T.get_reply()
            
        # Now grab data from selected channel on scope
        print 'getting scope trace from %s'%self.channel
        self.T.send_request('DAT:SOU %s'%self.channel)
        self.T.send_request('WFMP?')
        self.settings = self.T.get_reply()
        self.T.send_request('CURV?')
        self.values = self.T.get_reply(10008)
        (self.time, self.voltage_inv_) = self.T.all_data_values(self.settings, self.values)
        self.voltage = -1*self.voltage_inv_
        self.storage[channel]= [self.time,self.voltage]
        # py.plot(self.time, self.voltage, 'r.')
        # py.show()
    
    
    @not_setting
    def save_tekscope_settings(self):
        self.q = self.settings.split(';')
        self.saved_settings=[]
        self.settings_list = [10,8,13,12,14]
        for nn in range(len(self.settings_list)):
            self.saved_settings.append(self.q[self.settings_list[nn]])
        # Add some other scope settings
        self.T.send_request('HOR:SEC?')
        self.sdiv = self.T.get_reply()
        self.saved_settings.append(self.sdiv)


            
        
        
        
        
#######################################################################################
## Settings Class imported into the scripts
#######################################################################################
class Settings(object):
    """
    should instantiate this with __file__ argument to set the
    script path of the calling script.
    use _set_dict for simple values as before or make a method
    for more complex ones
    """        
    @not_setting    
    def __init__(self, filename, settings_dict = 'settings_dict', path=None):
        self.settings_dict = settings_dict          #sets name of settings dict file to use
        self.get_settings_dict()                    #gets setting dict from file
        self.scriptname = filename                  #saves name of script that called this
        self.cwd = os.getcwd()                      #saves current directory at instantiation
        for (k,v) in self._general_values_1.items(): #loads general default dict values
            setattr(self,k,v)     
        for (k,v) in self._general_values_2.items(): #loads general default dict values
            setattr(self,k,v)     
        self.Li6 = Li6Settings(self._Li6_values_)     #class for Li6 settings
        self.Rb85 = Rb85Settings(self._Rb85_values_) #class for Rb85 settings
        self.Rb87 = Rb87Settings(self._Rb87_values_) #class for Rb87 settings
        # self.cameras = ['Pixelink','Apogee']   #list of cameras configured for settings class
        self.cameras = ['Pixelink','PointGrey']   #list of cameras configured for settings class
        self.Pixelink = PixelinkSettings(self._pixelink_values_)#class for pixelink settings
        self.PointGrey = PointGreySettings(self._pointgrey_values_)
        self.Apogee = ApogeeSettings(self._apogee_values_) #class for apogee settings
        self.PA = PASettings(self._PA_values_) #class for apogee settings
        self.TekScope = TekScopeSettings(self._tek_scope_values_) # class for tek scope
        self.set_datafolder(path)         #sets inital data folder based on argument 'path'
        self.created_at =  self.timestamp #time that settings object is instantiated (script started)
        self.settingsLogName = 'settings.txt'   #name of file to store current run settings
        self.master_recipe = 'master_recipe'    #name of master recipe to load
        self.version = os.path.abspath(__file__)#version is just name of this settings module
        self.reference_run_list = []        #list of run numbers where ref values used
        self.reference_settings = []         #list of strings for ref runs like 'S.a=4'
        self.runNumber = 0                  #total number of recipe runs 
        self.stopFile = 'stop.txt'           #name of file that is searched for by check_stop method
        self.runfolder_made = False          #tells create_path no need to make path   
        #self.GA = GeneticAlgorithm()
        
    @not_setting
    def set_datafolder(self,path):
        if path is None:    #use default data folder from settings dict
            pass
        elif path == 'settings':   #folder of settings file
            self.datafolder = self.path_from_file(__file__)
        elif path == 'local':       #folder of script file
            self.datafolder = self.path_from_file(self.scriptname) 
        elif path in ['','.']:      #current working directory
            self.datafolder = self.cwd
        #user specified directory (use correct escape char or os.path.join or list)
        else:      
            self.datafolder = self.path_from_file(path)
        if not os.path.isdir(self.datafolder):
            raise Exception('datafolder "%s" is not actually a directory!'%self.datafolder)
        self.currentfolder = self.datafolder
        self.update_path()
        
    @not_setting
    def get_settings_dict(self):
        '''
        either import the default latest settings dict or the one given by the argument
        at instantiation.  Also import all the dictionaries
        '''
        # default: no version specified
        if self.settings_dict == 'settings_dict':
            from UTBus_Recipesb.settings_files import settings_dict
        else: 
            settings_dict = __import__('UTBus_Recipesb.settings_files.'+self.settings_dict,\
                globals(),locals(),[self.settings_dict])
        self._settings_dict_module = settings_dict
        d = self._settings_dict_module.__dict__
        #adds all the settings dictionaries to this object
        for k,v in d.items():
            if not k.startswith('__'):
                if isinstance(v,dict):
                    setattr(self,k,v)
        self.settings_dict = self._settings_dict_module.__name__
        
    @not_setting
    def set_sequence_values(self,i):
        for (name,list) in self.sequence_list:
            try:
                value = list[i]
            except IndexError:
                value = list[-1]
            setattr(self,name,value)
            
    @not_setting
    def _getatt(self,string):
        ac = self
        for c in string.split('.')[1:]:
            a = ac
            ac = getattr(a,c.strip())
        oldv = ac
        attr = c.strip()
        obj = a
        return obj,attr,oldv
        
    @not_setting
    def _getprop(self,string):
        s = string.split('.')
        ac = self
        for c in s[1:-1]:
            a= ac
            ac = getattr(a,c.strip())
        m0 = s[-1].split('(')
        setm = m0[0]
        propm = m0[0][3:]
        newv = eval(m0[1].split(')')[0])
        oldv= getattr(ac,propm.strip())
        return ac,setm,oldv,newv

    @not_setting
    def _setGetReset(self,setstring):
        # print 'in setGet'
        f = setstring.split('=')
        if len(f)==1:  # setting is given as a method like 'S.setROIcenter(ROI)'
            ac,setm,oldv,newv = self._getprop(f[0])
            m = getattr(ac,setm.strip())
            m(newv)
            resetdata = ['prop',ac,setm,oldv]
        else:   #method given as an attribute like 'S.loadtime = 5)
            obj,attr,oldv = self._getatt(f[0])
            newv = eval(f[1])
            setattr(obj,attr,newv)
            a = getattr(self,attr)
            resetdata = ['attr',obj,attr,oldv]
        return resetdata   

    @not_setting
    def _refReset(self,s):
        '''
        given resetdata from setGetRest, this will reset the settings properties to the old values
        after having used the reference values
        '''
        if s[0]=='prop':
            m = getattr(s[1],s[2])
            m(s[3])
        else:
            m = setattr(s[1],s[2],s[3])

    @not_setting
    def run_reference(self,setlist=None,save = True,**kw): 
        '''
        This runs the settings commands in the list, runs the recipe, saves the images, and then
        resets the values to what they were.  Save settings should be given as keywords.  They are
        passed directly to the save command (Unless save = False)
        '''
        # print 'in ref'
        if setlist is None:  # user can specify list in the call rather than using the ref_settings
            setlist = self.reference_settings
        resetlist = []
        for s in setlist:
            resetlist.append(self._setGetReset(s))
        # print 'starting reference run',self.N
        self.run_recipe()
        self.reference_run_list.append(self.runNumber)
        if save:
            self.save(**kw)
        for s in resetlist:
            self._refReset(s)
                        
    @not_setting
    def is_multiple(self,value,divisor):
        if not divisor:
            return False
        else:
            b = ((float(value)/divisor) > int(value/divisor))
            return not b

    @not_setting
    def run_recipe(self,ref=None,**kw):
        '''
        either import the default latest master recipe or an older version if specified
        by the setting, like
        S.master_recipe = 'master_recipe_testdummy'
        
        It then gets the run_recipe function and runs it given this settings object as an argument.
        '''
        #############################################
        ##problem changing name of self.master_recipe causes problems when rerunning
        ##weithout resetting
        #############################################
        print '######################### Running Recipe ##############################'
        if self.is_multiple(self.runNumber,ref):
            self.run_reference(**kw)
        hasMod=False
        load = 1
        if hasattr(self,'_master_recipe_module'): 
            hasMod = True
            mrm = self._master_recipe_module.__name__
        if self.master_recipe == 'master_recipe':  #default case
            from UTBus_Recipesb.master_recipes import master_recipe
            self._master_recipe_module = master_recipe
        else: 
            if hasMod: 
                #check if loaded module == desired module: then no load
                if mrm == 'UTBus_Recipesb.master_recipes.'+self.master_recipe: load=0
            #if different module desired : load it...
            if load: 
                self._master_recipe_module = __import__('UTBus_Recipesb.master_recipes.'\
                +self.master_recipe,globals(),locals(),[self.master_recipe])
        #ensure we save actual module name
        self.master_recipe_module_name = self._master_recipe_module.__name__ 
        self.maser_recipe_module_source = self._master_recipe_module.__file__
        print 'Running module',self._master_recipe_module
        run_recipe = self._master_recipe_module.run_recipe
        run_recipe(self)
        self.runNumber += 1
   
    @not_setting
    def create_path(self,suffix='datetime'):
        if not self.runfolder_made:  #if runfolder not made, make path and runfolder
            # print 'IN IF NOT SELF.RUNFOLDER_MADE'
            self.date = self.timestamp.split('_')[0]
            #datafolder
            self.make_dir(self.datafolder)
            #datefolder
            self.datefolder = os.path.join(self.datafolder,self.date)
            self.make_dir(self.datefolder)
            #runfolder
            script = os.path.splitext(os.path.split(self.scriptname)[1])[0]
            self.runfolder = os.path.join(self.datefolder,script)
            self.make_dir(self.runfolder,suffix=suffix)  # leaves currentfolder at runfolder
            self.runfolder = self.currentfolder
            # If set to True, program assumes the same foldername is used for everyrun
            # Set to False forces to program to check, and gives ability to save to multiple folders during a run
            self.runfolder_made = False 
        else:  #else runfolder exists so either make new one with new suffix or just switch currentdir
            # print '2222222222222222222 IN CREATE PATH 22222222222222222222'
            # print self.runfolder
            # print suffix
            self.make_dir(self.runfolder,suffix=None)

    @not_setting
    def update_path(self):
        self.Apogee.datafolder = self.currentfolder
        self.Pixelink.datafolder = self.currentfolder
        self.PointGrey.datafolder = self.currentfolder

    @not_setting
    def get_settings(self):
        self._settings_list = self.__get_settings(self)
        return self._settings_list
        
    @not_setting
    def __get_settings(self,obj):
        '''
        this sorts through the object and gets all attributes which are not 
        -- private ==> ('_","__") 
        -- or not marked explicitly 'not_setting', 
        -- or not methods that are not properties (like 'timestamp')
        ie. normal settings
        -- if attr is another object defined here it does same for its attributes
        This is used for saving the settings values
        '''
        values_dict = dict()
        namelist = dir(obj)
        for n in namelist:
            a = getattr(obj,n)
            if str(type(a)).startswith('<class'):
                    if hasattr(a,'skip_class') or a.__module__ != self.__module__:
                        pass
                    else:
                        cdict = self.__get_settings(a)
                        for k,v in cdict.items():
                            values_dict['_' + n + '.' + k] = v
            elif self.is_setting(n,a):
                values_dict[n] = self.__tmp
        return values_dict
               
    @not_setting
    def is_setting(self,n,a):
        if hasattr(a,'notsetting') or n.startswith('__') or  n.startswith('_'):
            return False
        ## it might be a method use to calculate a setting these should normally
        ## have @property decorators like 'timestamp' but we leave the option...
        if ismethod(a):
            try:
                self.__tmp = a()
            except TypeError:
                pass
        else:
            self.__tmp = a
        return True
       
    @not_setting
    def list_settings(self, verbose = True):
        settings = self.get_settings()
        skeys = settings.keys()
        skeys.sort(key=str.lower)
        settings_list = []
        if verbose:
            print '\n'+10*'*'+'SETTINGS'+10*'*'+'\n'
        for k in skeys:
            s1 = '%s'%k
            s2 = s1.ljust(20)
            s = '%s = %s'%(k,settings[k])
            settings_list.append(s)
            if verbose: print s
        return settings_list

    @not_setting
    def list_writer(self,_list,filepath):
        #Writes the list in list1 to the file specified by filepath
        with open(filepath, 'a') as myfile:
            for element in _list[-1]:
                myfile.write('%s\t' %element)
            myfile.write('\n')
        
    @not_setting
    def write_a_list_settings(self,_list,filepath):
        # f = open(filepath,'w')
        out = open(filepath,"w")
        for n in range(len(_list)):
            out.write("%s  \n" %(_list[n]))
        out.close()    
        # print 'wrote %s'%filepath
        
    @not_setting
    def write_settings(self,suffix=None):
        namebase = self.settingsLogName
        if suffix:
            base,ext = os.path.splitext(namebase)
            newfilename = base + "_" + suffix + "." + ext
        else:
            newfilename = namebase
        filepath = os.path.join(self.currentfolder,newfilename)
        _list = self.list_settings(verbose = False)
        self.write_a_list_settings(_list,filepath)
        return filepath
        
    @not_setting
    def write_PA_freq(self,suffix=None):
        namebase = "PA_freq.txt"
        if suffix:
            base,ext = os.path.splitext(namebase)
            newfilename = base + "_" + suffix + "." + ext
        else:
            newfilename = namebase
        filepath = os.path.join(self.currentfolder,newfilename)
        _list = self.PA.freq
        # self.write_a_list_PA(_list,filepath)
        #Should be able use
        self.list_writer(_list,filepath)
        # return filepath
        
    @not_setting
    def write_script(self,suffix=None):
        scriptname = os.path.split(self.scriptname)[1]
        if suffix:
            base,ext = os.path.splitext(scriptname)
            newfilename = base + "_" + suffix + "." + ext
        else:
            newfilename = scriptname
        newpath = os.path.join(self.currentfolder,newfilename)
        if not os.path.isfile(newpath):
            copyfile(self.scriptname,newpath)
        
    @not_setting
    def write_images(self,cameras='all',data='images',**kw):
        #this can take all 'save_images' keywords shown above in the camera classes
        #figure out which data is requested and which cameras have images
        print "####################hi#########################"
        if cameras in  ['all','all_b','all_d','all_i']:
            if cameras == 'all_b':
                data = 'both'
            elif cameras == 'all_d':
                data = 'data'
            else: 
                data = 'images'
            cameras = self.cameras
            print 'Camera List', cameras
            # Checks to make sure that the camera settings objects have a non-empty _imagelist.
            cameras = filter(lambda camNam: not getattr(getattr(self, camNam), '_imagelist') == [], cameras)
            # for camName in cameras:
                # print camName
                
            
            
            print 'Filtered Camera List', cameras             
        if cameras == None:
            cameras = []
        imagefolders={}
        for name in cameras:
            # if name.split('_')[-1] == 'b':
#                 data = 'both'
#             elif name.split('_')[-1] == 'd':
#                 data = 'data'
#             elif name.split('_')[-1] == 'i':
#                 data = 'images'
            c = getattr(self,name)
            #check if user wants to use the camera labels for filenames.  if so, set it.
            if kw.get('filenames','not_camera_labels') == 'camera_labels':
                kw['filenames'] = c.labels
            if data in ['data','both']:
                kw['data']=True
                imagefolder = c.save_images(**kw)
            if data in ['images','both']:
                kw['data']=False
                imagefolder = c.save_images(**kw)
            print 'image folder is',imagefolder
            if imagefolder:
                imagefolders[name] = imagefolder
        self.write_newdir_file(imagefolders)
    
    @not_setting
    def write_newdir_file(self,imagefolders):
        newdirfile = os.path.join(self.datafolder,'newdir.txt')
        f = open(newdirfile,'w')
        for (camera,imagefolder) in imagefolders.items():
            f.write('%s::%s\n'%(camera,imagefolder))
        if self.pickle:
            f.write('pickle::%s\n'%self.picklepath)
        f.close()
        
    @not_setting
    def write_pickle(self,suffix=None):
        # print 'in a pickle',self.currentfolder
        d=self.__get_settings(self)
        if suffix:
            picklefile = "pickled_settings_" + suffix + ".txt"
        else:
            picklefile = 'pickled_settings.txt'
        path = os.path.abspath(os.path.join(self.currentfolder,picklefile))
        f = open(path,'w')
        cPickle.dump(d,f)
        f.close()
        self.picklepath = path
        
    @not_setting
    def load_pickle(self,file):
        '''
        this is still a method in progress ,but the write pickle does write the setting dict.
        '''
        if not os.path.isabs(file):
            file = os.path.join(self.currentfolder,file)
     
        if os.path.isfile(file):
            f = open(file,'r')
            dict = cPickle.load(f)
            f.close()
            print dict
            for (k,v) in dict.items():
                print k,v
                try:
                    setattr(self,k,v)    
                except:
                    print 'WARNING: could not write %s: skipping.'%repr(k)
                    print sys.exc_info()[0]
        else:
            print 'file %s does not exist'%file
    
    @not_setting
    def save(self, 
            suffix='datetime',
            subsuffix=None,
            script=True,
            scriptsuffix=None,
            settings=True,
            settingssuffix=None,
            pickle=True,
            picklesuffix=None,
            camerasuffix='time',
            cameras='all_i',
            tekscope= False,
            **kw):
        # print 'suffix = ', suffix
        # print 'currentfolder = ',self.currentfolder
        self.create_path(suffix=suffix) #leaves currentfolder as runfolder_suffix
        # print 'in save; cameras=',cameras,self.cameras
        if script:  #copy script file to runfolder
            self.write_script(suffix=self.suffix(scriptsuffix))
        if settings or cameras or pickle or tekscope:
            #get script file name base only : .../script.py ==> script
            sequence_dir = os.path.splitext(os.path.split(self.scriptname)[1])[0]
            # print 'seqdir',sequence_dir
            self.make_dir(sequence_dir,suffix = subsuffix) #make subdir with scriptname_subsuffix
            self.sequence_dir = self.currentfolder
            if settings:
                self.write_settings(suffix=self.suffix(settingssuffix))
            if self.bool_write_Wavemeter:
                self.write_PA_freq(suffix=self.suffix(settingssuffix))
            if pickle:
                self.pickle = pickle
                self.write_pickle(suffix=self.suffix(picklesuffix))
            if cameras:
                self.write_images(cameras,suffix=self.suffix(camerasuffix),**kw)   
            if tekscope:
                self.advise=0
                self.nn_=1
                self.nn = str(self.nn_)
                # Save trace data to text file
                self.trace_dir = 'tekscope_'+camerasuffix
                self.savedir = os.path.join(self.currentfolder,self.trace_dir)
                self.filename = self.trace_dir+'_data_'+self.nn+'.txt'
                self.time = self.TekScope.storage['CH1'][0]
                self.voltage = self.TekScope.storage['CH1'][1]
                self.ref = self.TekScope.storage['CH2'][1]
                if not os.path.isdir(self.savedir):
                    os.mkdir(self.savedir)
                self.filepath = os.path.join(self.savedir,self.filename) 
                while os.path.exists(self.filepath):
                    self.nn_=self.nn_+1
                    self.nn = str(self.nn_)
                    self.filename = self.trace_dir+'_data_'+self.nn+'.txt'
                    self.filepath = os.path.join(self.savedir,self.filename) 
                    self.advise=1
                if self.advise:
                    print '!!!WARNING!!! tekscope save filename already exists. saved with suffix %s'%self.nn_
                file = open(self.filepath,'w')
                for index in range(len(self.time)):
                    file.write(str(self.time[index])+' '+str(self.voltage[index])+' '+str(self.ref[index])+'\n')
                file.close()
                
                # Save scope settings information to text file
                self.tek_settings_savedir = self.currentfolder
                self.tek_settings_filename = self.trace_dir+'_settings.txt'
                self.scope_settings = self.TekScope.saved_settings
                
                # Now add a few experiment settings
                self.scope_settings.append(self.Rb.loadmot_s)
                if self.bool_load_rb_magnetic_trap:
                    self.scope_settings.append(self.hold_rb_magnetic_trap_s)
                else:
                   self.scope_settings.append(999) 
                self.scope_settings.append(self.TekScope.scope_recapture_ms)
                
                self.tek_settings_filepath = os.path.join(self.savedir,self.tek_settings_filename)
                file = open(self.tek_settings_filepath,'w')
                for index in range(len(self.scope_settings)):
                    file.write(str(self.scope_settings[index])+'\n')
                file.close()

            
                
    
    def settimestamp(self,value):
        '''
        timestamp will always be current, so setting does nothing
        we provide this to allow generalized setting of attributes
        '''
        pass           
    
    @property
    def timestamp(self):
        return time.strftime("%Y%m%d_%H%M%S")
    
    @not_setting
    def path_from_file(self,filename):
        if os.path.isfile(filename):
            filepath = os.path.abspath(filename)
            return os.path.split(filepath)[0]
        else:
            return os.path.abspath(filename)
            
    @not_setting
    def make_dir(self,*path,**kw):
        """
        use to make standard directory and or set current dir to path
        for subsequent write commands
        keywords
        suffix = None,'date','time','datetime' or any artitrary string
               determines what follows rundirectory namebase.
               the first 4 will attach info described or use can send
               a string of his own to attach.
        make = True
                False: it will change currentdir to path if it exists but not make it.
        """
        default = dict(
            suffix=None,
            make=True
                        )
        for k in kw.keys():
            default[k] = kw[k]

        path = os.path.join(*path)
        
        path = path + self.suffix(default['suffix'])#added
        # print 'path is',path

        def makeit(path):
            if not os.path.isdir(path):
                if default['make']:
                    os.makedirs(path)
                    # print 'made new directory %s'%path
            else:
                print 'folder exists:  %s'%path
            self.currentfolder = path
            self.update_path()
            # print 'current folder set to: %s'%self.currentfolder
            return self.currentfolder
            
        if os.path.isabs(path):
            #path = path + self.suffix(default['suffix'])
            if os.path.isdir(path):
                self.currentfolder = os.path.abspath(path)
                # print 'current folder set to: %s'%self.currentfolder
                self.update_path()
                return path
            else:
                return makeit(path)
        else:
            print 'folder path is not absolute: making subdirectory.'
            path = os.path.join(self.currentfolder,path)
            return makeit(path)
                
    @not_setting
    def suffix(self,suffix):
        if suffix == 'date':
            # print 'WARNING: suffix does not contain time. Possible overwrite.'
            return '_%s'%self.date
        elif suffix == 'time':
            return '_%s'%self.timestamp.split('_')[1]
        elif suffix == 'datetime':
            return '_%s'%self.timestamp
        elif isinstance(suffix,type('')):
            # print 'WARNING: suffix does not contain time. Possible overwrite.'
            return '_%s'%suffix
        else:
            # print 'WARNING: suffix does not contain time. Possible overwrite.'
            return ''
    
    def stop_file_exists(self,remove=False):
        '''
        This can be used in a script loop to stop the loop.  When called the method
        will search for a 'stop.txt' file in the self.datafolder directory 
        (usually E:\DATA\) and return True if it finds it or False if not.
        This can then be used to break the loop or continue like this:
        if S.check_stop(): break
        then if you want to stop  the loop just create an empty 'stop.txt' file in that folder
        If remove = True, the method will automatically remove the stop file before returning
        '''
        print self.datafolder
        dirContents = os.listdir(self.datafolder)
        if os.path.basename(self.stopFile) in dirContents:
            stopFilePath = os.path.join(self.datafolder,self.stopFile)
            # print 'checking in %s for %s'%(self.datafolder,self.stopFile),os.path.isfile(stopFilePath)
            if os.path.isfile(stopFilePath):
                print 'stop file found'
                if remove:
                    os.remove(stopFilePath)
                    # os.remove(self.stopFile) #THIS WAS ORIGINALLY USED BUT DOESN'T HAVE THE CORRECT PATH. NOT SURE IF THIS CHANGE WILL HAVE ERRORS ELSEWHERE - KAHAN 20150617
                    print 'stop file removed'
                return True
            else: 
                return False
        else:#no flag file ==> do nothing
            return False
            
    @not_setting
    def append(self,C):
        '''
        used to append another classes public attributes to the Settings Object
        '''
        for n in dir(C):
            if n.startswith('_') or n.startswith('__'):
                continue
            else:
                a = getattr(C,n)
                if ismethod(a):
                    continue
                else:
                    setattr(self,n,a)
        
    @not_setting
    def list_methods(self,verbose=True):
        m = []
        for n in dir(self):
            if '__' in n:
                pass
            else:
                a = getattr(self,n)
                if ismethod(a):
                    m.append(n)
        if verbose: 
            print '\n'+10*'*'+'METHODS'+10*'*'+'\n'
            for md in m:   
                print md
        return m

    @not_setting
    def fitness(self):
        # fitnessfolder = "E:\UTBus_Recipes\UTBus_Recipesb\recipe_libs\genetic_algorithm"
        fitnessfolder = "E:\UTBus_Recipes\UTBus_Recipesb"
        fitnessFile ='fitness_value.txt'
        while 1:
            dirContents = os.listdir(fitnessfolder)
            if os.path.basename(fitnessFile) in dirContents:
                fitnessFilePath = os.path.join(fitnessfolder,fitnessFile)
                #print 'checking in %s for %s'%(self.datafolder,self.fitnessFile),os.path.isfile(fitnessFilePath)
                if os.path.isfile(fitnessFilePath):
                    #print 'fitness file found'
                    fin = open(fitnessFilePath,'r')
                    val = float(fin.readline().strip())
                    fin.close()
                    os.remove(fitnessFilePath)
                    return val
                else: 
                    return -1
            time.sleep(.5)
            
            
if __name__ == "__main__":
    S = Settings(__file__)
    print dir(S)
    print '\n'+10*'*'+'SETTINGS'+10*'*'+'\n'
    S.list_settings()
    for s in S.list_methods():
        print s
    if 1:
        S.create_path()
        #S.write_settings()
        

    #print 'loading settings file "%s"'%os.path.abspath(__file__)
    #print os.path.normpath(os.path.join(os.getcwd(), __file__))
    #print os.path.join(os.getcwd(), __file__)
    #print 'cwd',os.getcwd()
    #print 'file',__file__
    #for k in sys.modules.keys():
        #if 'test' in k or 'main' in k:
            #print 'sys',sys.modules[k]

