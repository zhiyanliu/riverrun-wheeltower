import collections
import os
import sys
import traceback

import constants


class _RTPPackageItem:
    def __init__(self, rtp_pkg, index):
        self._rtp_pkg = rtp_pkg
        self._index = index

    @property
    def core(self):
        return self._rtp_pkg

    @property
    def timestamp(self):
        return self._rtp_pkg.timestamp

    @property
    def index(self):
        return self._index


class _MetadataFrameItem:
    def __init__(self, meta_frame, index):
        self._meta_frame = meta_frame
        self._index = index

    @property
    def core(self):
        return self._meta_frame

    @property
    def timestamp(self):
        return self._meta_frame.timestamp

    @property
    def index(self):
        return self._index


class _TimestampGroupQueueBase(collections.deque):
    def __init__(self, rtp_pkt_item, meta_frame_item=None, meta_frame_item_overwritable=False):
        super(_TimestampGroupQueueBase, self).__init__()
        self._timestamp = rtp_pkt_item.timestamp
        self._index = rtp_pkt_item.index
        self.append(rtp_pkt_item)
        self._meta_frame_item = meta_frame_item
        self._meta_frame_item_overwritable = meta_frame_item_overwritable

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def index1(self):
        return self._index

    @property
    def meta_frame_item(self):
        return self._meta_frame_item

    @meta_frame_item.setter
    def meta_frame_item(self, meta_frame_item):
        if self.meta_frame_item is not None:
            print("WARN: a duplicated metadata frame for the same RTP packet(s) is detected, "
                  "last one timestamp = %d (linear space index = %d, addr = %s) "
                  "new one timestamp = %d (linear space index = %d, addr = %s)" %
                  (self._meta_frame_item.timestamp, self._meta_frame_item.index, hex(id(self._meta_frame_item.core)),
                   meta_frame_item.timestamp, meta_frame_item.index, hex(id(meta_frame_item.core))))
            traceback.print_stack(file=sys.stdout)
            if not self._meta_frame_item_overwritable:
                return
        self._meta_frame_item = meta_frame_item

    @property
    def is_meta_frame_matched(self):
        return self.meta_frame_item is not None

    def list_rtp_meta_frame(self):
        pass


class _TimestampGroupQueueOneMetaFramePerVideoFrame(_TimestampGroupQueueBase):
    def list_rtp_meta_frame(self):
        ret = list(map(lambda rtp_pkt_item: (rtp_pkt_item.core, None), self))
        if len(ret) > 0 and self.meta_frame_item is not None:
            rtp_pkt, _ = ret[0]
            ret[0] = (rtp_pkt, self.meta_frame_item.core)
        return ret


class _TimestampGroupQueueOneMetaFramePerRTPPacket(_TimestampGroupQueueBase):
    def list_rtp_meta_frame(self):
        return list(map(lambda rtp_pkt_item:
                        (rtp_pkt_item.core, self.meta_frame_item.core if self.meta_frame_item is not None else None),
                        self))


class SyncPolicy:
    def __init__(self):
        self._queue = None  # will overwrite by subclass
        if constants.get_sync_pkt_policy_whether_send_meta_frame_once():
            print("sending one metadata frame for each video frame if matched")
            self._timestamp_group_queue_class = _TimestampGroupQueueOneMetaFramePerVideoFrame
        else:
            print("sending one metadata frame for each RTP packet if matched")
            self._timestamp_group_queue_class = _TimestampGroupQueueOneMetaFramePerRTPPacket

    def _index_timestamp_group(self, index):
        # iter is faster than index operate a lot for deque implement in cpython, so count by myself
        # https://stackoverflow.com/questions/47338547/what-is-the-time-complexity-of-iterating-through-a-deque-in-python
        idx = 0
        for timestamp_group in self._queue:
            if timestamp_group.index1 == index:
                return idx, timestamp_group
            idx += 1
        raise ValueError("RTP packet group with index (linear timestamp space) %d is not in the queue" % index)

    def handle_video_pkt_meta_frame(self, rtp_pkt, rtp_pkt_index, meta_frame, meta_frame_index):
        """Returns:
            1. if any video packet is handled.
            2. the handle result, a list of tuple (video packet, metadata frame) is returned when #1 is True.
                The metadata frame could be None if the video packet is not matched with a metadata frame.
            3. if the metadata frame is matched.
            4. the amount of timestamp groups (video frames) are included in the #2 list.
            5. the amount of timestamp groups (video frames) are included in the #2 list which is matched
                with a metadata frame.
            """
        return False, None, False, 0, 0

    def handle_video_pkt(self, rtp_pkt, rtp_pkt_index):
        """Returns:
            1. if any video packet is handled.
            2. the handle result, a list of tuple (video packet, metadata frame) is returned when #1 is True.
                The metadata frame could be None if the video packet is not matched with a metadata frame.
            3. the amount of timestamp groups (video frames) are included in the #2 list.
            4. the amount of timestamp groups (video frames) are included in the #2 list which is matched
                with a metadata frame.
            """
        return False, None, 0, 0

    def handle_meta_frame(self, meta_frame, meta_frame_index):
        """Returns:
            1. if any video packet is handled.
            2. the handle result, a list of tuple (video packet, metadata frame) is returned when #1 is True.
                The metadata frame could be None if the video packet is not matched with a metadata frame.
            3. if the metadata frame is matched.
            4. the amount of timestamp groups (video frames) are included in the #2 list.
            5. the amount of timestamp groups (video frames) are included in the #2 list which is matched
                with a metadata frame.
            """
        return False, None, False, 0, 0

    @property
    def video_pkt_index_range(self):
        if self._queue is None:
            return -1, -1
        if len(self._queue) == 0:
            return 0, 0
        return self._queue[0].index1, self._queue[-1].index1

    @property
    def video_pkt_timestamp_range(self):
        if self._queue is None:
            return -1, -1
        if len(self._queue) == 0:
            return 0, 0
        return self._queue[0].timestamp, self._queue[-1].timestamp


