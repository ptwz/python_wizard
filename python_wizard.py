#import numpy as sp
import scipy as sp
from scipy import signal
from scipy.io import wavfile
from collections import OrderedDict
import copy

class userSettings(object):
    preEmphasis = True
    pitchValue = 0
    unvoicedThreshold = 0.3
    windowWidth = 2
    normalizeUnvoicedRMS = False
    normalizeVoicedRMS = False
    includeExplicitStopFrame = True
    preEmphasis = False
    preEmphasisAlpha = -0.9373
    overridePitch = False
    pitchOffset = 0
    maximumPitchInHZ = 500
    minimumPitchInHZ = 50
    frameRate = 25
    subMultipleThreshold = 0.9
    

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

        if downsample_factor>1:
            data = sp.signal.decimate(d2, int(downsample_factor), zero_phase=True)
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

#    def getCoefficientsFor(x, t=1):
        #r=sp.corrcoef(sp.array([x[0:len(x)-t], x[t:len(x)]]))
        #return r[0][1]
#        yield

    def sumOfSquaresFor(self):
        return sp.square(self.samples[self.start:self.end]).sum()

    def getCoefficientsFor(self):
        coefficients = [0]*11
        for i in range(0,11):
            coefficients[i] = self.aForLag(i)
        return coefficients

    def aForLag(self, lag):
        samples = self.size - lag
        return sum(self.samples[0:samples] * self.samples[lag:samples+lag])

    def getNormalizedCoefficientsFor(self, minimumPeriod, maximumPeriod):
        coefficients = [0]*(maximumPeriod+1)

        for lag in range(0,maximumPeriod+1):
            if (lag<minimumPeriod):
                coefficients[lag] = 0.0
                continue

            s = 0
            sumOfSquaresBeginning = 0
            sumOfSquaresEnding = 0
            samples = self.size - lag
            for i in range(0, samples):
                s += self.samples[i] * self.samples[i+lag]
                sumOfSquaresBeginning += self.samples[i] ** 2
                sumOfSquaresEnding += self.samples[i+lag] ** 2
            coefficients[lag] = s / sp.sqrt(sumOfSquaresBeginning * sumOfSquaresEnding)
        return coefficients

class Filterer(object):
    def __init__(self, buf, lowPassCutoffInHZ, highPassCutoffInHZ, gain, order=5, ):
        self.gain = gain
        self.buf = buf
        nyq = 0.5 * buf.sampleRate
        low = lowPassCutoffInHZ / nyq
        # Avoid highpass frequency above nyqist-freq, this leads to
        # weird behavior
        high = min( (highPassCutoffInHZ/ nyq, 1) )
        self.b, self.a = signal.butter(order, [low, high], btype='band')

    def process(self):
        myFilter = lambda x: signal.filtfilt(self.b, self.a, x)
        return Buffer.copy(self.buf, applyFilter=myFilter)

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

    def estimate(self):
        bestPeriod = int(self.bestPeriod())
        maximumMultiple = bestPeriod / self.minimumPeriod()

        found = False

        estimate = self.interpolated()
        # NaN check???!! if (estimate != estimate) return 0.0; 
        while not found and maximumMultiple >= 1:
            subMultiplesAreStrong = True
            for i in range(0, maximumMultiple):
                subMultiplePeriod = int( sp.floor( (i+1) * estimate / maximumMultiple + .5) )
                try:
                    curr = self._normalizedCoefficients[subMultiplePeriod]
                except IndexError:
                    curr = None
                if (curr is not None) and ( curr < userSettings.subMultipleThreshold * self._normalizedCoefficients[bestPeriod]):
                    subMultiplesAreStrong = False
            if subMultiplesAreStrong:
                estimate /= maximumMultiple
                found = True
            maximumMultiple -= 1

        return estimate

    def getNormalizedCoefficients(self):
        minimumPeriod = self.minimumPeriod() - 1
        maximumPeriod = self.maximumPeriod() + 1
        return self.buf.getNormalizedCoefficientsFor(minimumPeriod, maximumPeriod)

    def bestPeriod(self):
        if self._bestPeriod is None:
            bestPeriod = self.minimumPeriod()
            startPeriod = bestPeriod + 1
            maximumPeriod = self.maximumPeriod()

            for period in range(startPeriod, maximumPeriod):
                if (self._normalizedCoefficients[period] > self._normalizedCoefficients[bestPeriod]):
                    bestPeriod = period
            self._bestPeriod = int(bestPeriod)

        return self._bestPeriod

    def maxPitchInHZ(self):
        return userSettings.maximumPitchInHZ

    def minPitchInHZ(self):
        return userSettings.minimumPitchInHZ

    def minimumPeriod(self):
        return int(sp.floor(self.buf.sampleRate / userSettings.maximumPitchInHZ - 1))

    def maximumPeriod(self):
        return int(sp.floor(self.buf.sampleRate / userSettings.minimumPitchInHZ + 1))


