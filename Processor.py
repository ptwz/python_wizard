class Processor(object):
    def __init__(self, buf):
        self.mainBuffer = buf
        self.pitchTable = None
        self.pitchBuffer = Buffer.copy(buf)

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
            reflector = Reflector.translateCoefficients(coefficients, cur_buf.size)

            if wrappedPitch:
                pitch = int(wrappedPitch)
            else:
                pitch = self.pitchTable[i]

            frameData = FrameData(reflector, pitch, repeat=False)

            frames.append(frameData)

        if settings.includeExplicitStopFrame:
            frames.append(FrameData.stopFrame())

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

