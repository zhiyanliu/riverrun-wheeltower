import constants
import sync_pkt_receiver


# Income
def create_sync_pkt_receiver(stat_queue, sync_pkt_queue_size=20):
    port = constants.get_sync_pkt_server_port()
    receiver = sync_pkt_receiver.SyncPacketTCPReceiver(stat_queue, sync_pkt_queue_size, port)
    return receiver
