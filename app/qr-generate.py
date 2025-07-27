import json
import base64
import qrcode

print("For generate QR-code input username and password")
username = input("Input username:")
password = input("Input password:")
data = {
    "username": username,
    "password": base64.b64encode(password.encode()).decode()
}

qr = qrcode.make(json.dumps(data))
qr.save("rdp_credentials.png")

print("Generate QR-code Finish! File create!")