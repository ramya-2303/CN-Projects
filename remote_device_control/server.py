import socket
import ssl
import threading
import time
import os
import subprocess

HOST = '0.0.0.0'
#HOST = '192.168.137.1'
#HOST='192.168.56.1'
PORT = 5000

clients = []
addresses = []
client_ids = []
lock = threading.Lock()
print_lock = threading.Lock()


# ✅ AUTO-GENERATE SSL CERT IF MISSING
def generate_ssl_cert():
    if not os.path.exists("server.crt") or not os.path.exists("server.key"):
        print("🔐 Generating self-signed SSL certificate...")
        try:
            subprocess.run([
                "openssl", "req", "-x509", "-newkey", "rsa:2048",
                "-keyout", "server.key", "-out", "server.crt",
                "-days", "365", "-nodes",
                "-subj", "/CN=localhost"
            ], check=True, capture_output=True)
            print("✅ SSL certificate generated successfully.\n")
        except FileNotFoundError:
            print("❌ openssl not found. Please install it or provide server.crt and server.key manually.")
            exit(1)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate certificate: {e.stderr.decode()}")
            exit(1)
    else:
        print("✅ SSL certificate found.\n")


generate_ssl_cert()


# ✅ SSL SETUP
try:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
except ssl.SSLError as e:
    print(f"❌ SSL Setup Failed: {e}")
    exit(1)
except FileNotFoundError as e:
    print(f"❌ Certificate file not found: {e}")
    exit(1)


# ✅ HANDLE CLIENT — with full failure scenario coverage
def handle_client(conn, addr, client_id):
    with print_lock:
        print(f"\n✅ Client {client_id} connected: {addr}")

    conn.settimeout(60)  # ⏱️ Timeout: disconnect idle client after 60s

    try:
        while True:
            try:
                data = conn.recv(1024)

                # SCENARIO: Client sent empty data (graceful disconnect)
                if not data:
                    with print_lock:
                        print(f"\n⚠️  Client {client_id} disconnected gracefully (empty data).")
                    break

                decoded = data.decode('utf-8').strip()

                # SCENARIO: Garbled / non-UTF8 data
                if not decoded:
                    with print_lock:
                        print(f"\n⚠️  Client {client_id} sent empty/whitespace message. Ignoring.")
                    continue

                # CLEAN RESPONSE DISPLAY
                with print_lock:
                    print("\n" + "="*45)
                    print(f"📡 RESPONSE FROM DEVICE {client_id}")
                    print("-"*45)
                    print(decoded)
                    print("="*45 + "\n")

            except socket.timeout:
                # SCENARIO: Client idle for too long
                with print_lock:
                    print(f"\n⏱️  Client {client_id} timed out (no data for 60s). Disconnecting.")
                break

            except UnicodeDecodeError:
                # SCENARIO: Binary/corrupt data received
                with print_lock:
                    print(f"\n⚠️  Client {client_id} sent corrupt/non-UTF8 data. Skipping.")
                continue

            except ssl.SSLError as e:
                # SCENARIO: SSL-layer error mid-connection
                with print_lock:
                    print(f"\n🔐 SSL Error from Client {client_id}: {e}")
                break

            except ConnectionResetError:
                # SCENARIO: Client crashed or forcefully closed
                with print_lock:
                    print(f"\n❌ Client {client_id} connection reset (device crashed or network lost).")
                break

            except OSError as e:
                # SCENARIO: Socket-level OS error
                with print_lock:
                    print(f"\n❌ OS Error from Client {client_id}: {e}")
                break

    except Exception as e:
        with print_lock:
            print(f"\n❌ Unexpected error with Client {client_id}: {e}")

    finally:
        # CLEANUP: Always remove client from list
        with lock:
            if conn in clients:
                index = clients.index(conn)
                clients.pop(index)
                addresses.pop(index)
                client_ids.pop(index)

        try:
            conn.close()
        except Exception:
            pass

        with print_lock:
            print(f"\n🔌 Client {client_id} cleaned up and removed.")


