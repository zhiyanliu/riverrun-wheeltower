import log_server
import dump_server


def sync_pkt_logging_server_creator(stat_queue, log_queue, decoder_class, source_id):
    return log_server.LoggingServer(
        "logging server (for client source id #%d)" % source_id,
        stat_queue, log_queue, decoder_class, source_id)


def sync_pkt_dump_server_creator(stat_queue, dump_queue, source_id):
    return dump_server.DumpServer(
        "RTP packet dump server (for client source id #%d)" % source_id,
        stat_queue, dump_queue, source_id)
