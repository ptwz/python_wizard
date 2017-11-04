from collections import namedtuple

class BitPacker(object):

    @classmethod
    def pack(cls, frameData):
        parametersList = [ x.parameters() for x in frameData ]
        binary = FrameDataBinaryEncoder.process(parametersList)
        hexform = HexConverter.process(binary)
        return hexform

class BitHelpers(object):
    @classmethod
    def valueToBinary(cls, value, bits):
        return format(value, "0{}b".format(bits))

    @classmethod
    def valueForBinary(cls, binary):
        return int(binary, 2)

def ClosestValueFinder(actual, table):
    if actual < table[0]:
        return 0

    return table.index(min(table, key=lambda x:abs(x-actual)))


formatSpecifier = namedtuple("formatSpecifier", ["header", "formatString", "separator", "trailer"])
