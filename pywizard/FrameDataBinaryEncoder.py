from pywizard.tools import BitHelpers
from pywizard.CodingTable import CodingTable
from pywizard.HexConverter import HexConverter
from collections import namedtuple
import logging

class BitPacker(object):

    @classmethod
    def pack(cls, frameData):
        parametersList = [ x.parameters() for x in frameData ]
        binary = FrameDataBinaryEncoder.process(parametersList)
        hexform = HexConverter.process(binary)
        return hexform

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
