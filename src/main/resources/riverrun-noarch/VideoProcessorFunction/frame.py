class MetaFrame:
    def __init__(self, timestamp, meta_frame_buff):
        if timestamp is None:
            raise Exception("metadata frame timestamp is None")
        if meta_frame_buff is None:
            raise Exception("metadata frame buffer is None")
        self.timestamp = timestamp
        self.buff = meta_frame_buff

    def __reduce__(self):
        return self.__class__, (self.timestamp, self.buff)
