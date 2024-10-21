from pywizard.userSettings import settings
from pywizard.Buffer import Buffer
import numpy as np


class Segmenter(object):
    def __init__(self, buf, windowWidth):
        milliseconds = settings.frameRate
        self.size = int(np.ceil(buf.sampleRate / 1e3 * milliseconds))
        self.buf = buf
        self.windowWidth = windowWidth

    def eachSegment(self):
        length = self.numberOfSegments()
        for i in range(0, length):
            samples = self.samplesForSegment(i)
            buf = Buffer(samples=samples, size=self.sizeForWindow,
                         sampleRate=self.buf.sampleRate)
            yield (buf, i)

    def samplesForSegment(self, index):
        length = self.sizeForWindow()

        samples = self.buf.samples[index * self.size: index * self.size + length]
        samples = np.append(samples, [0]*(length-len(samples)))

        return samples

    def sizeForWindow(self):
        return int(self.size * self.windowWidth)

    def numberOfSegments(self):
        return int(np.ceil(float(self.buf.size) / float(self.size)))
