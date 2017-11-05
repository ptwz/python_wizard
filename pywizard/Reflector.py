import scipy as sp
from CodingTable import CodingTable
from userSettings import settings

class Reflector(object):
    """
    Implements the reflector parameter guessing for the LPC
    algorithm.

    Test if stop frames do not accidentally created
    >>> from CodingTable import CodingTable

    >>> r = Reflector()

    >>> r.rms = CodingTable.rms[15]

    >>> r.limitRMS = True

    >>> r.rms == CodingTable.rms[14]
    True
    """
    kNumberOfKParameters = 11

    def __init__(self, k=None, rms=None, limitRMS=None):
        # TODO From config!!
        self.unvoicedThreshold = settings.unvoicedThreshold
        if (k is None):
            assert(rms is None)
            assert(limitRMS is None)
            self.limitRMS = False
            self.ks = [0] * self.kNumberOfKParameters;
        else:
            assert(rms is not None)
            assert(limitRMS is not None)
            self._rms = rms
            self.ks = k
            self.limitRMS = limitRMS

    @classmethod
    def formattedRMS(cls, rms, numberOfSamples):
        return sp.sqrt( rms / numberOfSamples) * ( 1 << 15 )

    @classmethod
    def translateCoefficients(cls, r, numberOfSamples):
        '''Leroux Guegen algorithm for finding K's'''

        k = [0.0] * 11;
        b = [0.0] * 11;
        d = [0.0] * 12;

        k[1] = -r[1] / r[0]
        d[1] = r[1]
        d[2] = r[0] + (k[1] * r[1])

        for i in range(2, 11):
            y = r[i]
            b[1] = y

            for j in range(1, i):
                b[j + 1] = d[j] + (k[j] * y)
                y = y + (k[j] * d[j])
                d[j] = b[j]

            k[i] = -y / d[i]
            d[i + 1] = d[i] + (k[i] * y)
            d[i] = b[i]
        rms = cls.formattedRMS( d[11], numberOfSamples )
        return cls(k=k, rms=rms, limitRMS=True )


    @property
    def rms(self):
        if self.limitRMS and self._rms >= CodingTable.rms[CodingTable.kStopFrameIndex - 1]:
            return CodingTable.rms[CodingTable.kStopFrameIndex - 1]
        else:
            return self._rms

    @rms.setter
    def rms(self, rms):
        self._rms = rms

    def isVoiced(self):
        return not self.isUnvoiced()

    def isUnvoiced(self):
        return self.ks[1] >= self.unvoicedThreshold

