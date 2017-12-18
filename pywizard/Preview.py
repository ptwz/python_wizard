from Buffer import Buffer
from Reflector import Reflector
from Segmenter import Segmenter
from PitchEstimator import PitchEstimator
from userSettings import settings
from HammingWindow import HammingWindow
from FrameData import FrameData
from PreEmphasizer import PreEmphasizer
import scipy as sp
import logging

class Preview(object):
    chirp = (0x00,0x2a,0xd4,0x32,0xb2,0x12,0x25,0x14,0x02,0xe1,0xc5,0x02,0x5f,0x5a,0x05,0x0f,0x26,0xfc,0xa5,0xa5,0xd6,0xdd,0xdc,0xfc,0x25,0x2b,0x22,0x21,0x0f,0xff,0xf8,0xee,0xed,0xef,0xf7,0xf6,0xfa,0x00,0x03,0x02,0x01)

    def __init__(self, frames):
        self.frames = frames[:]
        self.frames.reverse()
        self.state = { "kParameterGain":0,
                       "kParameterRepeat":0,
                       "kParameterPitch":0}

    def render(self):
        decoding = True
        cur_frame = None
        sound = []
        ks = [0] * 10
        sample_count = 0
        rng = 0 # 1 + x + x^3 + x^4 + x^13
        lattice_fwd = [0.] * 11
        lattice_rev = [0.] * 11

        while decoding:
            cur_frame = self.frames.pop()
            pitch_count = 0
            interp_count = 0
            if len(self.frames) == 0:
                decoding = False
                break
            if cur_frame.stopFrame:
                decoding = False
                break

            frame_state = cur_frame.translatedParameters()

            if cur_frame.reflector.isVoiced:
                in_data = [ x * frame_state['kParameterGain'] for x in self.chirp[::-1] ]
            else:
                in_data = ( scipy.rand(100) * 128 * frame_state['kParameterGain']).tolist() 
                #for x in range(100):
                #    rng = (rng >> 1) ^ ( 0xB800 if (rng &1) else 0)
                #    in_data.append(rng)


            if not frame_state['kParameterRepeat']:
                # Repeat frames keep last reflector bits
                ks = [0] * 10

                copylen = 4
                if cur_frame.reflector.isVoiced():
                    copylen = 10

            for i in range(copylen):
                k = "kParameterK{}".format(i+1)
                ks[i] = frame_state[k]
    
            for value in in_data:
                lattice_fwd[10] = value / 65535.

                for i in range(9, -1, -1):
                    lattice_fwd[i] = lattice_fwd[i+1] - (ks[i]*lattice_rev[i]) / 2.
                    # 1/0: / 32768 !!

#            if lattice_fwd[0] > 1:
#                lattice_fwd[0] = 1
#            elif lattice_fwd[0] < -1:
#                lattice_fwd[0] = -1
#        
                for i in range(9, 0, -1):
                    lattice_rev[i] = lattice_rev[i-1] - (ks[i]*lattice_fwd[i]) / 2.
                    # 1/0: / 32768 !!
                lattice_rev[0] = lattice_fwd[0]

                yield lattice_fwd[0] / 4.

    def process(self):
        return(self.frameData)

