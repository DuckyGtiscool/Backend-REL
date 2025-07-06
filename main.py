import requests
import random
from flask import Flask, jsonify, request
import json

class GameInfo:
    def __init__(self):
        self.TitleId = "1842E6"
        self.SecretKey = "HIJIJJPYTNIDAN5WHGJ1X31N9TDB5FYJUSPDO1GGQY7Y188ZM3"
        self.ApiKey = "OC|8707181616048405|823579981c24a6e82dae72e9ee80fa63"

    def get_auth_headers(self):
        return {"content-type": "application/json", "X-SecretKey": self.SecretKey}

settings = GameInfo()
app = Flask(__name__)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1386840602154631279/u1I0qJuVXI1L4DnweCOvKHs41ctgHAQvA_zAgZVbFhyuLUIPKtaMfuAwj2Iw928AEG11"

@app.route("/", methods=["POST", "GET"])
def main():
    return """
        <html>
            <head>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
            </head>
            <body style="font-family: 'Inter', sans-serif;">
                <h1 style="color: red; font-size: 30px;">
                    get off my backends (Made By Tozic (Creds to BT) )
                </h1>
            </body>
        </html>
    """

@app.route("/api/photon", methods=["POST"])
def photonauth():
    print(f"Received {request.method} request at /api/photon")
    getjson = request.get_json()
    ticket = getjson.get("Ticket")
    nonce = getjson.get("Nonce")
    platform = getjson.get("Platform")
    user_id = ticket.split('-')[0] if ticket else None
    username = getjson.get("username")

    if not user_id or len(user_id) != 16:
        return jsonify({
            'resultCode': 2,
            'message': 'Invalid token',
            'userId': None,
            'nickname': None
        })

    req = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo",
        json={"PlayFabId": user_id},
        headers=settings.get_auth_headers()
    )

    print(f"Request to PlayFab returned status code: {req.status_code}")

    if req.status_code == 200:
        nickname = req.json().get("data", {}).get("UserInfo", {}).get("Username") or "Unknown"

        # ✅ Send Discord webhook
        webhook_payload = {
            "embeds": [{
                "title": "✅ Player Authenticated",
                "description": f"**UserId:** `{user_id}`\n**Username:** `{username or nickname}`\n**Platform:** `{platform}`",
                "color": 65280
            }]
        }

        try:
            webhook_response = requests.post(DISCORD_WEBHOOK_URL, json=webhook_payload)
            print(f"Webhook sent: {webhook_response.status_code}")
        except Exception as e:
            print(f"Failed to send Discord webhook: {e}")

        return jsonify({
            'resultCode': 1,
            'message': f'Authenticated user {user_id.lower()} title {settings.TitleId.lower()}',
            'userId': user_id.upper(),
            'nickname': nickname
        })

    else:
        return jsonify({
            'resultCode': 0,
            'message': "Something went wrong",
            'userId': None,
            'nickname': None
        })

@app.route("/api/PlayFabAuthentication", methods=["POST"])
def playfab_authentication():
    rjson = request.get_json()
    required_fields = ["Nonce", "AppId", "Platform", "OculusId"]
    missing_fields = [field for field in required_fields if not rjson.get(field)]

    if missing_fields:
        return (
            jsonify(
                {
                    "Message": f"Missing parameter(s): {', '.join(missing_fields)}",
                    "Error": f"BadRequest-No{missing_fields[0]}",
                }
            ),
            401,
        )

    if rjson.get("AppId") != settings.TitleId:
        return (
            jsonify(
                {
                    "Message": "Request sent for the wrong App ID",
                    "Error": "BadRequest-AppIdMismatch",
                }
            ),
            400,
        )

    url = f"https://{settings.TitleId}.playfabapi.com/Server/LoginWithServerCustomId"
    login_request = requests.post(
        url=url,
        json={
            "ServerCustomId": "OCULUS" + rjson.get("OculusId"),
            "CreateAccount": True,
        },
        headers=settings.get_auth_headers(),
    )

    if login_request.status_code == 200:
        data = login_request.json().get("data")
        session_ticket = data.get("SessionTicket")
        entity_token = data.get("EntityToken").get("EntityToken")
        playfab_id = data.get("PlayFabId")
        entity_type = data.get("EntityToken").get("Entity").get("Type")
        entity_id = data.get("EntityToken").get("Entity").get("Id")

        link_response = requests.post(
            url=f"https://{settings.TitleId}.playfabapi.com/Server/LinkServerCustomId",
            json={
                "ForceLink": True,
                "PlayFabId": playfab_id,
                "ServerCustomId": rjson.get("CustomId"),
            },
            headers=settings.get_auth_headers(),
        ).json()

        return (
            jsonify(
                {
                    "PlayFabId": playfab_id,
                    "SessionTicket": session_ticket,
                    "EntityToken": entity_token,
                    "EntityId": entity_id,
                    "EntityType": entity_type,
                }
            ),
            200,
        )
    else:
        if login_request.status_code == 403:
            ban_info = login_request.json()
            if ban_info.get("errorCode") == 1002:
                ban_message = ban_info.get("errorMessage", "No ban message provided.")
                ban_details = ban_info.get("errorDetails", {})
                ban_expiration_key = next(iter(ban_details.keys()), None)
                ban_expiration = (
                    ban_details.get(ban_expiration_key, ["No expiration date"])[0]
                    if ban_expiration_key
                    else "No expiration date provided."
                )
                return (
                    jsonify(
                        {
                            "BanMessage": ban_expiration_key,
                            "BanExpirationTime": ban_expiration,
                        }
                    ),
                    403,
                )
            else:
                error_message = ban_info.get("errorMessage", "Forbidden.")
                return (
                    jsonify({"Error": "PlayFab Error", "Message": error_message}),
                    403,
                )
        else:
            return (
                jsonify({
                    "Error": "PlayFab Error",
                    "Message": login_request.json().get("errorMessage", "Unknown error.")
                }),
                login_request.status_code
            )

