import json
import base64
import qrcode

print("For generate QR-code input username and password")
username = input("Input username:")
password = input("Input password:")
data = {
    "username": username,
    "password": password
}

data_code = base64.b64encode(json.dumps(data).encode("utf-8")).decode()

qr = qrcode.make(json.dumps(data_code))
qr.save(f"{username}+rdp_credentials.png")

print("Generate QR-code Finish! File create!")