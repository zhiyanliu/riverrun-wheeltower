import multiprocessing.connection

import base_server


class SyncServer(base_server.Server):
    def __init__(self, name, frame_handle_pipe_r, video_take_pipe_r, sync_pkt_emit_pipe_w,
                 sync_policy, sync_pkt_combiner):

        super(SyncServer, self).__init__(name)
        if frame_handle_pipe_r is None:
            raise Exception("frame handle read pipe connection is None")
        if video_take_pipe_r is None:
            raise Exception("video take read pipe connection is None")
        if sync_pkt_emit_pipe_w is None:
            raise Exception("synchronized packet emit write pipe connection is None")
        if sync_policy is None:
            raise Exception("packet synchronize policy is None")
        if sync_pkt_combiner is None:
            raise Exception("packet synchronize combiner is None")

        self._frame_handle_pipe_r = frame_handle_pipe_r
        self._video_take_pipe_r = video_take_pipe_r
        self._sync_pkt_emit_pipe_w = sync_pkt_emit_pipe_w
        self._sync_policy = sync_policy
        self._sync_pkt_combiner = sync_pkt_combiner

        # count latest timestamp and linear space index
        self._latest_meta_frame_timestamp = 0
        self._latest_meta_frame_index = None
        self._latest_rtp_pkt_timestamp = 0
        self._latest_rtp_pkt_index = None

        # calculate and log video frame match rate
        self._latest_handled_timestamp_count = 0
        self._latest_handled_timestamp_matched_count = 0

        # calculate metadata frame match rate
        self._in_meta_frame_count = 0
        self._match_meta_frame_count = 0

        # log output drop
        self._drop_count = 0

    def _log_routine(self):
        # log latest handle timestamp and linear space index
        print("latest handle metadata frame timestamp = %d (linear space index = %d)" %
              (self._latest_meta_frame_timestamp,
               -1 if self._latest_meta_frame_index is None else self._latest_meta_frame_index))
        print("latest handle video packet timestamp = %d (linear space index = %d)" %
              (self._latest_rtp_pkt_timestamp,
               -1 if self._latest_rtp_pkt_index is None else self._latest_rtp_pkt_index))

        # calculate and log video frame match rate
        rate = 0
        if self._latest_handled_timestamp_count > 0:
            rate = self._latest_handled_timestamp_matched_count / self._latest_handled_timestamp_count
        print("video frame match rate in last 5 seconds: %.2f%% (%d/%d)" %
              (rate * 100, self._latest_handled_timestamp_matched_count, self._latest_handled_timestamp_count))
        self._latest_handled_timestamp_count = 0
        self._latest_handled_timestamp_matched_count = 0

        # calculate and log metadata frame match rate
        rate = 0
        if self._in_meta_frame_count > 0:
            rate = self._match_meta_frame_count / self._in_meta_frame_count
        print("metadata frame match rate in last 5 seconds: %.2f%% (%d/%d)" %
              (rate * 100, self._match_meta_frame_count, self._in_meta_frame_count))
        self._in_meta_frame_count = 0
        self._match_meta_frame_count = 0

        # log the range of video packet timestamp of the synchronization queue
        print("the range of video packet timestamp of the synchronization queue: [%d, %d] "
              "(linear space index: [%d, %d])" %
              (self._sync_policy.video_pkt_timestamp_range + self._sync_policy.video_pkt_index_range))

        # log output drop
        if self._drop_count > 0:
            print("WARN: synchronized packet emitter is slow, the number of dropped synchronized packet in "
                  "last 5 seconds: %d" % self._drop_count)
            self._drop_count = 0  # reset

        self._start_log_routine()

    def _align(self):
        meta_frame = None
        rtp_pkt = None

        while not self._stop_flag.is_set():
            if rtp_pkt is None:
                try:
                    rtp_pkt = self._video_take_pipe_r.recv()
                except EOFError:  # read pipe connection closed
                    print("BUG: read pipe connection should not be closed before server finish")
                    rtp_pkt = None
                except Exception as e:
                    print("WARN: failed to receive video packet from the pipe: %s" % str(e))
                    rtp_pkt = None

            if meta_frame is None:
                try:
                    meta_frame = self._frame_handle_pipe_r.recv()
                except EOFError:  # read pipe connection closed
                    print("BUG: read pipe connection should not be closed before server finish")
                    meta_frame = None
                except Exception as e:
                    print("WARN: failed to receive metadata frame from the pipe: %s" % str(e))
                    meta_frame = None

            if rtp_pkt is None or meta_frame is None:
                continue

            if rtp_pkt.timestamp > meta_frame.timestamp:
                if rtp_pkt.timestamp - meta_frame.timestamp > 32768:  # 65536 / 2
                    rtp_pkt = None   # video frame is slow than metadata frame, in last rotation
                else:
                    meta_frame = None  # metadata frame is slow than video frame, in same rotation
            elif rtp_pkt.timestamp < meta_frame.timestamp:
                if meta_frame.timestamp - rtp_pkt.timestamp > 32768:  # 65536 / 2
                    meta_frame = None  # metadata frame is slow than video frame, in last rotation
                else:
                    rtp_pkt = None   # video frame is slow than metadata frame, in same rotation
            else:  # rtp_pkt.timestamp == meta_frame.timestamp
                # metadata frame and video frame are under same timestamp
                return rtp_pkt, meta_frame

        return None, None

    def _update_latest_rtp_pkt_counter(self, rtp_pkt):
        mis_order = False

        # update index before update latest timestamp
        if self._latest_rtp_pkt_index is None:
            self._latest_rtp_pkt_index = 0
        elif rtp_pkt.timestamp > self._latest_rtp_pkt_timestamp:
            if rtp_pkt.timestamp - self._latest_rtp_pkt_timestamp > 32768:  # 65536 / 2
                # 4. cross rotation, mis-order
                self._latest_rtp_pkt_index -= \
                    (65536 - rtp_pkt.timestamp) + (self._latest_rtp_pkt_timestamp - 0)
                mis_order = True
            else:
                # 1. no rotated, increase
                delta = rtp_pkt.timestamp - self._latest_rtp_pkt_timestamp
                if delta > 1:
                    print("WARN: video packet fast forward, timestamp delta = %d" % delta)
                self._latest_rtp_pkt_index += delta
        elif rtp_pkt.timestamp < self._latest_rtp_pkt_timestamp:
            if self._latest_rtp_pkt_timestamp - rtp_pkt.timestamp > 32768:  # 65536 / 2
                # 2. rotated, increase
                delta = (65536 - self._latest_rtp_pkt_timestamp) + (rtp_pkt.timestamp - 0)
                if delta > 1:
                    print("WARN: video packet fast forward, timestamp delta = %d" % delta)
                self._latest_rtp_pkt_index += delta

            else:
                # 3. non-cross rotation, mis-order
                self._latest_rtp_pkt_index -= \
                    self._latest_rtp_pkt_timestamp - rtp_pkt.timestamp
                mis_order = True

        if mis_order:
            print("WARN: mis-order RTP packet timestamp received, new arrived = %d, last received = %d)" %
                  (rtp_pkt.timestamp, self._latest_rtp_pkt_timestamp))

        # update latest timestamp at last
        self._latest_rtp_pkt_timestamp = rtp_pkt.timestamp

    def _update_latest_meta_frame_counter(self, meta_frame):
        mis_order = False

        # update index before update latest timestamp
        if self._latest_meta_frame_index is None:
            self._latest_meta_frame_index = 0
        elif meta_frame.timestamp > self._latest_meta_frame_timestamp:
            if meta_frame.timestamp - self._latest_meta_frame_timestamp > 32768:  # 65536 / 2
                # 4. cross rotation, mis-order
                self._latest_meta_frame_index -= \
                    (65536 - meta_frame.timestamp) + (self._latest_meta_frame_timestamp - 0)
                mis_order = True
            else:
                # 1. no rotated, increase
                self._latest_meta_frame_index += meta_frame.timestamp - self._latest_meta_frame_timestamp
        elif meta_frame.timestamp < self._latest_meta_frame_timestamp:
            if self._latest_meta_frame_timestamp - meta_frame.timestamp > 32768:  # 65536 / 2
                # 2. rotated, increase
                self._latest_meta_frame_index += \
                    (65536 - self._latest_meta_frame_timestamp) + (meta_frame.timestamp - 0)
            else:
                # 3. non-cross rotation, mis-order
                self._latest_meta_frame_index -= \
                    self._latest_meta_frame_timestamp - meta_frame.timestamp
                mis_order = True

        if mis_order:
            print("WARN: mis-order metadata frame timestamp received, new arrived = %d, last received = %d)" %
                  (meta_frame.timestamp, self._latest_meta_frame_timestamp))

        # update latest timestamp at last
        self._latest_meta_frame_timestamp = meta_frame.timestamp

    def _output(self, sync_list):
        for (rtp_pkt, meta_frame) in sync_list:
            try:
                ret, synced_pkt = self._sync_pkt_combiner.combine(rtp_pkt, meta_frame)
            except Exception as e:
                print("failed to combine RTP packet and metadata frame to synchronized packet: %s" % str(e))
                continue

            if not ret:
                continue

            try:
                self._sync_pkt_emit_pipe_w.send(synced_pkt)
            except ValueError as e:
                print("WARN: failed to send synchronized packet to the pipe: %s" % str(e))
                continue

    def serve(self):
        print("aligning video packet and metadata frame...")
        rtp_pkt, meta_frame = self._align()
        if rtp_pkt is None and meta_frame is None:
            return  # server stopped

        print("video packet and metadata aligned at timestamp: %d" % rtp_pkt.timestamp)

        self._update_latest_rtp_pkt_counter(rtp_pkt)
        self._update_latest_meta_frame_counter(meta_frame)

        meta_frame = None

        while not self._stop_flag.is_set():
            handle_ret = False
            care_list = []

            # income
            if rtp_pkt is None:
                care_list.append(self._video_take_pipe_r)
            if meta_frame is None:
                # the last metadata frame might be held if it arrived too early
                care_list.append(self._frame_handle_pipe_r)
            ready_pipes = multiprocessing.connection.wait(care_list, timeout=1)

            if len(care_list) != 0 and len(ready_pipes) == 0:
                # timeout, just for server stop checking
                continue

            if self._video_take_pipe_r in ready_pipes:
                try:
                    rtp_pkt = self._video_take_pipe_r.recv()

                    self._update_latest_rtp_pkt_counter(rtp_pkt)
                except EOFError:  # read pipe connection closed
                    print("BUG: read pipe connection should not be closed before server finish")
                    rtp_pkt = None
                except Exception as e:
                    print("WARN: failed to receive video packet from the pipe: %s" % str(e))
                    rtp_pkt = None

            if self._frame_handle_pipe_r in ready_pipes:
                try:
                    meta_frame = self._frame_handle_pipe_r.recv()

                    self._update_latest_meta_frame_counter(meta_frame)
                    self._in_meta_frame_count += 1
                except EOFError:  # read pipe connection closed
                    print("BUG: read pipe connection should not be closed before server finish")
                    meta_frame = None
                except Exception as e:
                    print("WARN: failed to receive metadata frame from the pipe: %s" % str(e))
                    meta_frame = None

            # early arrived metadata frame need to wait to reach high watermark of the sync queue
            # the watermark will be raised by continuative incoming video packet
            _low_watermark, high_watermark = self._sync_policy.video_pkt_index_range

            # sync
            matched = False
            if rtp_pkt is not None and meta_frame is not None:
                if ((high_watermark != 0 and self._latest_meta_frame_index <= high_watermark) or
                        self._latest_meta_frame_index <= self._latest_rtp_pkt_index):
                    handle_ret, sync_list, matched, timestamp_n, timestamp_matched_n =\
                        self._sync_policy.handle_video_pkt_meta_frame(rtp_pkt, self._latest_rtp_pkt_index,
                                                                      meta_frame, self._latest_meta_frame_index)
                    rtp_pkt = None
                    meta_frame = None
                else:
                    handle_ret, sync_list, timestamp_n, timestamp_matched_n =\
                        self._sync_policy.handle_video_pkt(rtp_pkt, self._latest_rtp_pkt_index)
                    rtp_pkt = None
            elif meta_frame is not None:  # video packet is not received
                if high_watermark != 0 and self._latest_meta_frame_index <= high_watermark:
                    handle_ret, sync_list, matched, timestamp_n, timestamp_matched_n =\
                        self._sync_policy.handle_meta_frame(meta_frame, self._latest_meta_frame_index)
                    meta_frame = None
            elif rtp_pkt is not None:     # metadata frame is not received
                handle_ret, sync_list, timestamp_n, timestamp_matched_n =\
                    self._sync_policy.handle_video_pkt(rtp_pkt, self._latest_rtp_pkt_index)
                rtp_pkt = None

            if matched:
                self._match_meta_frame_count += 1

            # outcome
            if handle_ret:
                self._latest_handled_timestamp_count += timestamp_n
                self._latest_handled_timestamp_matched_count += timestamp_matched_n
                self._output(sync_list)
