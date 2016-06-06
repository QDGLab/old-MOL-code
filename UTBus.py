"""
The instance of this class controls the state of the UTBus.
"""
from Singleton import Singleton

class UTBus_class(Singleton):
    def init(self,reference_frequency,sampling_rate_divider):
        self.__reference_frequency = float(reference_frequency)
        self.__sampling_rate_divider = sampling_rate_divider
        self.__sampling_frequency = float(reference_frequency)/sampling_rate_divider
    def __get_sampling_frequency(self):
        return self.__sampling_frequency

    sampling_frequency = property(__get_sampling_frequency)


UTBus = UTBus_class()
