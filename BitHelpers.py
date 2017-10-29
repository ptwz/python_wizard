class BitHelpers(object):
    @classmethod
    def valueToBinary(cls, value, bits):
        return format(value, "0{}b".format(bits))

    @classmethod
    def valueForBinary(cls, binary):
        return int(binary, 2)

