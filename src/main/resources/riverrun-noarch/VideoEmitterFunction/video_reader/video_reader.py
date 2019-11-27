class VideoPacketReader:
    def read(self):
        """Returns:
            1. if any video packet is read.
            2. the video RTP packet buffer.
            """
        return False, None

    def release(self):
        """Release the resource of this reader instance."""
        pass
