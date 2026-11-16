import socket

HOST = "192.168.0.174"
PORT = 5025

try:
    s = socket.create_connection((HOST, PORT), timeout=5)

    s.sendall(b"*IDN?\n")

    response = s.recv(1024)

    print("Instrument response:", response.decode())

    s.close()

except Exception as e:
    print("Connection failed:", e)
