import logging
import scipy as sp

class HammingWindow(object):
    _windows = {}

    @classmethod
    def processBuffer(cls, buf):
        l = len(buf)
        if l not in cls._windows:
            logging.debug("HammingWindow: Generate window for len {}".format(l))
            cls._windows[l] = [  (0.54 - 0.46 * sp.cos(2 * sp.pi * i / (l - 1))) for i in range(l)]

        buf.samples *= cls._windows[l]

