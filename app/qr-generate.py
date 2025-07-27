import json
import base64
import qrcode


data = {
    "username": "testgpo",
    "password": base64.b64encode("Qaz321wsx".encode()).decode()
}

qr = qrcode.make(json.dumps(data))
qr.save("rdp_credentials.png")