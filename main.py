import Flask, request, jsonify
import requests
import json
import hashlib
import os
from datetime import datetime

app = Flask(__name__)

webhookUrl = "https://discord.com/api/webhooks/1153559821266722836/QbJlR7xfvcPndTN76NUatcFVENddx14gEEOw1iM9jMOI4DONXuwJFUfWyy_-8EYQF_63"
webhookUrl2 = "https://discord.com/api/webhooks/1153559821266722836/QbJlR7xfvcPndTN76NUatcFVENddx14gEEOw1iM9jMOI4DONXuwJFUfWyy_-8EYQF_63"

titleData = {}

def loadTitleDataFromFile():
    try:
        with open('titleData.json', 'r') as file:
            return json.load(file)
    except Exception as e:
        print(e)
        return {}

def saveTitleDataToFile(data):
    with open('titleData.json', 'w') as file:
        json.dump(data, file, indent=2)

def md5(data):
    return hashlib.md5(data.encode('utf-8')).hexdigest()

@app.route('/', methods=['GET'])
def get_title_data():
    global titleData
    print('Title data fetched: ', titleData)
    return jsonify(titleData)

@app.route('/', methods=['POST'])
def update_title_data():
    global titleData
    receivedData = request.json['data']
    titleData = receivedData
    saveTitleDataToFile(titleData)
    return jsonify({"message": "Data updated successfully"})

@app.route('/api/photon', methods=['POST'])
def photon_api():
    data = request.json
    user_id = data["UserId"]
    nonce = data["Nonce"]
    data["timestamp"] = datetime.utcnow().isoformat()
    print(data)
    send_to_discord_webhook(data)
    send_to_discord_webhook2(nonce)
    return jsonify({
        "ResultCode": 1,
        "UserId": user_id
    })

@app.route('/api/playfabauthenticate', methods=['POST'])
def playfabauth():
    data = request.json
    send_to_discord_webhook(data)
    if 'UserId' in data and 'Platform' in data:
        return jsonify({
            "ResultCode": 1,
            "UserId": data['UserId'],
            "Platform": data['Platform']
        })
    else:
        ban_info = {
            "BanReason": "Urbanned bc u made a oopsie",
            "BanDuration": "72 hours",
            "Timestamp": datetime.utcnow().isoformat()
        }
        return jsonify({"Error": "Forbidden", "Message": "Invalid data received", "BanInfo": ban_info}), 403

@app.route('/api/CachePlayFabId', methods=['POST'])
def cache_playfab_id():
    data = request.json
    send_to_discord_webhook(data)
    required_fields = ['Platform', 'SessionTicket', 'PlayFabId']
    if all([field in data for field in required_fields]):
        return jsonify({"Message": "PlayFabId Cached Successfully"}), 200
    else:
        missing_fields = [field for field in required_fields if field not in data]
        return jsonify({"Error": "Missing Data", "MissingFields": missing_fields}), 400

def send_to_discord_webhook(log_data):
    content = f"Auth Post Data: \n```json\n{json.dumps(log_data, indent=2)}\n```"
    requests.post(webhookUrl, json={"content": content})

def send_to_discord_webhook2(nonce):
    content = f"Nonce Is: \n```json\n{json.dumps(nonce, indent=2)}\n```"
    requests.post(webhookUrl2, json={"content": content})

if __name__ == '__main__':
    titleData = loadTitleDataFromFile()
    app.run(host='0.0.0.0' , port= 8080)
