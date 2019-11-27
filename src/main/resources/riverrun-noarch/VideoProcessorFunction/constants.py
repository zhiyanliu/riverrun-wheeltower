import os

# Income metadata frame
METADATA_FRAME_SERVER_PORT_ENV_VAR_NAME = "METADATA_FRAME_SERVER_PORT"
METADATA_FRAME_SUBSCRIBE_TOPIC_ENV_VAR_NAME = "METADATA_FRAME_SUBSCRIBE_TOPIC"
METADATA_FRAME_TAKE_TYPE_ENV_VAR_NAME = "METADATA_FRAME_TAKE_TYPE"

METADATA_FRAME_TAKE_TYPE_SUBSCRIBE = "SUB"
METADATA_FRAME_TAKE_TYPE_RESPONSE = "REP"

METADATA_FRAME_THROTTLE_TOLERATE_COUNT_ENV_VAR_NAME = "METADATA_FRAME_THROTTLE_TOLERATE_COUNT"

# Income video stream
VIDEO_STREAM_SERVER_PORT_ENV_VAR_NAME = "VIDEO_STREAM_SERVER_PORT"
VIDEO_STREAM_SUBSCRIBE_TOPIC_ENV_VAR_NAME = "VIDEO_STREAM_SUBSCRIBE_TOPIC"
VIDEO_STREAM_TAKE_TYPE_ENV_VAR_NAME = "VIDEO_STREAM_TAKE_TYPE"

VIDEO_STREAM_TAKE_TYPE_SUBSCRIBE = "SUB"
VIDEO_STREAM_TAKE_TYPE_RESPONSE = "REP"
VIDEO_STREAM_TAKE_TYPE_UDP = "UDP"

# Outcome synchronized packet
SYNC_PACKET_SERVER_IP_ENV_VAR_NAME = "SYNC_PACKET_SERVER_IP"
SYNC_PACKET_SERVER_PORT_ENV_VAR_NAME = "SYNC_PACKET_SERVER_PORT"
SYNC_PACKET_SERVER_HEARTBEAT_TIMEOUT_SEC_ENV_VAR_NAME = "SYNC_PACKET_SERVER_HEARTBEAT_TIMEOUT_SEC"

SYNC_PACKET_POLICY_TYPE_ENV_VAR_NAME = "SYNC_PACKET_POLICY_TYPE"

SYNC_PACKET_POLICY_TYPE_ONE_SHOT = "ONE_SHOT"
SYNC_PACKET_POLICY_TYPE_DEADLINE = "DEADLINE"
SYNC_PACKET_POLICY_QUEUE_SIZE_ENV_VAR_NAME = "SYNC_PACKET_POLICY_QUEUE_SIZE"

SYNC_PACKET_POLICY_SEND_METADATA_FRAME_ONCE_ENV_VAR_NAME = "SYNC_PACKET_POLICY_SEND_METADATA_FRAME_ONCE"


_positive_terms = ["1", "on", "true", "t", "yes", "y", "ok"]


# Income
def get_meta_frame_server_port(default_server_port=9528):
    os.environ.setdefault(METADATA_FRAME_SERVER_PORT_ENV_VAR_NAME, str(default_server_port))

    try:
        port = int(os.environ[METADATA_FRAME_SERVER_PORT_ENV_VAR_NAME].strip())
    except ValueError:
        port = default_server_port

    return port


def get_meta_frame_subscribe_topic(default_topic="md"):
    os.environ.setdefault(METADATA_FRAME_SUBSCRIBE_TOPIC_ENV_VAR_NAME, str(default_topic))
    return os.environ[METADATA_FRAME_SUBSCRIBE_TOPIC_ENV_VAR_NAME].strip()


def get_meta_frame_take_type(default_type=METADATA_FRAME_TAKE_TYPE_SUBSCRIBE):
    os.environ.setdefault(METADATA_FRAME_TAKE_TYPE_ENV_VAR_NAME, default_type)
    return os.environ[METADATA_FRAME_TAKE_TYPE_ENV_VAR_NAME].strip()


