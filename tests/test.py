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
import threading
import time
from random import choice

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

test_functions = [
    test_like_post,
    test_like_comment,
    test_comment_post,
    test_comment_comment,
    test_send_friend_req,
    test_send_friend_req_ack,
    test_mention
]

# def worker():
#     while True:
#         func = choice(test_functions)  # Randomly select a test function
#         func()
#         time.sleep(1)  # Sleep to prevent overwhelming the server with requests

# def main():
#     threads = []
#     try:
#         # Create and start 100 threads
#         for _ in range(100):
#             t = threading.Thread(target=worker)
#             t.daemon = True  # Daemonize thread to ensure it exits when the main program exits
#             t.start()
#             threads.append(t)
            
#         for t in threads:
#             t.join()
#     except KeyboardInterrupt:
#         print("Interrupted by user. Stopping threads...")

def main():
    test_like_post()
    test_like_comment()
    # test_comment_post()
    # test_comment_comment()
    # test_send_friend_req()
    # test_send_friend_req_ack()
    # test_mention()

if __name__ == "__main__":
    main()