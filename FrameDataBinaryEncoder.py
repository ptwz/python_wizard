class FrameDataBinaryEncoder(object):
    @classmethod
    def process(cls, parametersList):
        bits = CodingTable.bits
        binary = ""
        for parameters in parametersList:
            params = CodingTable.parameters()
            for (param_name, idx) in zip(params, range(len(params))):
                if param_name not in parameters:
                    break
                value = parameters[param_name]
                binaryValue = BitHelpers.valueToBinary(value, bits[idx])
                logging.debug("param_name={} idx={} value={} binaryValue={}".format(param_name, idx, value, binaryValue))
                binary += binaryValue
        return cls.nibblesFrom(binary)

    @classmethod
    def nibblesFrom(cls, binary):
        nibbles = []
        while len(binary) >= 4:
            nibble = binary[0:4]
            binary = binary[4:]
            nibbles.append(nibble)
        return nibbles

formatSpecifier = namedtuple("formatSpecifier", ["header", "formatString", "separator", "trailer"])

