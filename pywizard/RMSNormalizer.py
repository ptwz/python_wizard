from userSettings import settings

class RMSNormalizer(object):
    @classmethod
    def normalize(cls, frameData, Voiced):
        """
        Normalize Voice levels to maximum RMS.

        >>> from FrameData import FrameData

        >>> from Reflector import Reflector

        >>> from CodingTable import CodingTable

        >>> r = Reflector()
        
        >>> rms = CodingTable.rms[2]

        >>> RMSNormalizer.maxRMSIndex
        3
        
        >>> framedata = FrameData(reflector=r, pitch=0, repeat=False)

        >>> RMSNormalizer.normalize([framedata], Voiced=True)

        >>> reflector.rms == CodingTable.rms[3]
        True
        """
        maximum = max( [ x.rms for x in frameData if x.isVoiced() == Voiced ] )

        if maximum <= 0:
            return

        if Voiced:
            ref = cls.maxRMSIndex()
        else:
            ref = cls.maxUnvoicedRMSIndex()
        scale = CodingTable.rms[cls.ref] / maximum

        for frame in FrameData:
            if not frame.reflector.isVoiced() == Voiced:
                frame.reflector.rms *= scale

    @classmethod
    def applyUnvoicedMultiplier(cls, frameData):
        mutiplier = cls.unvoicedRMSMultiplier()
        for frame in frameData:
            if frame.reflector.isUnvoiced():
                frame.reflector.rms *= mutiplier

    @classmethod
    def maxRMSIndex(cls):
        return settings.rmsLimit

    @classmethod
    def maxUnvoicedRMSIndex(cls):
        return settings.unvoicedRMSLimit

    @classmethod
    def unvoicedMultiplier(cls):
        return settings.unvoicedRMSMultiplier

