import os

# Income synchronized packet
SYNC_PACKET_SERVER_PORT_ENV_VAR_NAME = "SYNC_PACKET_SERVER_PORT"
SYNC_PACKET_SERVER_HEARTBEAT_INTERVAL_SEC_ENV_VAR_NAME = "SYNC_PACKET_SERVER_HEARTBEAT_INTERVAL_SEC"

# Outcome RTP packet
RTP_PACKET_FILE_SAVE_PATH_ENV_VAR_NAME = "RTP_PACKET_FILE_SAVE_PATH"
VIDEO_PACKET_FILE_SAVE_PATH_ENV_VAR_NAME = "VIDEO_PACKET_FILE_SAVE_PATH"
METADATA_FRAME_FILE_SAVE_PATH_ENV_VAR_NAME = "METADATA_FRAME_FILE_PATH"


# Income
def get_sync_pkt_server_port(default_server_port=9532):
    os.environ.setdefault(SYNC_PACKET_SERVER_PORT_ENV_VAR_NAME, str(default_server_port))

    try:
        port = int(os.environ[SYNC_PACKET_SERVER_PORT_ENV_VAR_NAME].strip())
    except ValueError:
        port = default_server_port

    return port


def get_sync_pkt_server_heartbeat_interval_sec(default_interval=30):
    os.environ.setdefault(SYNC_PACKET_SERVER_HEARTBEAT_INTERVAL_SEC_ENV_VAR_NAME, str(default_interval))

    try:
        timeout = int(os.environ[SYNC_PACKET_SERVER_HEARTBEAT_INTERVAL_SEC_ENV_VAR_NAME].strip())
    except ValueError:
        timeout = default_interval

    return timeout


# Outcome
def get_rtp_packet_file_save_path(default_path="/tmp/riverrun-streamer/video_rtp.dump"):
    os.environ.setdefault(RTP_PACKET_FILE_SAVE_PATH_ENV_VAR_NAME, default_path)
    return os.environ[RTP_PACKET_FILE_SAVE_PATH_ENV_VAR_NAME].strip()


def get_video_packet_file_save_path(default_path="/tmp/riverrun-streamer/video_packet.dump"):
    os.environ.setdefault(VIDEO_PACKET_FILE_SAVE_PATH_ENV_VAR_NAME, default_path)
    return os.environ[VIDEO_PACKET_FILE_SAVE_PATH_ENV_VAR_NAME].strip()


def get_metadata_frame_file_save_path(default_path="/tmp/riverrun-streamer/metadata_frame.dump"):
    os.environ.setdefault(METADATA_FRAME_FILE_SAVE_PATH_ENV_VAR_NAME, default_path)
    return os.environ[METADATA_FRAME_FILE_SAVE_PATH_ENV_VAR_NAME].strip()
