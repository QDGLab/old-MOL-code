"""
"""

from UTBusDevice import UTBusDevice

class AnalogOutput(UTBusDevice):

    def __init__(self,**parms):
        address = parms.pop("address")
        UTBusDevice.__init__(self,address)
        self.bit_depth = 16
        self.min = -10.
        self.max = 10.
        self.delta = (self.max - self.min)/(-1 + 2**self.bit_depth)

    def set_value(self,value):
        self.command(value)

    def set_scaled_value(self,value):
        if value < self.min or value > self.max:
            raise "Value '%f' outside of the allowed range" % value
        v = int((value - self.min)/self.delta)
        self.command(v)

    def set_scaled_values(self,values):
        scaled_values = []
        for value in values:
            if value < self.min or value > self.max:
                raise "Value '%f' outside of the allowed range" % value
            v = int((value - self.min)/self.delta)
            scaled_values.append(v)

        self.command(scaled_values)
