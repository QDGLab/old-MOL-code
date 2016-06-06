"""
"""
import os.path
import struct
import subprocess
from getpass import getuser
import sys

import ByteCode as BC
from Exceptions import *
import Globals
from SignalsManager import emit

MHz = 1000000.

recipes_stack_ = []

def set_utbus_external_clock(freq,run=True):#***
    from Globals import bus_address, utbus_external_clock_DDS_params as P
    from DDS import DDS
    address = bus_address["utbus_external_clock_dds"]
    R = Recipe("set_utbus_external_clock")
    R.start()
    D = DDS(address=address)
    D.reset()
    D.enable_comp()
    D.enable_control_DAC()
    D.single_tone(freq)
    D.set_amplitude(P['ampl'])
    R.end(bootstrap=True,run=run)#***

def turn_off_utbus_external_clock(run=True):#***
    from Globals import bus_address
    from DDS import DDS
    address = bus_address["utbus_external_clock_dds"]
    R = Recipe("turn_off_utbus_external_clock")
    R.start()
    D = DDS(address=address)
#    D.reset()
    D.single_tone(0)
    D.set_amplitude(0)
    R.end(bootstrap=True,run=run)#***
    
#run flag added by bruce on 20090212, affected parts annotated with #***
class Recipe(object):
    def __init__(self,name,**kw):
        self.name = name
        fname = os.path.join(Globals.bytecode_folder,name + ".utb")
        self.fname = fname
        self.__bcode_buffer_size = 1024

        self.use_external_trigger(kw.pop('use_external_trigger',False))
        self.set_timing_parameters(**kw)

    def use_external_trigger(self,state):
        self.use_external_trigger = state

    def set_timing_parameters(self,**kw):
        try:
            self.use_internal_clock = f = kw.get("use_internal_clock",True)
            if not f:
                self.bus_sampling_frequency = kw["sampling_frequency"]
            else:
                self.bus_sampling_frequency_divider = kw.get("sampling_frequency_divider",20)
                self.bus_sampling_frequency = Globals.DDS_reference_sampling_rate/self.bus_sampling_frequency_divider
            self.command_period = 3/float(self.bus_sampling_frequency)
        except KeyError,K:
            raise Error("You must provide parameter '%s' to set_timing_parameters" % K)

    def add_device(self,device):
        self.__devices.append(device)

    def start(self):
        global recipes_stack_
        recipes_stack_.append(self)
        self.f = open(self.fname,"wb")
        self.__devices = []
        self.__bcode = ""
        self.__len = 0
        self.__cycles = 0
        # the position of the time markers measured in cycles
        self.__time_markers = {'start' : 0}
        self.insert_bytecode(*BC.signature())
        print "Bytecode generation starts (%s)" % self.name

    def end(self,repeat=1,bootstrap=False,run=True): #***
        global recipes_stack_
        self.insert_bytecode(*BC.stop())
        if self.__len > 0:
            self.f.write(self.__bcode)
            self.__bcode = ""
            self.__len = 0
        
        recipes_stack_.pop()
        self.f.close()
        print "Bytecode generation ends (%s)" %self.name
        emit("recipe_ends")

        if not bootstrap:
            if not self.use_internal_clock:
                set_utbus_external_clock(self.bus_sampling_frequency,run = run)#***
            else:
                turn_off_utbus_external_clock(run = run)#***

        emit("bytecode_starts")
        print "Recipe %s will run for %f seconds" % (self.name,
                                                     self.__cycles_2_time(self.__cycles))
        if run:     #***
            self.__run_bytecode(repeat)
        emit("bytecode_stops")

    def comment(self,msg):
        bcode = BC.comment(msg)
        self.insert_bytecode(bcode)

    def set_sampling_rate_divider(self,sr):
        bcode = BC.set_sampling_rate_divider(sr)
        self.insert_bytecode(bcode)

    def wait_cycles(self,cycles):
        bcode = BC.wait(cycles)
        self.insert_bytecode(*bcode)

    def wait_time(self,dt,factor):
        if dt == 0 : return
        cycles = self.__time_2_cycles(dt,factor)
        Dt = float(dt*factor)
        self.wait_cycles(cycles)
        
    def wait_s(self,s):
        # print 'waiting %d s \n' %(s)
        self.wait_time(s,1)

    def wait_ms(self,ms):
        # print 'waiting %d ms \n' %(ms)
        self.wait_time(ms,0.001)

    def wait_us(self,us):
        self.wait_time(us,0.000001)
    
    def set_time_marker(self,label):
        if label in self.__time_markers:
            raise Error('Time marker was already used in this recipe!')
        self.__time_markers[label] = self.__cycles
        return self.__cycles_2_time(self.__cycles)
        
    def get_time(self,reference='start'):
        now = self.__cycles
        then = self.__time_markers[reference]
        Dc = now - then
        return self.__cycles_2_time(Dc)
        
    def get_time_marker(self,label):
        return self.__cycles_2_time(self.__time_markers[label])

    def goto(self,t,reference='start'):
        # print 'goto %lf\n' %(t)
        now = self.__cycles
        then = self.__time_2_cycles(t,1) + self.__time_markers[reference]
        Dc = then - now
        if Dc < 0:
            raise Error("The goto(%f,'%s') is in the past by %d cycles!!" % (t,reference,-Dc))
        self.wait_cycles(Dc)
        return t

    goto_s = goto
    def goto_ms(self,t,reference='start'):
        return self.goto(t*0.001,reference)
    def goto_us(self,t,reference='start'):
        return self.goto(t*0.000001,reference)

    def insert_bytecode(self,bcode,cycles):
        self.__bcode += bcode
        self.__len += len(bcode)
        self.__cycles += cycles
        if self.__len >= self.__bcode_buffer_size:
            self.f.write(self.__bcode)
            self.__bcode = ""
            self.__len = 0

    def __time_2_cycles(self,t,factor):
        T = float(t*factor)
        sf = self.bus_sampling_frequency
        cycles = T*sf
