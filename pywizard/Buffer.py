from scipy import signal
from scipy.io import wavfile
import scipy as sp
import logging

class Buffer(object):
    @classmethod
    def copy(cls, orig, applyFilter=None):
        if applyFilter is None:
            return cls(size=orig.size, sampleRate=orig.sampleRate, samples=orig.samples, start=orig.start, end=orig.end)
        else:
            return cls(size=orig.size, sampleRate=orig.sampleRate, samples=applyFilter(orig.samples), start=orig.start, end=orig.end)

    @classmethod
    def fromWave(cls, filename):
        (rate,data)=wavfile.read(filename)

        expected_rate = 8.0e3
        downsample_factor = rate/expected_rate
        assert(downsample_factor>=1)

        d2 = sp.array(data, 'float')
        if data.dtype.name == 'int16':
            d2 /= 2**15
        elif data.dtype.name == 'int32':
            d2 /= 2**31
        elif data.dtype.name == 'uint8':
            d2 -= 128
            d2 /= 127

        assert(max(d2) <= 1)

        if downsample_factor>1:
            data = sp.signal.resample(d2, int(len(d2)/downsample_factor))
            logging.debug("downsampled: was {} samples, now {} samples".format(len(d2), len(data)))
        else:
            data = d2

        return cls(sampleRate=expected_rate, samples=data)

    def __init__(self, size=None, sampleRate=None, samples=None, start=None, end=None):
        self.sampleRate = sampleRate
        if (samples is None):
            # Equivalent to initWithSize
            assert( size is not None and sampleRate is not None)
            self.size = size
            self.samples = sp.zeros(samples, dtype=float)
        else:
            self.samples = sp.array(samples)
            self.size = len(self.samples)

        if start is None:
            self.start = 0
        else:
            self.start = start
        if end is None:
            self.end = self.size
        else:
            self.end = end

    def __len__(self):
        return(self.size)

    def copySamples(self, samples):
        self.samples = samples[self.start:self.end]

    def energy(self):
        return self.sumOfSquaresFor()

    def sumOfSquaresFor(self):
        return sp.square(self.samples[self.start:self.end]).sum()

    def getCoefficientsFor(self):
        logging.debug("getCoefficientsFor max(self.samples)={}".format(max(self.samples)))
        coefficients = [0]*11
        for i in range(0,11):
            coefficients[i] = self.aForLag(i)
        return coefficients

    def aForLag(self, lag):
        samples = self.size - lag
        return sum(self.samples[0:samples] * self.samples[lag:samples+lag])

    def rms(self, x):
        return sp.sqrt(x.dot(x)/x.size)

    def getNormalizedCoefficientsFor(self, minimumPeriod, maximumPeriod):
        coefficients = [0]*(maximumPeriod+1)

        for lag in range(0,maximumPeriod+1):
            if (lag<minimumPeriod):
                coefficients[lag] = 0.0
                continue

            s = sum(self.samples[:-lag] * self.samples[lag:])
            rmsBeginning = self.rms(self.samples[:-lag])
            rmsEnding = self.rms(self.samples[lag:])
            
            if rmsBeginning * rmsEnding <= 1e-15:
                coefficients[lag] = sp.NaN
            else:
                coefficients[lag] = s / (rmsBeginning * rmsEnding)
        return coefficients

