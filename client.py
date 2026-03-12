import socket
import ssl
import random
import time

HOST = '127.0.0.1'
PORT = 5000

context = ssl.create_default_context()

context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

secure_socket = context.wrap_socket(client_socket, server_hostname=HOST)

secure_socket.connect((HOST, PORT))

print("Connected to server")

while True:

    command = secure_socket.recv(1024).decode()

    if not command:
        break

    print("Command received:", command)

    if command == "STATUS":
        response = "Device running"

    elif command == "TEMP":
        response = f"Temperature: {random.randint(20,35)} C"

    elif command == "TIME":
        response = time.ctime()

    else:
        response = "Unknown command"

    secure_socket.send(response.encode())

secure_socket.close()