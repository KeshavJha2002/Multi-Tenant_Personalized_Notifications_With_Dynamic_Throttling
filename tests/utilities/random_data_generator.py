import json
import random
import time



def generate_data_for_like_on_post():
  action_type = "LIKE"
  action_on = "POST"
  action_on_id = f"post_{random.randint(1, 1_000_000)}"
  action_by = f"user_{random.randint(1, 10000)}"
  action_to = f"user_{random.randint(1, 10000)}"
  action_at = int(time.time() * 1000)  # Timestamp in milliseconds
  data = {
      "action_type": action_type,
      "action_on": action_on,
      "action_on_id": action_on_id,
      "action_by": action_by,
      "action_to": action_to,
      "action_at": action_at
  }
  return json.dumps(data)



def generate_data_for_like_on_comment():
  action_type = "LIKE"
  action_on = "COMMENT"
  action_on_id = f"comment_{random.randint(1, 1_000_000)}"
  action_by = f"user_{random.randint(1, 10000)}"
  action_to = f"user_{random.randint(1, 10000)}"
  action_at = int(time.time() * 1000)  # Timestamp in milliseconds
  data = {
      "action_type": action_type,
      "action_on": action_on,
      "action_on_id": action_on_id,
      "action_by": action_by,
      "action_to": action_to,
      "action_at": action_at
  }
  return json.dumps(data)



def generate_data_for_comment_on_post():
  action_type = "COMMENT"
  action_on = "POST"
  action_on_id = f"post_{random.randint(1, 1_000_000)}"
  action_by = f"user_{random.randint(1, 10000)}"
  action_to = f"user_{random.randint(1, 10000)}"
  action_at = int(time.time() * 1000)  # Timestamp in milliseconds
  data = {
      "action_type": action_type,
      "action_on": action_on,
      "action_on_id": action_on_id,
      "action_by": action_by,
      "action_to": action_to,
      "action_at": action_at
  }
  return json.dumps(data)



def generate_data_for_comment_on_comment():
  action_type = "COMMENT"
  action_on = "COMMENT"
  action_on_id = f"comment_{random.randint(1, 1_000_000)}"
  action_by = f"user_{random.randint(1, 10000)}"
  action_to = f"user_{random.randint(1, 10000)}"
  action_at = int(time.time() * 1000)  # Timestamp in milliseconds
  data = {
      "action_type": action_type,
      "action_on": action_on,
      "action_on_id": action_on_id,
      "action_by": action_by,
      "action_to": action_to,
      "action_at": action_at
  }
  return json.dumps(data)



def generate_data_for_send_friend_req():
  action_type = "FRIEND_REQ"
  action_by = f"user_{random.randint(1, 10000)}"
  action_on = f"user_{random.randint(1, 10000)}"
  action_at = int(time.time() * 1000)  # Timestamp in milliseconds
  data = {
      "action_type": action_type,
      "action_by": action_by,
      "action_on": action_on,
      "action_at": action_at
  }
  return json.dumps(data)



def generate_data_for_send_friend_req_ack():
  action_type = "FRIEND_REQ_ACK"
  action_by = f"user_{random.randint(1, 10000)}"
  action_on = f"user_{random.randint(1, 10000)}"
  action_at = int(time.time() * 1000)  # Timestamp in milliseconds
  data = {
      "action_type": action_type,
      "action_by": action_by,
      "action_on": action_on,
      "action_at": action_at
  }
  return json.dumps(data)

def generate_data_for_mention():
  action_types = ["POST", "COMMENT", "CONVERSATION"]
  action_type = "MENTION"
  action_on = random.choice(action_types)
  action_on_id = f"{action_on}_{random.randint(1, 10000)}"
  action_by = f"user_{random.randint(1, 10000)}"
  action_to = f"user_{random.randint(1, 10000)}"
  action_at = int(time.time() * 1000)  # Timestamp in milliseconds
  data = {
      "action_type": action_type,
      "action_by": action_by,
      "action_on": action_on,
      "action_on_id": action_on_id,
      "action_to": action_to,
      "action_at": action_at
  }
  return json.dumps(data)

