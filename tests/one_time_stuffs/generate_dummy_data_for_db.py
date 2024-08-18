"""
The following is a one-time script to create dummy data for the database
to simulate users of the social media platform.
Use the generated csv file, or create your own csv file to with test cases as per your need
"""

import csv
import random

def generate_user_data(num_users):
  users = []
  for i in range(num_users):
    user_id = f"user_{i+1}"
    in_app_notifications = random.choice([True, False])
    mail_notifications = random.choice([True, False])
    mail_like_notifications = random.choice([True, False])
    mail_comment_notifications = random.choice([True, False])
    mail_mention_notifications = random.choice([True, False])
    mail_connection_notifications = random.choice([True, False])
    users.append({
      "user_id": user_id,
      "in_app_notifications": in_app_notifications,
      "mail_notifications": mail_notifications,
      "mail_like_notifications": mail_like_notifications,
      "mail_comment_notifications": mail_comment_notifications,
      "mail_mention_notifications": mail_mention_notifications,
      "mail_connection_notifications": mail_connection_notifications
    })
  return users

def create_csv(data, filename):
  fieldnames = ["user_id", "in_app_notifications", "mail_notifications", "mail_like_notifications", "mail_comment_notifications", "mail_mention_notifications", "mail_connection_notifications"]
  with open(filename, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

# Generate sample data
num_users = 10_000
user_data = generate_user_data(num_users)

# Create CSV file
output_filename = "user_data_db_one_time_creation.csv"
create_csv(user_data, output_filename)