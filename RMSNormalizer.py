class RMSNormalizer(object):
    @classmethod
    def normalize(cls, frameData, Voiced):
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

