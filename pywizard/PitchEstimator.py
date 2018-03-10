from scipy import signal
from userSettings import settings
import logging
import scipy as sp

class PitchEstimator(object):
    @classmethod
    def pitchForPeriod(cls, buf):
        return cls(buf).estimate()

    def __init__(self, buf):
        self._bestPeriod = None
        self.buf = buf
        if settings.pitchEstimate=="fft":
            self._fft = self.buf.fft()
            self.estimate = self.estimate_fft
        else:
            self._normalizedCoefficients = self.getNormalizedCoefficients()
            self.estimate = self.estimate_autocorr

    def isOutOfRange(self):
        x = self.bestPeriod()
        return ( (self._normalizedCoefficients[x] < self._normalizedCoefficients[x-1])
                 and
                 (self._normalizedCoefficients[x] < self._normalizedCoefficients[x+1]) )

    def interpolated(self):
        bestPeriod = int(self.bestPeriod())
        middle = self._normalizedCoefficients[bestPeriod]
        left = self._normalizedCoefficients[bestPeriod - 1]
        right  = self._normalizedCoefficients[bestPeriod + 1]

        if ( (2*middle - left - right) == 0):
            return bestPeriod
        else:
            return bestPeriod + .5 * ( right - left) / (2 * middle - left - right)

    def estimate_fft(self):
        fftlen = len(self._fft)
        fft_half = self._fft[0:fftlen/2]
        maximum_idx = fft_half.argsort()[-1]
        period = int(fftlen / maximum_idx)
        logging.debug("estimate_fft: maximum_idx={}, perid={}".format(maximum_idx, period))
        return(period)

    def estimate_autocorr(self):
        bestPeriod = int(self.bestPeriod())
        maximumMultiple = bestPeriod / self.minimumPeriod()

        found = False

        estimate = self.interpolated()
        if sp.isnan(estimate):
            return 0.0
        while not found and maximumMultiple >= 1:
            subMultiplesAreStrong = True
            for i in range(0, maximumMultiple):
                logging.debug("estimate={} maximumMultiple={}".format(estimate, maximumMultiple))
                subMultiplePeriod = int( sp.floor( (i+1) * estimate / maximumMultiple + .5) )
                try:
                    curr = self._normalizedCoefficients[subMultiplePeriod]
                except IndexError:
                    curr = None
                if (curr is not None) and ( curr < settings.subMultipleThreshold * self._normalizedCoefficients[bestPeriod]):
                    subMultiplesAreStrong = False
            if subMultiplesAreStrong:
                estimate /= maximumMultiple
            maximumMultiple -= 1

        return estimate

    def getNormalizedCoefficients(self):
        minimumPeriod = self.minimumPeriod() - 1
        maximumPeriod = self.maximumPeriod() + 1
        return self.buf.getNormalizedCoefficientsFor(minimumPeriod, maximumPeriod)

    def bestPeriod(self):
        if self._bestPeriod is None:
            bestPeriod = self.minimumPeriod()
            maximumPeriod = self.maximumPeriod()

            bestPeriod = self._normalizedCoefficients.index(max(self._normalizedCoefficients))
            logging.debug("_normalizedCoefficients = {}".format(self._normalizedCoefficients))
            logging.debug("bestPeriod={} minimumPeriod={} maximumPeriod={}".format(bestPeriod, self.minimumPeriod(), self.maximumPeriod()))
            if bestPeriod < self.minimumPeriod():
                bestPeriod = self.minimumPeriod()
            if bestPeriod > maximumPeriod:
                bestPeriod = maximumPeriod

            self._bestPeriod = int(bestPeriod)

        return self._bestPeriod

    def maxPitchInHZ(self):
        return settings.maximumPitchInHZ

    def minPitchInHZ(self):
        return settings.minimumPitchInHZ

    def minimumPeriod(self):
        return int(sp.floor(self.buf.sampleRate / settings.maximumPitchInHZ - 1))

    def maximumPeriod(self):
        return int(sp.floor(self.buf.sampleRate / settings.minimumPitchInHZ + 1))


def ClosestValueFinder(actual, table):
    if actual < table[0]:
        return 0

    return table.index(min(table, key=lambda x:abs(x-actual)))

