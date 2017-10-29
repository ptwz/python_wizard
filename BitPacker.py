from FrameDataBinaryEncoder import FrameDataBinaryEncoder
from HexConverter import HexConverter

class BitPacker(object):

    @classmethod
    def pack(cls, frameData):
        parametersList = [ x.parameters() for x in frameData ]
        binary = FrameDataBinaryEncoder.process(parametersList)
        hexform = HexConverter.process(binary)
        return hexform