@app.route("/api/CachePlayFabId", methods=["POST"])
def cache_playfab_id():
    return jsonify({"Message": "Success"}), 200

@app.route("/api/TitleData", methods=["POST", "GET"])
def title_data():
    response = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/GetTitleData",
        headers=settings.get_auth_headers()
    )
    if response.status_code == 200:
        return jsonify(response.json().get("data", {}).get("Data"))
    else:
        return jsonify({}), response.status_code

@app.route("/api/ConsumeOculusIAP", methods=["POST"])
def consume_oculus_iap():
    rjson = request.get_json()
    access_token = rjson.get("userToken")
    user_id = rjson.get("userID")
    nonce = rjson.get("nonce")
    sku = rjson.get("sku")

    response = requests.post(
        url=f"https://graph.oculus.com/consume_entitlement?nonce={nonce}&user_id={user_id}&sku={sku}&access_token={settings.ApiKey}",
        headers={"content-type": "application/json"},
    )

    if response.json().get("success"):
        return jsonify({"result": True})
    else:
        return jsonify({"error": True})

@app.route("/api/GetAcceptedAgreements", methods=['POST', 'GET'])
def GetAcceptedAgreements():
    return jsonify({"PrivacyPolicy": "1.1.28", "TOS": "11.05.22.2"}), 200

@app.route("/api/SubmitAcceptedAgreements", methods=['POST', 'GET'])
def SubmitAcceptedAgreements():
    return jsonify({}), 200

@app.route("/api/ConsumeCodeItem", methods=["POST"])
def consume_code_item():
    rjson = request.get_json()
    code = rjson.get("itemGUID")
    playfab_id = rjson.get("playFabID")
    session_ticket = rjson.get("playFabSessionTicket")

    if not all([code, playfab_id, session_ticket]):
        return jsonify({"error": "Missing parameters"}), 400

    raw_url = "https://github.com/redapplegtag/backendsfrr"
    response = requests.get(raw_url)

    if response.status_code != 200:
        return jsonify({"error": "GitHub fetch failed"}), 500

    lines = response.text.splitlines()
    codes = {line.split(":")[0]: line.split(":")[1] for line in lines if ":" in line}

    if code not in codes:
        return jsonify({"result": "CodeInvalid"}), 404

    if codes[code] == "AlreadyRedeemed":
        return jsonify({"result": codes[code]}), 200

    grant_response = requests.post(
        f"https://{settings.TitleId}.playfabapi.com/Admin/GrantItemsToUsers",
        json={
            "ItemGrants": [{
                "PlayFabId": playfab_id,
                "ItemId": item_id,
                "CatalogVersion": "DLC"
            } for item_id in ["dis da cosmetics", "anotehr cposmetic", "anotehr"]]
        },
        headers=settings.get_auth_headers()
    )

    if grant_response.status_code != 200:
        return jsonify({"result": "PlayFabError", "errorMessage": grant_response.json().get("errorMessage", "Grant failed")}), 500

    return jsonify({"result": "Success", "itemID": code, "playFabItemName": codes[code]}), 200

@app.route('/api/v2/GetName', methods=['POST', 'GET'])
def GetNameIg():
    return jsonify({"result": f"GORILLA{random.randint(1000, 9999)}"})