def ClosestValueFinder(actual, table):
    if actual < table[0]:
        return 0
    for i in range(0, len(table)):
        previous = table[ i - 1 ]
        if (table[i] - actual) < (actual - previous):
            return i
        else:
            return i-1

    return len(table)-1

class CodingTable(object):
    kStopFrameIndex = 15
    kParameterGain = 'gain'

    k1 = ( -0.97850, -0.97270, -0.97070, -0.96680, -0.96290, -0.95900,
    -0.95310, -0.94140, -0.93360, -0.92580, -0.91600, -0.90620, -0.89650,
    -0.88280, -0.86910, -0.85350, -0.80420, -0.74058, -0.66019, -0.56116,
    -0.44296, -0.30706, -0.15735, -0.00005, 0.15725, 0.30696, 0.44288,
    0.56109, 0.66013, 0.74054, 0.80416, 0.85350 )

    k2 = ( -0.64000, -0.58999, -0.53500, -0.47507, -0.41039, -0.34129, -0.26830, -0.19209, -0.11350, -0.03345, 0.04702, 0.12690, 0.20515, 0.28087, 0.35325, 0.42163, 0.48553, 0.54464, 0.59878, 0.64796, 0.69227, 0.73190, 0.76714, 0.79828, 0.82567, 0.84965, 0.87057, 0.88875, 0.90451, 0.91813, 0.92988, 0.98830)

    k3 = ( -0.86000, -0.75467, -0.64933, -0.54400, -0.43867, -0.33333, -0.22800, -0.12267, -0.01733, 0.08800, 0.19333, 0.29867, 0.40400, 0.50933, 0.61467, 0.72000)

    k4 = ( -0.64000, -0.53145, -0.42289, -0.31434, -0.20579, -0.09723, 0.01132, 0.11987, 0.22843, 0.33698, 0.44553, 0.55409, 0.66264, 0.77119, 0.87975, 0.98830)

    k5 = ( -0.64000, -0.54933, -0.45867, -0.36800, -0.27733, -0.18667, -0.09600, -0.00533, 0.08533, 0.17600, 0.26667, 0.35733, 0.44800, 0.53867, 0.62933, 0.72000)

    k6 = ( -0.50000, -0.41333, -0.32667, -0.24000, -0.15333, -0.06667, 0.02000, 0.10667, 0.19333, 0.28000, 0.36667, 0.45333, 0.54000, 0.62667, 0.71333, 0.80000)

    k7 = ( -0.60000, -0.50667, -0.41333, -0.32000, -0.22667, -0.13333, -0.04000, 0.05333, 0.14667, 0.24000, 0.33333, 0.42667, 0.52000, 0.61333, 0.70667, 0.80000)

    k8 = ( -0.50000, -0.31429, -0.12857, 0.05714, 0.24286, 0.42857, 0.61429, 0.80000)

    k9 = ( -0.50000, -0.34286, -0.18571, -0.02857, 0.12857, 0.28571, 0.44286, 0.60000)

    k10 = ( -0.40000, -0.25714, -0.11429, 0.02857, 0.17143, 0.31429, 0.45714, 0.60000)

    rms = ( 0.0, 52.0, 87.0, 123.0, 174.0, 246.0, 348.0, 491.0, 694.0, 981.0, 1385.0, 1957.0, 2764.0, 3904.0, 5514.0, 7789.0)

    pitch = ( 0.0, 1.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 36.0, 36.0, 38.0, 39.0, 40.0, 41.0, 42.0, 44.0, 46.0, 48.0, 50.0, 52.0, 53.0, 56.0, 58.0, 60.0, 62.0, 65.0, 67.0, 70.0, 72.0, 75.0, 78.0, 80.0, 83.0, 86.0, 89.0, 93.0, 97.0, 100.0, 104.0, 108.0, 113.0, 117.0, 121.0, 126.0, 131.0, 135.0, 140.0, 146.0, 151.0, 157)

    bits = ( 4, 1, 6, 5, 5, 4, 4, 4, 4, 4, 3, 3, 3)
    
    @classmethod
    def kSizeFor(cls, k):
        if k>10:
            raise Exception("RangeError")
        return 1 << cls.bits[k+2]

    @classmethod
    def rmsSize(cls):
        return 1 << cls.bits[0]

    @classmethod
    def pitchSize(cls):
        return 1 << cls.bits[2]

    @classmethod
    def kBinFor(cls, k):
        mapping = { 1:cls.k1, 2:cls.k2, 3:cls.k3, 4:cls.k4, 5:cls.k5, 6:cls.k6, 7:cls.k7, 8:cls.k8, 9:cls.k9, 10:cls.k10}
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


