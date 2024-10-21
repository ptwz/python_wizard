from pywizard.tools import BitHelpers
from pywizard.HexConverter import HexConverter
import logging


class BitPacker(object):
    @classmethod
    def raw_stream(cls, processor):
        frameData = processor.frames
        parametersList = [x.parameters() for x in frameData]
        raw_data = FrameDataBinaryEncoder.process(processor.codingTable,
                                                  parametersList)
        return HexConverter.preprocess(raw_data)

    @classmethod
    def pack(cls, processor):
        frameData = processor.frames
        parametersList = [x.parameters() for x in frameData]
        raw_data = FrameDataBinaryEncoder.process(processor.codingTable,
                                                  parametersList)
        return HexConverter.process(raw_data)


class FrameDataBinaryEncoder(object):
    @classmethod
    def process(cls, codingTable, parametersList):
        bits = codingTable.bits
        binary = ""
        for parameters in parametersList:
            params = codingTable.parameters()
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
