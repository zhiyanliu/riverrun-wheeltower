import os

from video_reader import video_reader


class VideoPacketHoBotX2SDKReader(video_reader.VideoPacketReader):
    def __init__(self, shm_filename="foo_30M"):  # filename under /dev/shm/
        self._filename = shm_filename
        self._sdk = None
        self._init_sdk()
        print("hobotx2 SDK based video packet reader created, pid = %d, filename = %s" % (os.getpid(), self._filename))

    def _init_sdk(self):
        try:
            print("initializing hobotx2 SDK interface")
            from video_reader import hobotx2  # hobotx2.so
            self._sdk = hobotx2
            ret = self._sdk.init_video(self._filename)
            if 0 != ret:
                raise Exception("retcode = %d" % ret)
            print("hobotx2 SDK interface initialized successfully")
        except Exception as e:
            print("failed to init hobotx2 SDK interface: %s" % str(e))
            self._sdk = None
            raise Exception("init hobotx2 SDK interface failed")

    def _destroy_sdk(self):
        if self._sdk is None:
            return
        try:
            print("destroy hobotx2 SDK interface")
            ret = self._sdk.deinit_video()
            if 0 != ret:
                raise Exception("retcode = %d" % ret)
            self._sdk = None
            print("hobotx2 SDK interface destroyed successfully")
        except Exception as e:
            print("failed to destroy hobotx2 SDK interface: %s" % str(e))
            raise Exception("destroy hobotx2 SDK interface failed")

    def read(self):
        try:
            while True:
                ret, rtp_pkt = self._sdk.read_video_stream()
                if 0 == ret:
                    if len(rtp_pkt) == 0:
                        # FIXME(production): SDK's block-IO interface shouldn't return an empty RTP packet
                        print("empty video packet received, ignored")
                        continue
                    break
                elif -32 == ret:  # the connection between CP and AP is broken
                    try:
                        print("hobotx2 SDK connection is broken, re-init the SDK to rebuild")
                        self._destroy_sdk()
                        self._init_sdk()
                    except Exception as e:
                        print("failed to rebuild the hobotx2 SDK connection")
                        raise e
                else:
                    raise Exception("retcode = %d" % ret)
        except Exception as e:
            print("failed to read video packet from the SDK interface (read_video_stream) %s: %s" %
                  (self._filename, str(e)))
            return False, None
        return True, rtp_pkt

    def release(self):
        self._destroy_sdk()
        print("hobotx2 SDK based video packet reader released, pid = %d, filename = %s" % (os.getpid(), self._filename))