class Reflector(object):
    kNumberOfKParameters = 11

    def __init__(self, k=None, rms=None, limitRMS=None):
        # TODO From config!!
        self.unvoicedThreshold = userSettings.unvoicedThreshold
        if (k is None):
            assert(rms is None)
            assert(limitRMS is None)
            self.ks = [0] * self.kNumberOfKParameters;
        else:
            assert(rms is not None)
            assert(limitRMS is not None)
            self.rms = rms
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
    
    def setRms(self, rms):
        self.rms = rms

    def rms(self):
        if self.limitRMS and self.rms >= CodingTable.rms[CodingTable.kStopFrameIndex - 1]:
            return CodingTable.rms[CodingTable.kStopFrameIndex - 1]
        else:
            return self.rms

    def isVoiced(self):
        return not self.isUnvoiced()

    def isUnvoiced(self):
        return self.ks[1] >= self.unvoicedThreshold

class FrameData(object):
    @classmethod
    def stopFrame(cls):
        reflector = Reflector()
        reflector.setRms ( CodingTable.rms[CodingTable.kStopFrameIndex] )
        fd = cls(reflector=reflector, pitch=0, repeat=False)
        fd.stopFrame = True
        return fd

    @classmethod
    def frameForDecoding(cls):
        reflector = Reflector()
        fd = cls(reflector=reflector, pitch=0, repeat=False)
        fd.decodeFrame = True
        return fd
    
    def __init__(self, reflector, pitch, repeat):
        self.reflector = reflector
        self.pitch = pitch
        print pitch
        self.repeat = repeat
        self._parameters = None

    def parameters(self):
        if self._parameters is None:
            self._parameters = self.parametersWithTranslate(False)
        return self._parameters

    def translatedParameters(self):
        if self._translatedParameters is None:
            self._translatedParameters = self.parametersWithTranslate(True)
        return self._translatedParameters

    def parametersWithTranslate(self, translate):
        parameters = {}
        parameters[CodingTable.kParameterGain] = self.parameterizedValueForRMS(self.reflector.rms, translate=translate)
    
        if parameters[CodingTable.kParameterGain] > 0:
            parameters[CodingTable.kParameterRepeat] = self.parameterizedValueForRepeat(self.repeat)
            parameters[CodingTable.kParameterPitch] = self.parameterizedValueForPitch(self.pitch, translate)

            if not parameters[CodingTable.kParameterRepeat]:
                ks = self.kParametersFrom(1, 4, translate=translate)
                parameters.update(ks)
                if ( parameters[CodingTable.kParameterPitch] != 0  and (self.isForDecoding or self.reflector.isVoiced) ):
                    ks = self.kParametersFrom(5, 10, translate=translate)
                    parameters.update(ks)
    
        return copy.deepcopy(parameters)

    def setParameter(self, parameter, value = None, translatedValue = None):
        self.parameters = None
        
        if parameter == CodingTable.kParameterGain:
            if translatedValue is None:
                index = int(value)
                rms = CodingTable.rms(index)
            else:
                rms = translatedValue
            self.reflector.rms = float(rms)
                
        elif parameter == CodingTable.kParameterRepeat:
            self.repeat = bool(value)

        elif parameter == CodingTable.kParameterPitch:
            if translatedValue is None:
                pitch = CodingTable.pitch[int(value)]
            else:
                pitch = translatedValue
            self.pitch = float(pitch)

        else:
            bin_no = int(parameter[1])
            if translatedValue is None:
                index = int(value)
                k = CodingTable.kBinFor(index)
            else:
                l = float(translatedValue)
            self.reflector.ks[bin_no] = float(k)

    def parameterizedValueForK(self, k, bin_no, translate):
        index = ClosestValueFinder(k, table=CodingTable.kBinFor(bin_no))
        if translate:
            return CodingTable.kBinFor(bin_no)[index]
        else:
            return index

    def parameterizedValueForRMS(self, rms, translate):
        index = ClosestValueFinder(rms, table=CodingTable.rms)
        print rms, index
        if translate:
            return CodingTable.rms[index]
        else:
            return index

    def parameterizedValueForPitch(self, pitch,translate):
        index = 0
        if self.isForDecoding:
            if pitch==0:
                return 0
            if userSettings.overridePitch:
                index = int(userSettings.overridePitch)
                return CodingTable.pitch[index]
        elif self.reflector.isUnvoiced() or pitch==0:
            return 0

        if userSettings.overridePitch:
            offset = 0
        else:
            offset = userSettings.pitchOffset

        index = ClosestValueFinder(pitch, table=CodingTable.pitch)

        index += offset

        if index > 63: index = 63
        if index < 0: index = 0

        if translate:
            return CodingTable.pitch[index]
        else:
            return index

    def parameterizedValueForRepeat(self, repeat):
        return bool(repeat)

    def kParametersFrom(self, frm, to, translate):
        if self.isStopFrame: return None
        parameters = {}
        for k in range(frm, to+1):
            key = self.parameterKeyForK(k)
            parameters[key] = self.parameterizedValueForK(self.reflector.ks[k], bin_no=k, translate=translate)
        return copy.deepcopy(parameters)

    def parameterKeyForK(self, k):
        return "k{}".format(int(k))

