import struct

import kaitaistruct

import rtp_pkt as rtp_packet


def _parse_timestamp_fast(rtp_pkt):
    try:
        timestamp = struct.unpack('!i', rtp_pkt[4:8])[0]
        return True, timestamp
    except Exception as e:
        print("failed to parse RTP packet: %s" % str(e))
        return False, None


def _parse_timestamp_complete(rtp_pkt):
    rtp_pkt_pdu = None
    try:
        rtp_pkt_pdu = rtp_packet.RtpPacket(kaitaistruct.KaitaiStream(kaitaistruct.BytesIO(rtp_pkt)))
        return True, rtp_pkt_pdu.timestamp
    except Exception as e:
        print("failed to parse RTP packet: %s" % str(e))
        return False, None
    finally:
        if rtp_pkt_pdu is not None:
            rtp_pkt_pdu.close()


class RTPPacket:
    def __init__(self, rtp_pkt, fast_parse=True):
        if rtp_pkt is None:
            raise Exception("RTP packet is None")
        self.buff = rtp_pkt

        if fast_parse:
            ret, self.timestamp = _parse_timestamp_fast(self.buff)
        else:
            ret, self.timestamp = _parse_timestamp_complete(self.buff)
        if not ret:
            raise Exception("RTP packet is invalid")
