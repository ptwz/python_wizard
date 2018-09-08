from pywizard.Reflector import Reflector
from copy import deepcopy
from pywizard.tools import ClosestValueFinder
from pywizard.CodingTable import CodingTable
from pywizard.FrameDataBinaryEncoder import FrameDataBinaryEncoder
from pywizard.userSettings import settings

class FrameData(object):
    @classmethod
    def stopFrame(cls):
        reflector = Reflector()
        reflector.rms = CodingTable.rms[CodingTable.kStopFrameIndex]
        fd = cls(reflector=reflector, pitch=0, repeat=False)
        fd.decodeFrame = False
        fd.stopFrame = True
        return fd

    @classmethod
    def frameForDecoding(cls):
        reflector = Reflector()
        fd = cls(reflector=reflector, pitch=0, repeat=False)
        fd.decodeFrame = True
        return fd

    def __repr__(self):
        return "FrameData(reflector={}, pitch={}, repeat={}, parameters{})".format(self.reflector, self.pitch, self.repeat, self.parameters())

    def __init__(self, reflector, pitch, repeat, parameters=None):
        self.reflector = reflector
        self.pitch = pitch
        self.stopFrame = False
        self.decodeFrame = False
        self.repeat = repeat
        self._parameters = parameters

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
        parameters["kParameterGain"] = self.parameterizedValueForRMS(self.reflector.rms, translate=translate)

        if parameters["kParameterGain"] > 0:
            parameters["kParameterRepeat"] = self.parameterizedValueForRepeat(self.repeat)
            parameters["kParameterPitch"] = self.parameterizedValueForPitch(self.pitch, translate)

            if not parameters["kParameterRepeat"]:
                ks = self.kParametersFrom(1, 4, translate=translate)
                if ks is not None:
                    parameters.update(ks)
                if ( parameters["kParameterPitch"] != 0  and (self.decodeFrame or self.reflector.isVoiced) ):
                    ks = self.kParametersFrom(5, 10, translate=translate)
                    parameters.update(ks)

        return deepcopy(parameters)

    def setParameter(self, parameter, value = None, translatedValue = None):
        self.parameters = None

        if parameter == 'kParameterGain':
            if translatedValue is None:
                index = int(value)
                rms = CodingTable.rms(index)
            else:
                rms = translatedValue
            self.reflector.rms = float(rms)

        elif parameter == "kParameterRepeat":
            self.repeat = bool(value)

        elif parameter == "kParameterPitch":
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
                l = k[index]
            else:
                l = float(translatedValue)
            self.reflector.ks[bin_no] = float(l)

    def parameterizedValueForK(self, k, bin_no, translate):
        index = ClosestValueFinder(k, table=CodingTable.kBinFor(bin_no))
        if translate:
            return CodingTable.kBinFor(bin_no)[index]
        else:
            return index

    def parameterizedValueForRMS(self, rms, translate):
        index = ClosestValueFinder(rms, table=CodingTable.rms)
        if translate:
            return CodingTable.rms[index]
        else:
            return index

    def parameterizedValueForPitch(self, pitch,translate):
        index = 0
        if self.decodeFrame:
            if pitch==0:
                return 0
            if settings.overridePitch:
                index = int(settings.overridePitch)
                return CodingTable.pitch[index]
        elif self.reflector.isUnvoiced() or pitch==0:
            return 0

        if settings.overridePitch:
            offset = 0
        else:
            offset = settings.pitchOffset

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
        if self.stopFrame: return None
        parameters = {}
        for k in range(frm, to+1):
            key = self.parameterKeyForK(k)
            parameters[key] = self.parameterizedValueForK(self.reflector.ks[k], bin_no=k, translate=translate)
        return deepcopy(parameters)

    def parameterKeyForK(self, k):
        return "kParameterK{}".format(int(k))