class HammingWindow(object):
    @classmethod
    def processBuffer(cls, buf):
        for i in range(0, len(buf)):
            window =  0.54 - 0.46 * sp.cos(2 * sp.pi * i / (len(buf) - 1))
            buf.samples[i] *= window

class PreEmphasizer(object):
    @classmethod
    def processBuffer(cls, buf):
        preEnergy = buf.energy()

        alpha = cls.alpha()
        unmodifiedPreviousSample = buf.samples[0]
        tempSample = None
        for i in range(1, len(buffer)):
            tempSample = buffer.sample[i]
            buffer.samples[i] += (alpha * unmodifiedPreviousSample)
            unmodifiedPreviousSample = tempSample

        cls.scaleBuffer(buf, preEnergy, buf.energy())

    @classmethod
    def alpha(cls):
        return userSettings.preEmphasisAlpha

    @classmethod
    def scaleBuffer(buf, preEnergy, postEnergy):
        scale = sp.square(preEnergy / postEnergy)

        for i in range(0, len(buf)):
            buf.values[i] *= scale


class RMSNormalizer(object):
    @classmethod
    def normalize(cls, frameData, Voiced):
        maximum = max( [ x.rms for x in frameData if x.isVoiced() == Voiced ] )
    
        if maximum <= 0:
            return

        if Voiced:
            ref = cls.maxRMSIndex()
        else:
            ref = cls.maxUnvoicedRMSIndex()
        scale = CodingTable.rms[cls.ref] / maximum

        for frame in FrameData:
            if not frame.reflector.isVoiced() == Voiced:
                frame.reflector.rms *= scale
    
    @classmethod
    def applyUnvoicedMultiplier(cls, frameData):
        mutiplier = cls.unvoicedRMSMultiplier()
        for frame in frameData:
            if frame.reflector.isUnvoiced():
                frame.reflector.rms *= mutiplier

    @classmethod
    def maxRMSIndex(cls):
        return userSettings.rmsLimit

    @classmethod
    def maxUnvoicedRMSIndex(cls):
        return userSettings.unvoicedRMSLimit

    @classmethod
    def unvoicedMultiplier(cls):
        return userSettings.unvoicedRMSMultiplier

