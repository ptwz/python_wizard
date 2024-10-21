from pywizard.userSettings import settings
import logging
import numpy as np


class PitchEstimator(object):
    @classmethod
    def pitchForPeriod(cls, buf):
        return cls(buf).estimate()

    def __init__(self, buf):
        self._bestPeriod = None
        self.buf = buf
        self._normalizedCoefficients = self.getNormalizedCoefficients()

    def isOutOfRange(self):
        x = self.bestPeriod()
        return ((self._normalizedCoefficients[x] < self._normalizedCoefficients[x-1])
                and
                (self._normalizedCoefficients[x] < self._normalizedCoefficients[x+1])
                )

    def interpolated(self):
        bestPeriod = int(self.bestPeriod())
        middle = self._normalizedCoefficients[bestPeriod]
        left = self._normalizedCoefficients[bestPeriod - 1]
        right = self._normalizedCoefficients[bestPeriod + 1]

        if (2*middle - left - right) == 0:
            return bestPeriod
        else:
            return bestPeriod + .5 * (right - left) / (2 * middle - left - right)

    def estimate(self):
        bestPeriod = int(self.bestPeriod())
        maximumMultiple = bestPeriod / self.minimumPeriod()

        found = False

        estimate = self.interpolated()
        if np.isnan(estimate):
            return 0.0
        while not found and maximumMultiple >= 1:
            subMultiplesAreStrong = True
            for i in range(0, int(maximumMultiple)):
                logging.debug("estimate={} maximumMultiple={}".format(estimate, maximumMultiple))
                subMultiplePeriod = int(np.floor((i+1) * estimate / maximumMultiple + .5))
                try:
                    curr = self._normalizedCoefficients[subMultiplePeriod]
                except IndexError:
                    curr = None
                if (curr is not None) and (curr < settings.subMultipleThreshold * self._normalizedCoefficients[bestPeriod]):
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
        return int(np.floor(self.buf.sampleRate / settings.maximumPitchInHZ - 1))

    def maximumPeriod(self):
        return int(np.floor(self.buf.sampleRate / settings.minimumPitchInHZ + 1))


def ClosestValueFinder(actual, table):
    if actual < table[0]:
        return 0

    return table.index(min(table, key=lambda x: abs(x-actual)))
