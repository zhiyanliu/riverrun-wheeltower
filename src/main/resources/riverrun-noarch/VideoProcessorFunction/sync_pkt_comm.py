import constants
import sync_pkt_sender


# Outcome
def create_sync_pkt_combiner():
    return sync_pkt_sender.SyncPacketCombiner()


def create_sync_pkt_sender():
    ip, port = constants.get_sync_pkt_server_ip_port()
    if "" == ip:
        sender = sync_pkt_sender.SyncPacketNoneSender()  # eat all outputs, in test?
        print("None synchronized packet sender is used, no any synchronized packets out")
    else:
        sender = sync_pkt_sender.SyncPacketTCPSender(ip, port)
    return sender


def create_emitter():
    emitter = create_sync_pkt_sender()
    return emitter
