Create app/conf.ini file with the following structure:

[RDP_Settings]
RDP_SERVER = """ip adress or name server"""
RDP_PORT = """server port"""
DOMAIN = """DOMAIN name"""
WIDTH = 
HEIGHT = 

Add to app/ logo file, logo.png and icon file icon.ico

For generate qr-code use qr-generate script

Depends for Ubuntu install:
python3 python3-tk python3-pil python3-opencv freerdp2-x11 python3-pyzbar python3-pil.imagetk