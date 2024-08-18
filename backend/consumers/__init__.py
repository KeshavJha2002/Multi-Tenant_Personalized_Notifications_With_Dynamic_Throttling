from .consumer_like import run as run_like_consumer
from .consumer_comment import run as run_comment_consumer

__all__ = ["generate_data_for_like_on_post", "generate_data_for_like_on_comment", "generate_data_for_comment_on_post", "generate_data_for_comment_on_comment", "generate_data_for_send_friend_req", "generate_data_for_send_friend_req_ack", "generate_data_for_mention"] 