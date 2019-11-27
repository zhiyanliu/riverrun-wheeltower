import constants
import video_subscriber
import video_receiver


# Income
def create_udp_receiver():
    receiver_port = constants.get_video_stream_server_port()
    return video_receiver.VideoRTPUDPReceiver(port=receiver_port)


def create_responser():
    receiver_port = constants.get_video_stream_server_port()
    return video_receiver.VideoRTPTCPReceiver(port=receiver_port)


def create_subscriber():
    subscriber_port = constants.get_video_stream_server_port()
    topic = constants.get_video_stream_subscribe_topic()
    if "" == topic:
        subscriber = video_subscriber.VideoRTPPacketSubscriber(port=subscriber_port)
    else:
        subscriber = video_subscriber.VideoRTPPacketSubscriber(port=subscriber_port, topic=topic)
    return subscriber


def create_taker():
    taker = None
    take_type = constants.get_video_stream_take_type()
    if constants.VIDEO_STREAM_TAKE_TYPE_SUBSCRIBE == take_type:
        taker = create_subscriber()
    elif constants.VIDEO_STREAM_TAKE_TYPE_RESPONSE == take_type:
        taker = create_responser()
    elif constants.VIDEO_STREAM_TAKE_TYPE_UDP == take_type:
        taker = create_udp_receiver()

    if taker is None:
        print("Invalid environment variables provided for video processor")
        print("Variable %s must be %s %s or %s, exits" %
              (constants.VIDEO_STREAM_TAKE_TYPE_ENV_VAR_NAME, constants.VIDEO_STREAM_TAKE_TYPE_UDP,
               constants.VIDEO_STREAM_TAKE_TYPE_RESPONSE, constants.VIDEO_STREAM_TAKE_TYPE_SUBSCRIBE))
    return taker
