import requests
from utilities import (
    generate_data_for_like_on_post,
    generate_data_for_like_on_comment,
    generate_data_for_comment_on_post,
    generate_data_for_comment_on_comment,
    generate_data_for_send_friend_req,
    generate_data_for_send_friend_req_ack,
    generate_data_for_mention
)

BASE_URL = "http://127.0.0.1:8000"

def test_like_post():
    url = f"{BASE_URL}/api/like_post"
    data = generate_data_for_like_on_post()
    requests.post(url, data=data)

def test_like_comment():
    url = f"{BASE_URL}/api/like_comment"
    data = generate_data_for_like_on_comment()
    requests.post(url, data=data)

def test_comment_post():
    url = f"{BASE_URL}/api/comment_post"
    data = generate_data_for_comment_on_post()
    requests.post(url, data=data)

def test_comment_comment():
    url = f"{BASE_URL}/api/comment_comment"
    data = generate_data_for_comment_on_comment()
    requests.post(url, data=data)

def test_send_friend_req():
    url = f"{BASE_URL}/api/send_friend_req"
    data = generate_data_for_send_friend_req()
    requests.post(url, data=data)

def test_send_friend_req_ack():
    url = f"{BASE_URL}/api/send_friend_req_ack"
    data = generate_data_for_send_friend_req_ack()
    requests.post(url, data=data)

def test_mention():
    url = f"{BASE_URL}/api/mention"
    data = generate_data_for_mention()
    requests.post(url, data=data)

if __name__ == "__main__":
    for _ in range(2): 
        test_like_post()
        test_like_comment()
        test_comment_post()
        test_comment_comment()
        test_send_friend_req()
        test_send_friend_req_ack()
        test_mention()