import socket
import ssl
import threading

HOST = '127.0.0.1'
PORT = 5000

clients = []
addresses = []
lock = threading.Lock()

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="server.crt", keyfile="server.key")


def handle_client(conn, addr, client_id):
    print(f"Client {client_id} connected: {addr}")

    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            print(f"[Client {client_id}] Response: {data}")

    except:
        pass

    print(f"Client {client_id} disconnected")

    with lock:
        if conn in clients:
            index = clients.index(conn)
            clients.pop(index)
            addresses.pop(index)

    conn.close()


def accept_clients(server_socket):
    client_id = 1

    while True:
        conn, addr = server_socket.accept()

        with lock:
            clients.append(conn)
            addresses.append(addr)

        print(f"Client ID {client_id} assigned")

        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr, client_id),
            daemon=True
        )
        thread.start()

        client_id += 1


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print("Server started... waiting for clients")

secure_server = context.wrap_socket(server_socket, server_side=True)

threading.Thread(
    target=accept_clients,
    args=(secure_server,),
    daemon=True
).start()


while True:

    if len(clients) == 0:
        # Just wait silently
        continue

    print("\nConnected Clients:")

    with lock:
        for i, addr in enumerate(addresses):
            print(f"{i+1} : {addr}")

    try:
        client_choice = int(input("Select client number: ")) - 1

        with lock:
            if client_choice < 0 or client_choice >= len(clients):
                print("Invalid client number")
                continue

            command = input("Enter command (STATUS / TEMP / TIME): ")

            clients[client_choice].send(command.encode())

    except Exception as e:
        print("Error:", e)