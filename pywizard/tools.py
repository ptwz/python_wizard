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
    '''
    Find the tabulated value closest to the given one.

    >>> floats = [1.0, 2.0]

    >>> ClosestValueFinder(1.25, floats)
    0
    >>> ClosestValueFinder(1.75, floats)
    1
    >>> floats = [5.0, 6.0]

    >>> ClosestValueFinder(-1.0, floats)
    0
    >>> ClosestValueFinder(8.0, floats)
    1
    '''
    if actual < table[0]:
        return 0

    return table.index(min(table, key=lambda x:abs(x-actual)))


formatSpecifier = namedtuple("formatSpecifier", ["header", "formatString", "separator", "trailer"])
