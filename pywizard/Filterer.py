from scipy import signal
from pywizard.Buffer import Buffer


class Filterer(object):
    def __init__(self, buf, lowPassCutoffInHZ, highPassCutoffInHZ, gain,
                 order=5):
        self.gain = gain
        self.buf = buf
        nyq = 0.5 * buf.sampleRate
        low = lowPassCutoffInHZ / nyq
        # Avoid highpass frequency above nyqist-freq, this leads to
        # weird behavior
        high = min((highPassCutoffInHZ / nyq, 1))
        self.b, self.a = signal.butter(order, [low, high], btype='band')

    def process(self):
        return Buffer.copy(self.buf,
                           applyFilter=lambda x: signal.filtfilt(self.b, self.a, x))