class OneShotSyncPolicy(SyncPolicy):
    def __init__(self, queue_size):
        super(OneShotSyncPolicy, self).__init__()
        if queue_size < 1:
            raise Exception("invalid queue size, must greater than zero")
        self._queue_size = queue_size
        self._queue = collections.deque([])  # control queue overflow manually
        print("one-shot synchronize policy created, pid = %d, queue size = %d" % (os.getpid(), self._queue_size))

    def _append_video_pkt_item(self, rtp_pkt_item):
        try:
            _, timestamp_group = self._index_timestamp_group(rtp_pkt_item.index)
            timestamp_group.append(rtp_pkt_item)
            return None
        except ValueError:
            # no any RTP packet groups with the index (linear timestamp space) in the queue yet
            timestamp_group = self._timestamp_group_queue_class(rtp_pkt_item)
            overflow_timestamp_group = None
            if len(self._queue) == self._queue_size:
                overflow_timestamp_group = self._queue.popleft()
            self._queue.append(timestamp_group)
            return overflow_timestamp_group

    def handle_video_pkt_meta_frame(self, rtp_pkt, rtp_pkt_index, meta_frame, meta_frame_index):
        self._queue_size += 1  # size up one slot temporarily
        try:
            handled, _, _, _ = self.handle_video_pkt(rtp_pkt, rtp_pkt_index)
            if handled:
                raise Exception("BUG: the queue shouldn't overflow after sized up one slot temporarily")

            handled, ret, matched, timestamp_group_n, timestamp_group_matched_n =\
                self.handle_meta_frame(meta_frame, meta_frame_index)

            if not handled:
                # flush first one slot before size down the queue if overflowed
                if len(self._queue) == self._queue_size:
                    overflow_timestamp_group = self._queue.popleft()
                    ret = overflow_timestamp_group.list_rtp_meta_frame()
                    handled = True
                    timestamp_group_n = 1
                    timestamp_group_matched_n = 1 if overflow_timestamp_group.is_meta_frame_matched else 0

            if handled:
                return True, ret, matched, timestamp_group_n, timestamp_group_matched_n
            else:
                return False, None, matched, timestamp_group_n, timestamp_group_matched_n
        finally:
            # size down one slot
            self._queue_size -= 1

    def handle_video_pkt(self, rtp_pkt, rtp_pkt_index):
        rtp_pkt_item = _RTPPackageItem(rtp_pkt, rtp_pkt_index)

        overflow_timestamp_group = self._append_video_pkt_item(rtp_pkt_item)
        if overflow_timestamp_group is None:
            return False, None, 0, 0
        return (True, overflow_timestamp_group.list_rtp_meta_frame(), 1,
                1 if overflow_timestamp_group.is_meta_frame_matched else 0)

    def handle_meta_frame(self, meta_frame, meta_frame_index):
        matched = False
        ret = []
        remove_indices = []
        timestamp_group_matched_n = 0
        # again, iter is faster than index operate a lot for deque implement in cpython, so count by myself
        idx = 0

        meta_frame_item = _MetadataFrameItem(meta_frame, meta_frame_index)

        for timestamp_group in self._queue:
            if not timestamp_group.index1 > meta_frame_item.index:
                if timestamp_group.index1 == meta_frame_item.index:
                    timestamp_group.meta_frame_item = meta_frame_item
                    matched = True
                # delete from end to begin to prevent index changes during the loop
                remove_indices.insert(0, idx)
            idx += 1

        if matched:
            del remove_indices[0]

        for idx1 in reversed(remove_indices):
            ret += self._queue[idx1].list_rtp_meta_frame()
            timestamp_group_matched_n += 1 if self._queue[idx1].is_meta_frame_matched else 0

        for idx1 in remove_indices:
            del self._queue[idx1]

        if len(ret) > 0:
            return True, ret, matched, len(remove_indices), timestamp_group_matched_n
        else:
            return False, None, matched, len(remove_indices), timestamp_group_matched_n


