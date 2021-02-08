from pywizard.userSettings import settings
from lpcplayer.tables import tables

class CodingTable(object):
    kStopFrameIndex = 15

    rms = ( 0.0, 52.0, 87.0, 123.0, 174.0, 246.0, 348.0, 491.0, 694.0, 981.0, 1385.0, 1957.0, 2764.0, 3904.0, 5514.0, 7789.0)

    def __init__(self, name):
        chip = tables[name]

        for k in range(1,11):
            ks=list(chip.ktable[k-1])
            for i, k_value in enumerate(ks):
                ks[i]=k_value/512
            setattr(self, 'k'+str(k), ks)

        self.pitch=chip.pitchtable
        self.bits=(chip.energy_bits,)\
                         +(1,)\
                         +(chip.pitch_bits,)\
                         + chip.kbits

    def kSizeFor(self, k):
        if k>10:
            raise Exception("RangeError")
        return 1 << self.bits[k+2]

    def rmsSize(self):
        return 1 << self.bits[0]

    def pitchSize(self):
        return 1 << self.bits[2]

    def kBinFor(self, k):
        mapping = { 1:self.k1, 2:self.k2, 3:self.k3, 4:self.k4, 5:self.k5, 6:self.k6, 7:self.k7, 8:self.k8, 9:self.k9, 10:self.k10}
        return mapping[k]

    @classmethod
    def parameters(cls):
        return [
             'kParameterGain',
             'kParameterRepeat',
             'kParameterPitch',
             'kParameterK1',
             'kParameterK2',
             'kParameterK3',
             'kParameterK4',
             'kParameterK5',
             'kParameterK6',
             'kParameterK7',
             'kParameterK8',
             'kParameterK9',
             'kParameterK10'
              ]

    bits = ( 4, 1, 6, 5, 5, 4, 4, 4, 4, 4, 3, 3, 3)

