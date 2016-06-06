"""
This module is used to control a DDS.
"""
import struct

from UTBus1.Exceptions import *
from UTBus1.Utils import signum
from UTBus1.Globals import master_DDS_params

from UTBus1.UTBusDevice import UTBusDevice
from Register import Register, RegisterField
from ProgrammableField import ProgrammableField

# describe all the register fields that can be independently programmed
DDS_programmable_fields = {
    "phase_1" : {"type" : "int","reg_fields" : ["01","00[0:5]"]},
    "phase_2" : {"type" : "int","reg_fields" : ["03","02[0:5]"]},
    "freq_1" : {"type" : "int","reg_fields" : ["09","08","07","06","05","04"]},
    "freq_2" : {"type" : "int","reg_fields" : ["0F","0E","0D","0C","0B","0A"]},
    "delta_freq" : {"type" : "int_2c",
                    "reg_fields" : ["15","14","13","12","11","10"]},
    "update_clock" : {"type" : "int","reg_fields" : ["19","18","17","16"]},
    "ramp_rate_clock" : {"type" : "int","reg_fields" : ["1C","1B","1A[0:3]"]},
    "PD_comp" : {"type" : "bit","address" : "1D[4]", "default" : 1},
    "PD_control_dac" : {"type" : "bit","address" : "1D[2]"},
    "PD_dac" : {"type" : "bit","address" : "1D[1]"},
    "PD_dig" : {"type" : "bit","address" : "1D[0]"},
    "PLL_range" : {"type" : "bit","address" : "1E[6]", "default" : 1},
    "PLL_bypass" : {"type" : "bit","address" : "1E[5]", "default" : 1},
    "refclock_multiplier" : {"type" : "small_int","bits" : "1E[0:4]","default" : 4},
    "CLR_acc1" : {"type" : "bit","address" : "1F[7]"},
    "CLR_acc2" : {"type" : "bit","address" : "1F[6]"},
    "triangle" : {"type" : "bit","address" : "1F[5]"},
    "mode" : {"type" : "small_int","bits" : "1F[1:3]"},
    "internal_update_clock" : {"type" : "bit","address" : "1F[0]","default" : 1},
    "bypass_inv_sinc" : {"type" : "bit","address" : "20[6]"},
    "OSK_en" : {"type" : "bit","address" : "20[5]","default" : 1},
    "OSK_int" : {"type" : "bit","address" : "20[4]"},
    "OSK_multiplier" : {"type" : "int","reg_fields" : ["22","21[0:3]"]},
    "OSK_ramp_rate" : {"type" : "int","reg_fields" : ["25"],"default" : 128},
    "control_dac" : {"type" : "int","reg_fields" : ["27","26[0:3]"]},
    }
# the undefined register bits
DDS_undefined_fields = [
    "00[6:7]",
    "02[6:7]",
    "1A[4:7]",
    "1D[3]",
    "1D[5:7]",
    "1E[7]",
    "1F[4]",
    "20[0:3]",
    "20[7]",
    "21[4:7]",
    "23[0:7]",
    "24[0:7]",
    "26[4:7]",
]
# the operation modes (valid values for DDS_parms['mode']
DDS_modes = {
    "single_tone" : 0,
    "fsk" : 1,
    "ramped fsk" : 2,
    "chirp" : 3,
    "bpsk" : 4,
    }