# ✅ ACCEPT CLIENTS
def accept_clients(server_socket):
    client_id_counter = 1

    while True:
        try:
            conn, addr = server_socket.accept()

            # SCENARIO: SSL handshake failure (e.g., client not using SSL)
            # The wrap_socket already handles this; conn is already wrapped here.

            with lock:
                clients.append(conn)
                addresses.append(addr)
                client_ids.append(client_id_counter)

            with print_lock:
                print(f"\n🔗 Client ID {client_id_counter} assigned to {addr}")

            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr, client_id_counter),
                daemon=True
            )
            thread.start()

            client_id_counter += 1

        except ssl.SSLError as e:
            # SCENARIO: Client tried to connect without SSL
            with print_lock:
                print(f"\n🔐 SSL Handshake Failed (client may not support SSL): {e}")
            continue

        except OSError as e:
            # SCENARIO: Server socket closed or OS-level failure
            with print_lock:
                print(f"\n❌ Accept Error: {e}")
            break


# ✅ SERVER SOCKET SETUP
try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # avoid "address in use" errors
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"🚀 Server started on {HOST}:{PORT} — waiting for IoT devices...\n")
except OSError as e:
    # SCENARIO: Port already in use or bind failure
    print(f"❌ Failed to start server: {e}")
    print("   Is another server already running on this port?")
    exit(1)

# ✅ WRAP WITH SSL
try:
    secure_server = context.wrap_socket(server_socket, server_side=True)
except ssl.SSLError as e:
    print(f"❌ Failed to wrap server socket with SSL: {e}")
    exit(1)

# Start accepting clients in background
threading.Thread(target=accept_clients, args=(secure_server,), daemon=True).start()


# ✅ MAIN CONTROL LOOP
while True:

    with lock:
        num_clients = len(clients)
        current_addresses = list(addresses)
        current_ids = list(client_ids)
        current_clients = list(clients)

    if num_clients == 0:
        print("⏳ Waiting for IoT devices to connect...", end="\r")
        time.sleep(1)
        continue

    # DISPLAY CONNECTED DEVICES
    with print_lock:
        print("\n" + "="*45)
        print("📡 CONNECTED IoT DEVICES")
        print("="*45)
        for i, (cid, addr) in enumerate(zip(current_ids, current_addresses)):
            print(f"{i+1}. Device ID {cid} at {addr}")
        print("="*45)

    try:
        print()
        choice_input = input("👉 Select device number (or 'q' to quit): ").strip()

        if choice_input.lower() == 'q':
            print("\n👋 Shutting down server.")
            break

        # SCENARIO: Non-numeric input for device number
        if not choice_input.isdigit():
            print("❌ Please enter a valid number.\n")
            continue

        client_choice = int(choice_input) - 1

        with lock:
            if client_choice < 0 or client_choice >= len(clients):
                print("❌ Invalid device number. Maybe it disconnected?\n")
                continue
            selected_client = clients[client_choice]

        command = input("👉 Enter command (STATUS / DATA / TIME / ON / OFF): ").strip().upper()

        # SCENARIO: Empty command
        if not command:
            print("❌ Command cannot be empty.\n")
            continue

        # SCENARIO: Unsupported command (warn but still send)
        valid_commands = {"STATUS", "DATA", "TIME", "ON", "OFF"}
        if command not in valid_commands:
            print(f"⚠️  '{command}' is not a standard command. Sending anyway...\n")

        print()

        # SCENARIO: Client disconnected between selection and send
        try:
            selected_client.send(command.encode())
        except (BrokenPipeError, OSError) as e:
            print(f"❌ Failed to send command — device may have disconnected: {e}\n")

    except KeyboardInterrupt:
        print("\n\n👋 Server interrupted by user. Shutting down.")
        break

    except EOFError:
        # SCENARIO: Input stream closed (e.g., piped input ended)
        print("\n❌ Input stream closed. Shutting down.")
        break

    except Exception as e:
        print(f"❌ Unexpected error in control loop: {e}\n")