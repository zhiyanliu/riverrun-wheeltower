import os

from frame_reader import frame_reader


class FrameHoBotX2SDKReader(frame_reader.FrameReader):
    def __init__(self):
        self._sdk = None
        self._init_sdk()
        print("hobotx2 SDK based frame reader created, pid = %d" % os.getpid())

    def _init_sdk(self):
        try:
            print("initializing hobotx2 SDK interface")
            from frame_reader import hobotx2  # hobotx2.so
            self._sdk = hobotx2
            ret = self._sdk.init_smart()
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
            ret = self._sdk.deinit_smart()
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
                ret, meta_frame_timestamp, meta_frame_buff = self._sdk.read_smart_frame_with_id()
                if 0 == ret:
                    if meta_frame_timestamp < 0 or meta_frame_timestamp > 65535:
                        print("invalid timestamp of metadata frame received: %d, ignored" % meta_frame_timestamp)
                        continue
                    if len(meta_frame_buff) == 0:
                        print("empty metadata frame received, ignored")
                        continue
                    break
                elif -7 == ret or -10 == ret:  # the connection between CP and AP is broken
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
            print("failed to read metadata frame from the SDK interface (read_smart_frame_with_id): %s" % str(e))
            return False, -1, None

        return True, meta_frame_timestamp, meta_frame_buff

    def release(self):
        self._destroy_sdk()
        print("hobotx2 SDK based frame reader released, pid = %d" % os.getpid())


class FrameHoBotX2NoneReader(frame_reader.FrameReader):
    def __init__(self):
        from frame_reader import x2_pb2
        self._frame_module = x2_pb2
        print("hobotx2 NONE frame reader created, pid = %d" % os.getpid())

    def read(self):
        meta_frame = self._frame_module.FrameMessage()
        # fake data to prevent empty serialized string
        meta_frame.capture_msg_.targets_.append(self._frame_module.CaptureTarget())
        meta_frame.capture_msg_.targets_[0].captures_.append(self._frame_module.Capture())
        meta_frame.capture_msg_.targets_[0].captures_[0].timestamp_ = 0
        return True, meta_frame.smart_msg_.timestamp_, meta_frame.SerializeToString()

    def release(self):
        print("hobotx2 NONE frame reader released, pid = %d" % os.getpid())