class Segmenter(object):
    def __init__(self, buf, windowWidth):
        milliseconds = userSettings.frameRate
        self.size = int(sp.ceil(buf.sampleRate / 1e3 * milliseconds))
        self.buf = buf
        self.windowWidth = windowWidth

    def eachSegment(self):
        length = self.numberOfSegments()
        for i in range (0, length):
            samples = self.samplesForSegment(i)
            buf = Buffer(samples = samples, size=self.sizeForWindow, sampleRate=self.buf.sampleRate)
            yield (buf, i)

    def samplesForSegment(self, index):
        length = self.sizeForWindow()
        samples = sp.zeros(length)
        for i in range(0, length):
            sampleIndex = index * self.size + i
            samples[i] = self.buf.samples[sampleIndex] if sampleIndex < self.buf.size else 0.0
        return samples

    def sizeForWindow(self):
        return int(self.size * self.windowWidth)

    def numberOfSegments(self):
        return int(sp.ceil(float(self.buf.size) / float(self.size)))

class Processor(object):
    def __init__(self, buf):
        self.mainBuffer = buf
        self.pitchTable = None
        self.pitchBuffer = Buffer.copy(buf)
        
        if userSettings.preEmphasis:
            PreEmphasizer.processBuffer(buf)
        
        self.pitchTable = {}
        wrappedPitch = False
        if userSettings.overridePitch:
            wrappedPitch = userSettings.pitchValue
        else:
            self.pitchTable = self.pitchTableForBuffer(self.pitchBuffer)
        
        coefficients = sp.zeros(11)

        segmenter = Segmenter(buf=self.mainBuffer, windowWidth=userSettings.windowWidth)

        frames = []
        for (cur_buf, i) in segmenter.eachSegment():
            HammingWindow.processBuffer(cur_buf)
            coefficients = cur_buf.getCoefficientsFor()
            reflector = Reflector.translateCoefficients(coefficients, cur_buf.size)
            
            if wrappedPitch:
                pitch = int(wrappedPitch)
            else:
                pitch = self.pitchTable[i]

            frameData = FrameData(reflector, pitch, repeat=False)

            frames.append(frameData)
        
        if userSettings.includeExplicitStopFrame:
            frames.append(FrameData.stopFrame)

        self.frames = frames

    def pitchTableForBuffer(self, pitchBuffer):
        filterer = Filterer(pitchBuffer, lowPassCutoffInHZ=userSettings.minimumPitchInHZ, highPassCutoffInHZ=userSettings.maximumPitchInHZ, gain=1)
        buf = filterer.process()

        segmenter = Segmenter(buf, windowWidth=2)
        pitchTable = sp.zeros(segmenter.numberOfSegments())

        for (buf, index) in segmenter.eachSegment():
            pitchTable[index] = PitchEstimator.pitchForPeriod(buf)

        return pitchTable


    def process(self):
        return(self.frameData)

class BitHelpers(object):
    @classmethod
    def valueToBinary(value, bits):
        return format(value, "0{}b".format(bits))

    @classmethod
    def valueForBinary(binary):
        return int(binary, 2)

class FrameDataBinaryEncoder(object):
    @classmethod
    def process(cls, parametersList):
        bits = CodingTable.bits
        binary = ""
        for parameters in parametersList:
            parametersList = CodingTable.parameters()
            for (param_name, idx) in zip(parametersList, range(len(parametersList))):
                if param_name not in parameters:
                    break
                value = parameters[param_name]
                binaryValue = BitHelpers.valueToBinary(value, bits[idx])
                binary += binaryValue
        return cls.nibblesFrom(binary)

    @classmethod
    def nibblesFrom(cls, binary):
        nibbles = []
        while len(binary) >= 4:
            nibble = binary[0:4]
            binary = binary[4:]
            nibbles.append(binary)
        return nibbles

class BitPacker(object):
    delimiter = ","

    @classmethod
    def pack(cls, frameData):
        parametersList = frameData.parameters()
        print parametersList
        #binary = FrameDataBinaryEncoder.process(parametersList)
        #hexform = HexConverter.process(binary)
        #reverse = NibbleBitReverser.process(hexform)
        #switched = NibbleSwitcher.process(reverse)
        #output = HexFormatter.process(switched)

        #return cls.delimiter.join(cls.output)



b=Buffer.fromWave('/Users/peter/Downloads/BlueWizard-master/unprocessed/ces.wav')
x=Processor(b)
print "done"
for frame in x.frames:
    print BitPacker.pack(frame)
