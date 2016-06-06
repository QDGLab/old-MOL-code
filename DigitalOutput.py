"""
"""
from UTBusDevice import UTBusDevice

class DigitalOutput(UTBusDevice):

    def __init__(self,**parms):
        address = parms.pop("address")
        UTBusDevice.__init__(self,address)
        self.bits = [0 for i in range(16)]

    def set_bit(self,bit_index,state):
        self.bits[bit_index] = state
        value = self.bits[0]
        p = 1
        for i in range(1,16):
            p *= 2
            if self.bits[i]:
                value += p

        self.command(value)

    def reset(self):
        for i in range(len(self.bits)):
            self.set_bit(i,0)
