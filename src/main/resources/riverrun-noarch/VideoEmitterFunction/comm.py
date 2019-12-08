import constants
import video_publisher
from video_reader import horizon_x2
from video_reader import net_sock
import video_sender


def create_reader():
    read_type = constants.get_video_packet_read_type()
    if constants.READ_TYPE_HORIZON_SDK == read_type:
        shm_filename = constants.get_shm_filename()
        if "" == shm_filename:
            print("Invalid environment variables provided for video packet reader")
            print("Variable %s is necessary, exits" % constants.VIDEO_RTP_PACKET_SHM_FILENAME)
            reader = None
        else:
            reader = horizon_x2.VideoPacketHoBotX2SDKReader()
    elif constants.READ_TYPE_NET_SOCKET == read_type:
        port = constants.get_net_socket_server_port()
        reader = net_sock.VideoPacketNetSocketReader(port=port)
    else:
        reader = None

    if reader is None:
        print("Invalid environment variables provided for video packet reader")
        print("Variable %s is necessary, exits" % constants.READ_TYPE_ENV_VAR_NAME)
        print("Variable %s must be %s or %s, exits" %
              (constants.READ_TYPE_ENV_VAR_NAME, constants.READ_TYPE_HORIZON_SDK, constants.READ_TYPE_NET_SOCKET))
        print("Variable %s must be configured when variable %s is configured to %s, exits" %
              (constants.SHM_FILENAME_ENV_VAR_NAME, constants.READ_TYPE_ENV_VAR_NAME, constants.READ_TYPE_HORIZON_SDK))
    return reader


def create_udp_sender():
    receiver_ip, receiver_port = constants.get_server_ip_port()
    if "" == receiver_ip:
        sender = None
    else:
        sender = video_sender.RTPPacketUDPSender(receiver_ip, port=receiver_port)
    return sender


def create_requester():
    receiver_ip, receiver_port = constants.get_server_ip_port()
    if "" == receiver_ip:
        sender = None
    else:
        sender = video_sender.RTPPacketTCPSender(receiver_ip, port=receiver_port)
    return sender


def create_publisher():
    subscriber_ip, subscriber_port = constants.get_server_ip_port()
    topic = constants.get_publish_topic()
    if "" == subscriber_ip:
        publisher = None
    elif "" == topic:
        publisher = video_publisher.RTPPacketPublisher(subscriber_ip, port=subscriber_port)
    else:
        publisher = video_publisher.RTPPacketPublisher(subscriber_ip, port=subscriber_port, topic=topic)
    return publisher


def create_emitter():
    emitter = None
    emit_type = constants.get_client_emit_type()
    if constants.EMIT_TYPE_PUBLISH == emit_type:
        emitter = create_publisher()
    elif constants.EMIT_TYPE_REQUEST == emit_type:
        emitter = create_requester()
    elif constants.EMIT_TYPE_UDP == emit_type:
        emitter = create_udp_sender()

    if emitter is None:
        print("Invalid environment variables provided for video packet sender")
        print("Variable %s is necessary, exits" % constants.SERVER_IP_ENV_VAR_NAME)
        print("Variable %s must be %s %s or %s, exits" %
              (constants.EMIT_TYPE_ENV_VAR_NAME, constants.EMIT_TYPE_UDP,
               constants.EMIT_TYPE_REQUEST, constants.EMIT_TYPE_PUBLISH))
    return emitter
