import constants
import frame_subscriber
import frame_receiver


# Income
def create_receiver():
    receiver_port = constants.get_meta_frame_server_port()
    return frame_receiver.FrameReceiver(port=receiver_port)


def create_subscriber():
    subscriber_port = constants.get_meta_frame_server_port()
    topic = constants.get_meta_frame_subscribe_topic()
    if "" == topic:
        subscriber = frame_subscriber.FrameSubscriber(port=subscriber_port)
    else:
        subscriber = frame_subscriber.FrameSubscriber(port=subscriber_port, topic=topic)
    return subscriber


def create_taker():
    taker = None
    take_type = constants.get_meta_frame_take_type()
    if constants.METADATA_FRAME_TAKE_TYPE_SUBSCRIBE == take_type:
        taker = create_subscriber()
    elif constants.METADATA_FRAME_TAKE_TYPE_RESPONSE == take_type:
        taker = create_receiver()

    if taker is None:
        print("Invalid environment variables provided for video processor")
        print("Variable %s must be %s or %s, exits" %
              (constants.METADATA_FRAME_TAKE_TYPE_ENV_VAR_NAME, constants.METADATA_FRAME_TAKE_TYPE_RESPONSE,
               constants.METADATA_FRAME_TAKE_TYPE_SUBSCRIBE))
    return taker
