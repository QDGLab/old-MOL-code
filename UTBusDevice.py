"""
The basic interface of all UTBus devices.
"""
import copy_reg
import os,os.path
import pickle
import types

from ByteCode import simple_command, command_sequence
from Exceptions import *
from Globals import state_folder
from Recipe import insert_bytecode
from SignalsManager import connect

pjoin = os.path.join

def get_state_file_name(base_address):
    return pjoin(state_folder,"state_%d" % base_address)

class UTBusDeviceMetaclass(type):
    _active_devices = {}
    def __init__(cls,cls_name,bases,dict):
        """
        """
        
    def __call__(cls,*args,**kw):
        base_address = kw.get("base_address",kw["address"])
        # maybe the device is already active
        device = cls._active_devices.get(base_address)
        if device: return device

        # device not active, load the previous state if available
        state_file_name = get_state_file_name(base_address)
        if os.path.isfile(state_file_name) and not kw.get("ignore_old_state"):
#            print "reusing state for device '%d' from '%s'" %\
#             (base_address,state_file_name)
            f = open(state_file_name,"r")
            try:
                device = pickle.load(f)
            except:
                print "Something wrong with the state file of device %s (%s)" %\
                    (base_address,state_file_name)
                device = type.__call__(cls,*args,**kw)
            f.close()
        # prev state not available: create a new device
        else:
            device = type.__call__(cls,*args,**kw)

        cls._active_devices[base_address] = device
        connect("recipe_ends",device.save_state)
        connect("UTBusDriver interrupted",device.delete_state)
        
        return device

class UTBusDevice(object):
    __metaclass__ = UTBusDeviceMetaclass
    
    def __init__(self,base_address,ignore_old_state=False):
        self.base_address = base_address

    def command(self,data,offset=0):
        address = self.base_address + offset
        return self.__raw_command(address,data)

    def __raw_command(self,address,data):
        if isinstance(data,list):
            bcode = command_sequence(address,data)
        else:
            bcode = simple_command(address,data)
        insert_bytecode(*bcode)

    def save_state(self):
        fname = get_state_file_name(self.base_address)
        f = open(fname,'w')
        pickle.dump(self,f)
        f.close()
#        print "saved state for device '%d' in file '%s'" %\
#         (self.base_address,fname)

    def delete_state(self):
        fname = get_state_file_name(self.base_address)
        if os.path.isfile(fname):
#            print "Delete state file '%s'" % fname
            os.unlink(fname)

def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    if func_name.startswith('__') and not func_name.endswith('__'):
        cls_name = cls.__name__.lstrip('_')
        if cls_name: func_name = '_' + cls_name + func_name
    return _unpickle_method, (func_name, cls, obj)

def _unpickle_method(func_name, cls, obj):
    if obj is None:
        method = getattr(cls, func_name)
    else:
        method = getattr(obj, func_name) 
    return method
copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)