class DDS(UTBusDevice):

    def __init__(self,**kw):
        """
        The following keyword arguments are required:
        address : the (unshifted) address
        reflock : the frequency of the reference clock
        refclock_multiplier : the clock multiplier [4-20]
        internal_FSK: 
        """
        address = kw.pop("address")
        UTBusDevice.__init__(self,address)

        self.__refclock = kw.pop("refclock",master_DDS_params["freq"])
        self.__refclock_multiplier = mult = kw.pop("refclock_multiplier",20)
        self.__disable_PLL = (mult == 1)
        if mult != 1 and (mult < 4 or mult > 20):
            raise Error("Invalid reflock multiplier, '%d'. Must be an integer in the [4,20] range or 1 (which means PLL is disabled).")
        self.__SYSCLK = self.__refclock * self.__refclock_multiplier
        self.__internal_FSK = kw.pop("internal_FSK",False)
        self.__FSK = None

        # map hex address to Register instance
        # is populated dynamically by self.__create_field
        self.__registers = {}
        # the DDS programmable fields
        self.__fields = {}
        for (name,field_desc) in DDS_programmable_fields.items():
            self.__fields[name] = self.__create_field(name,field_desc)
        # fill the DDS undefined bits
        for fd in DDS_undefined_fields:
            rf = self.__get_register_field(fd)
            rf.set(0)

        if not self.__disable_PLL:
            self.enable_PLL(True)

    def reset(self,update_chip=True):
        # needs to be fixed: the master reset signal has to be high for at least
        # 10 SYSCLK cycles (see pag. 32 in the manual).
        # For the time being it is assumed that the UTBus is at least 10x slower
        # than SYSCLK

        # reset the chip
        self.command(0)
        self.__FSK = 0
        
        for f in self.__fields.values():
            f.reset()

        for r in self.__registers.values():
            r.mark_as_clean()

        self.enable_PLL(not self.__disable_PLL)
        self.__set("bypass_inv_sinc",1)
        self.__set("PD_control_dac",1)
        self.__set("PD_comp",1)
        self.__set("internal_update_clock",0)
        self.__set("OSK_en",1)
        self.__set("OSK_int",0)

        mult = self.__refclock_multiplier
        self.__set("refclock_multiplier",mult)
        if self.__SYSCLK >= 200*10**6:
            self.__set("PLL_range",1)
        
        self.__set("OSK_multiplier",4095)

        if update_chip: self.__program_chip()

    def enable_PLL(self,state):
        if state:
            s = 0
        else:
            s = 1
        self.__set("PLL_bypass",s)
        
    def enable_comp(self,update_chip=True):
        self.__set("PD_comp",0)
        if update_chip: self.__program_chip()
 
    def enable_control_DAC(self,update_chip=True):
        self.__set("PD_control_dac",0)
        if update_chip: self.__program_chip()

    def enable_control(self,update_chip=True):
        print "Deprecation warning: Rename enable_control to enable_control_DAC!!"
        self.enable_control_DAC(update_chip)

    def set_amplitude(self,value,update_chip=True):
        """
        value should be in the range [0,1]
        """
        if value < 0 or value > 1:
            raise Error("value '%f' is out of valid range [0,1]" % value)
        enc_value = int(value*4095)
        self.__set("OSK_multiplier",enc_value)
        if update_chip: self.__program_chip()

    def single_tone(self,f,update_chip=True):
        FREQ = self.__freq_to_register_value

        self.__set("mode",0)
        self.__set("freq_1",FREQ(f))

        if update_chip: self.__program_chip()

    def unramped_FSK(self,f1,f2,update_chip=True):
        FREQ = self.__freq_to_register_value

        print 'in unramped_FSK'
        
        self.__set("mode",1)
        self.__set("freq_2",FREQ(f2))
        self.__set("freq_1",FREQ(f1))
        #self.__set("freq_2",FREQ(f2))

        if update_chip: self.__program_chip()
        
    def ramped_FSK(self,f1,f2,DT,update_chip=True):
        if f1 > f2:
            raise Error("ramped method requires the first frequency to be the lowest one")

        SYSCLK = self.__SYSCLK
        print SYSCLK
        Ts = 1./SYSCLK
        FREQ = self.__freq_to_register_value
        min_df = self.__get_frequency_resolution()
        
        # set the mode
        self.__set("mode",2)
        self.__set("freq_1",FREQ(f1))
        self.__set("freq_2",FREQ(f2))

        # try Nr = 1 first
        Nr = 1
        dt = (Nr + 1)*2.*Ts
        N = int(DT/dt)
        df = float(f2 - f1)/N

        if df == 0 or abs(df) >= 1*min_df:
            pass
        else:
            df = signum(df)*1*min_df
            N = int(float(f2 - f1)/df)
            Nr = int((DT*df)/(2*Ts*(f2 - f1)))

        self.__set("delta_freq",FREQ(df,twos_complement=True))
        self.__set("ramp_rate_clock",Nr)
        self.__set("triangle",0)

        # toggle CLR ACC1
        for s in (0,1,0):
            self.__set("CLR_acc1",s)
            
        if update_chip: self.__program_chip()

    def sawtooth(self,f1,f2,DT,update_chip=True):
        if f1 > f2:
            raise Error("sawtooth method requires the first frequency to be the lowest one")

        SYSCLK = self.__SYSCLK
        Ts = 1./SYSCLK
        FREQ = self.__freq_to_register_value
        min_df = self.__get_frequency_resolution()
        
        # set the mode
        self.__set("mode",2)
        self.__set("freq_1",FREQ(f1))
        self.__set("freq_2",FREQ(f2))

        # try Nr = 1 first
        Nr = 1
        dt = (Nr + 1)*2.*Ts
        N = int(DT/dt)
        df = float(f2 - f1)/N

        if df == 0 or abs(df) >= 1*min_df:
            pass
        else:
            df = signum(df)*1*min_df
            N = int(float(f2 - f1)/df)
            Nr = int((DT*df)/(2*Ts*(f2 - f1)))

        self.__set("delta_freq",FREQ(df,twos_complement=True))
        self.__set("ramp_rate_clock",Nr)
        self.__set("triangle",1)

        # toggle CLR ACC1
        self.__set("CLR_acc1",1)
            
        if update_chip: self.__program_chip()

    def triangle_ramp(self,f1,f2,DT,update_chip=True):
        SYSCLK = self.__SYSCLK
        Ts = 1./SYSCLK
        FREQ = self.__freq_to_register_value
        min_df = self.__get_frequency_resolution()
        
        # set the mode
        self.__set("mode",2)
        # toggle CLR ACC1
        for s in (0,1,0):
            self.__set("CLR_acc1",s)
            
        self.__set("freq_1",FREQ(f1))
        self.__set("freq_2",FREQ(f2))

        # try Nr = 1 first
        Nr = 1
        dt = (Nr + 1)*2.*Ts
        N = int(DT/dt)
        df = float(f2 - f1)/N

        if df == 0 or abs(df) >= min_df:
            pass
        else:
            df = signum(df)*min_df
            N = int(float(f2 - f1)/df)
            Nr = int((DT*df)/(2*Ts*(f2 - f1)))

        self.__set("delta_freq",FREQ(df,twos_complement=True))
        self.__set("ramp_rate_clock",Nr)
        self.__set("triangle",1)

        if update_chip: self.__program_chip()


    def set_FSK(self,value):
        """
        Set the FSK (pin 29) to value.
        Works only for the DDS-es that have jumper W2 enabled!
        """
        if not self.__internal_FSK:
            raise Error("set_FSK can be called only for DDS-es that use an internal FSK")
        
        if value:
            v = 1
        else:
            v = 0
            
        if v == self.__FSK: return
        self.__FSK = v
        self.__program_chip(force = True)
        
    def send_update_clock(self):
        bcode = self.__get_bus_address("23")
        self.command(bcode,offset=2)