class DeadlineSyncPolicy(SyncPolicy):
    def __init__(self, queue_size):
        super(DeadlineSyncPolicy, self).__init__()
        if queue_size < 1:
            raise Exception("invalid queue size, must greater than zero")
        self._queue_size = queue_size
        self._queue = collections.deque([], self._queue_size)
        print("deadline synchronize policy created, pid = %d, queue size = %d" % (os.getpid(), self._queue_size))

    def _append_video_pkt_meta_frame_items(self, rtp_pkt_item, meta_frame_item):
        try:
            _, timestamp_group = self._index_timestamp_group(rtp_pkt_item.index)
            timestamp_group.append(rtp_pkt_item)
            if meta_frame_item is not None:
                timestamp_group.meta_frame_item = meta_frame_item
            return None
        except ValueError:
            # no any RTP packet groups with the index (linear timestamp space) in the queue yet
            timestamp_group = self._timestamp_group_queue_class(rtp_pkt_item, meta_frame_item)
            overflow_timestamp_group = None
            if len(self._queue) == self._queue_size:
                overflow_timestamp_group = self._queue.popleft()
            self._queue.append(timestamp_group)
            return overflow_timestamp_group

    def _handle_video_pkt_meta_frame_items(self, rtp_pkt_item, meta_frame_item):
        overflow_timestamp_group = self._append_video_pkt_meta_frame_items(rtp_pkt_item, meta_frame_item)
        if overflow_timestamp_group is None:
            return False, None, 0, 0
        return (True, overflow_timestamp_group.list_rtp_meta_frame(), 1,
                1 if overflow_timestamp_group.is_meta_frame_matched else 0)

    def handle_video_pkt_meta_frame(self, rtp_pkt, rtp_pkt_index, meta_frame, meta_frame_index):
        _, _, matched, _, _ = self.handle_meta_frame(meta_frame, meta_frame_index)

        rtp_pkt_item = _RTPPackageItem(rtp_pkt, rtp_pkt_index)

        if not matched and rtp_pkt_item.index == meta_frame_index:
            mf_item = _MetadataFrameItem(meta_frame, meta_frame_index)
            matched = True
        else:
            mf_item = None

        handled, ret, timestamp_group_n, timestamp_group_matched_n =\
            self._handle_video_pkt_meta_frame_items(rtp_pkt_item, mf_item)
        return handled, ret, matched, timestamp_group_n, timestamp_group_matched_n

    def handle_video_pkt(self, rtp_pkt, rtp_pkt_index):
        rtp_pkt_item = _RTPPackageItem(rtp_pkt, rtp_pkt_index)
        return self._handle_video_pkt_meta_frame_items(rtp_pkt_item, None)

    def handle_meta_frame(self, meta_frame, meta_frame_index):
        meta_frame_item = _MetadataFrameItem(meta_frame, meta_frame_index)

        matched = False
        for timestamp_group in self._queue:
            if timestamp_group.index1 == meta_frame_item.index:
                timestamp_group.meta_frame_item = meta_frame_item
                matched = True
        return False, None, matched, 0, 0


class SyncNonePolicy(SyncPolicy):
    def __init__(self):
        super(SyncNonePolicy, self).__init__()
        print("None synchronize policy created, pid = %d" % os.getpid())

    def handle_video_pkt_meta_frame(self, rtp_pkt, rtp_pkt_index, meta_frame, meta_frame_index):
        rtp_pkt_item = _RTPPackageItem(rtp_pkt, rtp_pkt_index)
        meta_frame_item = _MetadataFrameItem(meta_frame, meta_frame_index)

        if rtp_pkt_item.index == meta_frame_item.index:
            mf_item = meta_frame_item
            matched = True
        else:
            mf_item = None
            matched = False

        timestamp_group = self._timestamp_group_queue_class(rtp_pkt_item, mf_item)
        return (True, timestamp_group.list_rtp_meta_frame(), matched, 1,
                1 if timestamp_group.is_meta_frame_matched else 0)

    def handle_video_pkt(self, rtp_pkt, rtp_pkt_index):
        rtp_pkt_item = _RTPPackageItem(rtp_pkt, rtp_pkt_index)
        timestamp_group = self._timestamp_group_queue_class(rtp_pkt_item, None)
        return True, timestamp_group.list_rtp_meta_frame(), 1, 0

    def handle_meta_frame(self, meta_frame, meta_frame_index):
        return False, None, False, 0, 0


def create_sync_policy():
    policy = None
    try:
        policy_name = constants.get_sync_pkt_policy()
        if constants.SYNC_PACKET_POLICY_TYPE_ONE_SHOT == policy_name:
            policy = OneShotSyncPolicy(constants.get_sync_pkt_policy_queue_size())
        elif constants.SYNC_PACKET_POLICY_TYPE_DEADLINE == policy_name:
            policy = DeadlineSyncPolicy(constants.get_sync_pkt_policy_queue_size())
        else:
            policy = SyncNonePolicy()
    except Exception as e:
        print("failed to create synchronization policy: %s" % str(e))
    return policy
