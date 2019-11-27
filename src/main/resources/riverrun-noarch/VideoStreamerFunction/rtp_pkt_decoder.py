import os
import threading

import bitstruct
import kaitaistruct

import rtp_payload
import rtp_pkt as rtp_packet


class RTPPacketSimpleDecoder:
    def __init__(self, source_id):
        self._source_id = source_id
        self._nal_unit_buff = b""
        self._nal_unit_type = None
        self._nal_unit_complete = None
        self._nal_packer = bitstruct.compile("u1u2u5")
        self._nal_stream_packer = bitstruct.compile("u24")
        # log latest RTP timestamp
        self._latest_rtp_timestamp = None
        # log frame statistics
        self._received_i_frame_count = 0
        self._received_slice_count = 0
        self._received_sps_count = 0
        self._received_pps_count = 0
        self._start_log_routine()
        print("RTP packet simple decoder created, pid = %d, client source id = %d" % (os.getpid(), self._source_id))

    def _start_log_routine(self):
        self._log_timer = threading.Timer(5, self._log_routine)
        self._log_timer.start()

    def _log_routine(self):
        # log latest RTP timestamp
        if self._latest_rtp_timestamp is not None:
            print("RTP timestamp reaches %d" % self._latest_rtp_timestamp)
            self._latest_rtp_timestamp = None  # reset
        # log frame statistics
        print("the number of received I frame from the source #%d in last 5 seconds: %d" %
              (self._source_id, self._received_i_frame_count))
        print("the number of received slice (include P and B frame) from the source #%d in last 5 seconds: %d" %
              (self._source_id, self._received_slice_count))
        print("the number of received SPS from the source #%d in last 5 seconds: %d" %
              (self._source_id, self._received_sps_count))
        print("the number of received PPS from the source #%d in last 5 seconds: %d" %
              (self._source_id, self._received_pps_count))
        # reset
        self._received_i_frame_count = 0
        self._received_slice_count = 0
        self._received_sps_count = 0
        self._received_pps_count = 0
        self._start_log_routine()

    def _update_frame_statistics(self, rtp_pkt_payload):
        if rtp_payload.RTPPayload.NALUnitTypeEnum.pps == rtp_pkt_payload.nal_unit_type:
            self._received_pps_count += 1
        elif rtp_payload.RTPPayload.NALUnitTypeEnum.sps == rtp_pkt_payload.nal_unit_type:
            self._received_sps_count += 1
        elif rtp_payload.RTPPayload.NALUnitTypeEnum.idr == rtp_pkt_payload.nal_unit_type:
            self._received_i_frame_count += 1
        elif rtp_payload.RTPPayload.NALUnitTypeEnum.slice == rtp_pkt_payload.nal_unit_type:
            self._received_slice_count += 1

    def _process_nal_unit(self):
        # buff = self._nal_stream_packer.pack(0x000001)
        # buff += self._nal_unit_buff
        # H264 file starts from a SPS NAL unit to make player works
        pass

    def put(self, rtp_pkt):
        if rtp_pkt is None:
            raise Exception("RTP packet is None")

        rtp_pkt_pdu = None
        rtp_pkt_payload = None

        try:
            rtp_pkt_pdu = rtp_packet.RtpPacket(kaitaistruct.KaitaiStream(kaitaistruct.BytesIO(rtp_pkt)))
            self._latest_rtp_timestamp = rtp_pkt_pdu.timestamp

            rtp_pkt_payload = rtp_payload.RTPPayload(kaitaistruct.KaitaiStream(kaitaistruct.BytesIO(rtp_pkt_pdu.data)))

            if not rtp_pkt_payload.fragment_nal_unit:  # single NAL unit
                if self._nal_unit_complete is not None:
                    print("WARN: wrong order (or invalid) RTP single NAL unit detected, skip the packet")
                    return

                self._nal_unit_buff = self._nal_packer.pack(rtp_pkt_payload.f, rtp_pkt_payload.nri,
                                                            int(rtp_pkt_payload.nal_unit_type))
                self._nal_unit_buff += rtp_pkt_payload.data
                self._nal_unit_type = rtp_pkt_payload.nal_unit_type
                self._nal_unit_complete = True
                self._update_frame_statistics(rtp_pkt_payload)
            else:  # FU-A fragmentation
                if 1 == rtp_pkt_payload.start_bit and 0 == rtp_pkt_payload.end_bit:  # first fragment
                    if self._nal_unit_complete is not None and not self._nal_unit_complete:
                        print("WARN: wrong order (or invalid) RTP FU-A NAL fragmentation detected, skip the packet")
                        return

                    self._nal_unit_buff = self._nal_packer.pack(rtp_pkt_payload.f, rtp_pkt_payload.nri,
                                                                int(rtp_pkt_payload.nal_unit_type))
                    self._nal_unit_buff += rtp_pkt_payload.data
                    self._nal_unit_type = rtp_pkt_payload.nal_unit_type
                    self._nal_unit_complete = False
                    self._update_frame_statistics(rtp_pkt_payload)
                elif 0 == rtp_pkt_payload.start_bit and 0 == rtp_pkt_payload.end_bit:  # middle fragment
                    if self._nal_unit_complete is not None and self._nal_unit_complete:
                        print("WARN: wrong order (or invalid) RTP FU-A fragmentation detected, skip the packet")
                        return

                    self._nal_unit_complete = False
                    self._nal_unit_buff += rtp_pkt_payload.data
                elif 0 == rtp_pkt_payload.start_bit and 1 == rtp_pkt_payload.end_bit:  # last fragment
                    if self._nal_unit_complete is not None and self._nal_unit_complete:
                        print("WARN: wrong order (or invalid) RTP FU-A fragmentation detected, skip the packet")
                        return

                    self._nal_unit_buff += rtp_pkt_payload.data
                    self._nal_unit_complete = True
                else:
                    raise Exception("RTP packet is invalid, unknown start/end bit of the FU-A fragmentation")

            if self._nal_unit_complete:
                try:
                    self._process_nal_unit()
                finally:
                    # reset
                    self._nal_unit_complete = None
                    self._nal_unit_buff = b''
                    self._nal_unit_type = None

        except Exception as e:
            print("failed to parse RTP packet: %s" % str(e))
        finally:
            if rtp_pkt_payload is not None:
                rtp_pkt_payload.close()
            if rtp_pkt_pdu is not None:
                rtp_pkt_pdu.close()

    def release(self):
        self._log_timer.cancel()
        print("RTP packet simple decoder released, pid = %d, client source id = %d" % (os.getpid(), self._source_id))