def get_meta_frame_throttle_tolerate_count(default_count=10):
    os.environ.setdefault(METADATA_FRAME_THROTTLE_TOLERATE_COUNT_ENV_VAR_NAME, str(default_count))

    try:
        count = int(os.environ[METADATA_FRAME_THROTTLE_TOLERATE_COUNT_ENV_VAR_NAME].strip())
    except ValueError:
        count = default_count

    return count


def get_video_stream_server_port(default_server_port=9530):
    os.environ.setdefault(VIDEO_STREAM_SERVER_PORT_ENV_VAR_NAME, str(default_server_port))

    try:
        port = int(os.environ[VIDEO_STREAM_SERVER_PORT_ENV_VAR_NAME].strip())
    except ValueError:
        port = default_server_port

    return port


def get_video_stream_subscribe_topic(default_topic="rtp"):
    os.environ.setdefault(VIDEO_STREAM_SUBSCRIBE_TOPIC_ENV_VAR_NAME, str(default_topic))
    return os.environ[VIDEO_STREAM_SUBSCRIBE_TOPIC_ENV_VAR_NAME].strip()


def get_video_stream_take_type(default_type=VIDEO_STREAM_TAKE_TYPE_RESPONSE):
    os.environ.setdefault(VIDEO_STREAM_TAKE_TYPE_ENV_VAR_NAME, default_type)
    return os.environ[VIDEO_STREAM_TAKE_TYPE_ENV_VAR_NAME].strip()


# Outcome
def get_sync_pkt_server_ip_port(default_server_port=9532):
    os.environ.setdefault(SYNC_PACKET_SERVER_IP_ENV_VAR_NAME, "")  # prevent KeyError error
    os.environ.setdefault(SYNC_PACKET_SERVER_PORT_ENV_VAR_NAME, str(default_server_port))

    try:
        port = int(os.environ[SYNC_PACKET_SERVER_PORT_ENV_VAR_NAME].strip())
    except ValueError:
        port = default_server_port

    return os.environ[SYNC_PACKET_SERVER_IP_ENV_VAR_NAME].strip(), port


def get_sync_pkt_server_heartbeat_timeout_sec(default_timeout=30):
    os.environ.setdefault(SYNC_PACKET_SERVER_HEARTBEAT_TIMEOUT_SEC_ENV_VAR_NAME, str(default_timeout))

    try:
        timeout = int(os.environ[SYNC_PACKET_SERVER_HEARTBEAT_TIMEOUT_SEC_ENV_VAR_NAME].strip())
    except ValueError:
        timeout = default_timeout

    return timeout


def get_sync_pkt_policy(default_policy=SYNC_PACKET_POLICY_TYPE_ONE_SHOT):
    os.environ.setdefault(SYNC_PACKET_POLICY_TYPE_ENV_VAR_NAME, default_policy)
    return os.environ[SYNC_PACKET_POLICY_TYPE_ENV_VAR_NAME].strip()


def get_sync_pkt_policy_queue_size(default_queue_size=15):
    os.environ.setdefault(SYNC_PACKET_POLICY_QUEUE_SIZE_ENV_VAR_NAME, str(default_queue_size))

    try:
        queue_size = int(os.environ[SYNC_PACKET_POLICY_QUEUE_SIZE_ENV_VAR_NAME].strip())
    except ValueError:
        queue_size = default_queue_size

    return queue_size


def get_sync_pkt_policy_whether_send_meta_frame_once(default_whether=True):
    os.environ.setdefault(SYNC_PACKET_POLICY_SEND_METADATA_FRAME_ONCE_ENV_VAR_NAME, "1" if default_whether else "0")
    if os.environ[SYNC_PACKET_POLICY_SEND_METADATA_FRAME_ONCE_ENV_VAR_NAME].strip().lower() in _positive_terms:
        return True
    else:
        return False
