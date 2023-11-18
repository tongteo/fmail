from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)

def query_mailbox(mailbox, message_id=None):
    endpoint = "https://api.maildrop.cc/graphql"
    headers = {"content-type": "application/json"}

    if message_id:
        query = f"""
        {{
            "query": "query GetMessage {{ message(mailbox:\\"{mailbox}\\", id:\\"{message_id}\\") {{ id headerfrom subject date html }} }}"
        }}
        """
    else:
        query = f"""
        {{
            "query": "query GetInbox {{ inbox(mailbox:\\"{mailbox}\\") {{ id headerfrom subject date html }} }}"
        }}
        """

    response = requests.post(endpoint, headers=headers, data=query)
    response_json = response.json()

    return response_json


def save_database(email_list):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS emails
                 (email text)''')

    c.execute("DELETE FROM emails")

    for email in email_list:
        c.execute("INSERT INTO emails VALUES (?)", (email,))

    conn.commit()
    conn.close()

def load_database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS emails
                 (email text)''')

    c.execute("SELECT * FROM emails")

    email_list = [row[0] for row in c.fetchall()]

    conn.close()

    return email_list

email_list = load_database()

@app.route('/api/add_email', methods=['POST'])
def add_email():
    email = request.json.get('email')
    if email not in email_list and len(email_list) < 1000:
        email_list.append(email)
        save_database(email_list)
        return jsonify({'message': 'Email added successfully'}), 200
    else:
        return jsonify({'message': 'Email list is full or email already exists'}), 400

@app.route('/api/get_emails', methods=['GET'])
def get_emails():
    return jsonify(email_list), 200

@app.route('/api/get_mailbox', methods=['GET'])
def get_mailbox():
    email_index = request.args.get('email_index')
    if 0 < int(email_index) <= len(email_list):
        email_name = email_list[int(email_index) - 1]
        result = query_mailbox(email_name)
        return jsonify(result), 200
    else:
        return jsonify({'message': 'Invalid email index'}), 400

@app.route('/api/get_message', methods=['GET'])
def get_message():
    email_index = request.args.get('email_index')
    message_id = request.args.get('message_id')
    if 0 < int(email_index) <= len(email_list):
        email_name = email_list[int(email_index) - 1]
        result = query_mailbox(email_name, message_id)
        return jsonify(result), 200
    else:
        return jsonify({'message': 'Invalid email index'}), 400

if __name__ == "__main__":
    app.run(debug=True)
