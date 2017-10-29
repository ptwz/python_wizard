class HexConverter(object):
    formats = {
        "arduino" : formatSpecifier("const unsigned char FILENAME[] PROGMEM = {",
                     "0x{:02X}",
                     ",",
                     "};"),
        "C"       : formatSpecifier("const unsigned char FILENAME[] = {",
                     "0x{:02X}",
                     ",",
                     "};"),
        "hex"     : formatSpecifier("",
                     "{:02x}",
                     " ",
                     "")
                    }

    @classmethod
    def process(cls, nibbles):
        '''
        Creates nibble swapped, reversed data bytestream as hex value list.
        Used to be NibbleBitReverser, NibbleSwitcher and HexConverter
        '''
        formatter = cls.formats[settings.outputFormat]
        result = []
        for u,l in zip(nibbles[0::2], nibbles[1::2]):
            raw = (u+l)[::-1]
            data = int(raw, base=2)
            result.append(formatter.formatString.format(data))
        logging.debug("Will format output using {} ({})".format(settings.outputFormat, formatter ))
        return formatter.header + formatter.separator.join(result) + formatter.trailer