#        if cycles < 1:
#            raise Error("I cannot convert time %f s into cycles when the bus sampling frequency is %f" % (T,sf))
        icycles = int(cycles)
        if cycles - icycles > 0.5:
            icycles += 1
        return icycles

    def __cycles_2_time(self,cycles):
        return float(cycles)/self.bus_sampling_frequency

    def __run_bytecode(self,repeat):
        cmd = [Globals.bus_driver_path]
        if self.use_internal_clock:
            cmd.append(1)
        else:
            cmd.append(0)

        if not self.use_internal_clock:
            cmd.append(self.bus_sampling_frequency)
        else:
            cmd.append(self.bus_sampling_frequency_divider)

        if self.use_external_trigger:
            cmd.append(1)
        else:
            cmd.append(0)
        
        cmd.append(self.fname)

        cmd = map(str,cmd)
        for i in range(repeat):
            try:
                print " ".join(cmd)
                subprocess.call(cmd)
            except KeyboardInterrupt:
                emit("UTBusDriver interrupted")
                print "UTBusDriver interrupted"

#    def insert_marker_at_time(self,t,factor):
#        current_cycles = self.__cycles
#        final_cycles = self.__time_2_cycles(t,factor)
#        Dc = final_cycles - current_cycles
#        if Dc < 0:
#            raise Error("The marker at time %f s is in tha past!!" % (t*factor))
#        self.wait_cycles(Dc)
#
#    def insert_marker_at_time_s(self,t):
#        self.insert_marker_at_time(t,1)
#        
#    def insert_marker_at_time_ms(self,t):
#        self.insert_marker_at_time(t,0.001)
        
        
def insert_bytecode(bcode,cycles):
    global recipes_stack_
    if not recipes_stack_:
        raise Error("The recipes stack is empty at this moment")
    recipes_stack_[-1].insert_bytecode(bcode,cycles)
        
#def get_state_dir(addr):
#    return os.path.join(Globals.state_folder,"object_%d" % addr)

def get_current_recipe():
    global recipes_stack_
    return recipes_stack_[-1]
