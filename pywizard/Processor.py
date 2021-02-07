from pywizard.Buffer import Buffer
from pywizard.Filterer import Filterer
from pywizard.Reflector import Reflector
from pywizard.Segmenter import Segmenter
from pywizard.PitchEstimator import PitchEstimator
from pywizard.userSettings import settings
from pywizard.HammingWindow import HammingWindow
from pywizard.FrameData import FrameData
from pywizard.PreEmphasizer import PreEmphasizer
from pywizard.CodingTable import CodingTable
import scipy as sp
import logging

class Processor(object):
    def __init__(self, buf, model=None):
        self.mainBuffer = buf
        self.pitchTable = None
        self.pitchBuffer = Buffer.copy(buf)
        self.codingTable = CodingTable()

        if settings.preEmphasis:
            PreEmphasizer.processBuffer(buf)

        self.pitchTable = {}
        wrappedPitch = False
        if settings.overridePitch:
            wrappedPitch = settings.pitchValue
        else:
            self.pitchTable = self.pitchTableForBuffer(self.pitchBuffer)

        coefficients = sp.zeros(11)

        segmenter = Segmenter(buf=self.mainBuffer, windowWidth=settings.windowWidth)

        frames = []
        for (cur_buf, i) in segmenter.eachSegment():
            HammingWindow.processBuffer(cur_buf)
            coefficients = cur_buf.getCoefficientsFor()
            reflector = Reflector.translateCoefficients(self.codingTable, coefficients, cur_buf.size)

            if wrappedPitch:
                pitch = int(wrappedPitch)
            else:
                pitch = self.pitchTable[i]

            frameData = FrameData(reflector, pitch, repeat=False)

            frames.append(frameData)

        if settings.includeExplicitStopFrame:
            frames.append(frameData.stopFrame())

        self.frames = frames

    def pitchTableForBuffer(self, pitchBuffer):
        filterer = Filterer(pitchBuffer, lowPassCutoffInHZ=settings.minimumPitchInHZ, highPassCutoffInHZ=settings.maximumPitchInHZ, gain=1)
        buf = filterer.process()

        segmenter = Segmenter(buf, windowWidth=2)
        pitchTable = sp.zeros(segmenter.numberOfSegments())

        for (buf, index) in segmenter.eachSegment():
            pitchTable[index] = PitchEstimator.pitchForPeriod(buf)

        return pitchTable


    def process(self):
        return(self.frameData)

