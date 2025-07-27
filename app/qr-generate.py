import json
import base64
import qrcode


data = {
    "username": "",
    "password": base64.b64encode("".encode()).decode()
}

qr = qrcode.make(json.dumps(data))
qr.save("rdp_credentials.png")