class FrameReader:
    def read(self):
        """Returns:
            1. if any metadata frame is read.
            2. the timestamp of the metadata frame.
            3. the metadata frame buffer.
            """
        return False, -1, None

    def release(self):
        """Release the resource of this reader instance."""
        pass