###############################################################################
############################## INTERNAL #######################################
###############################################################################
    def __get_register_field(self,f):
        addr = f[0:2]
        if not addr in self.__registers:
            self.__registers[addr] = Register(addr)
        R = self.__registers[addr]

        if len(f) == 2:
            (s,e) = (0,7)
        elif len(f) == 5:
            p = int(f[3:-1])
            (s,e) = (p,p)
        elif len(f) > 5:
            (s,e) = map(int,f[3:-1].split(":"))
        else:
            raise InternalError("Cannot find register info from '%s'" % f)
            
        return R.get_register_field(s,e)

    def __create_field(self,name,field_desc):
        
        field_type_info = {
            "int" : {"valid_parms" : ["reg_fields","default"]},
            "int_2c" : {"valid_parms" : ["reg_fields","default"]},
            "small_int" : {"valid_parms" : ["bits","default"]},
            "bit" : {"valid_parms" : ["address","default"]},
            }

        type = field_desc.get("type")
        if not type in field_type_info:
            raise InternalError("Unknown field type '%s'" % type)
        for k in field_desc:
            if k == "type" : continue
            if not k in field_type_info[type]["valid_parms"]:
                raise InternalError("Unrecognized field_desc parameter '%s' for type '%s'" % (k,type))

        if type == "int":
            reg_fields = field_desc["reg_fields"]
            if not isinstance(reg_fields,list):
                raise InternalError("[%s] 'reg_fields' must be a list" % name)
            the_field = ProgrammableField(
                type,name,
                register_fields=[self.__get_register_field(f) 
                                 for f in reg_fields],
                default=field_desc.get("default",0))
        
        elif type == "int_2c":
            reg_fields = field_desc["reg_fields"]
            if not isinstance(reg_fields,list):
                raise InternalError("[%s] 'reg_fields' must be a list" % name)
            the_field = ProgrammableField(
                type,name,
                register_fields=[self.__get_register_field(f) 
                                 for f in reg_fields],
                default=field_desc.get("default",0))
        
        elif type == "small_int":
            the_field = ProgrammableField(
                type,name,
                register_fields=[self.__get_register_field(field_desc["bits"])],
                default=field_desc.get("default",0))
            
        elif type == "bit":
            the_field = ProgrammableField(
                type,name,
                register_fields = [self.__get_register_field(field_desc["address"])],
                default = field_desc.get("default",0))
        else:
            raise InternalError("Unrecognized parameter type '%s' in field_desc: %s" % (type,field_desc))

        return the_field

    def __set(self,name,value):
        self.__fields[name].set(value)

    def __get(self,name):
        return self.__fields[name].value()

    def __get_bus_address(self,hex_address):
        a = int(hex_address,16)
        if self.__internal_FSK and self.__FSK:
            a += int("40",16)
        return a

    def __set_register(self,reg_addr_hex,value):
        data = self.__get_bus_address(reg_addr_hex) + (value<<8)
        self.__load_data(data)

    def __load_data(self,data):
        # A0 = 1, A1 = 0
        self.command(data,offset=1)

    def __program_chip(self,force=False):
        changed_q = False
        for R in self.__registers.values():
            if not R.clean_q():
                value = R.value()
                if value is None:
                    raise Exception("Register '%s' has no value!" % R)
                self.__set_register(R.hex_address,value)
                R.mark_as_clean()
                changed_q = True

        if force or changed_q:
            self.send_update_clock()

    def __freq_to_register_value(self,freq,twos_complement=False):
        """
        Returns an integer that can be used to program the 6 byte
        frequency registers.
        """
        if twos_complement:
            c1 = float(2**47)
        else:
            c1 = float(2**48)
        return int(freq*(c1/self.__SYSCLK))

    def __get_frequency_resolution(self):
        c1 = float(2**48)
        return self.__SYSCLK/c1
    
if __name__ == "__main__":
    from Recipe import Recipe
    R = Recipe(r"D:\tmp\bcode.utb")
    R.start()
    D = DDS(address=30,refclock=15*10**6,refclock_multiplier=20)
    reg = Register("1f",D)
    reg.set(4,0,5)
    reg.set_bit(5,1)
    reg.set_bit(6,1)
    R.end()
    print reg
