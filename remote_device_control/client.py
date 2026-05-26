import socket
import ssl
import random
import time

#HOST = '192.168.137.1'
HOST='192.168.56.1'
PORT = 5000
RECONNECT_ATTEMPTS = 3       # how many times to retry on connection failure
RECONNECT_DELAY = 3          # seconds between retries


# ✅ DEVICE SETUP
device_name = input("Enter Device (TEMP / LIGHT / MOTION): ").strip().upper()

# SCENARIO: Invalid device type entered
valid_devices = {"TEMP", "LIGHT", "MOTION"}
if device_name not in valid_devices:
    print(f"❌ Unknown device '{device_name}'. Defaulting to TEMP.")
    device_name = "TEMP"

if device_name == "TEMP":
    components = ["Temp Sensor", "Humidity Sensor", "Clock Module"]

elif device_name == "LIGHT":
    components = ["LED", "LDR Sensor", "Clock Module"]
    light_status = "OFF"

elif device_name == "MOTION":
    components = ["PIR Sensor", "Buzzer", "Clock Module"]

print("\n" + "="*40)
print(f"🔌 Device: {device_name}")
print("Components:")
for c in components:
    print(f"  • {c}")
print("="*40 + "\n")


# ✅ SSL CONTEXT
try:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE   # self-signed cert, so skip verification
except ssl.SSLError as e:
    print(f"❌ Failed to create SSL context: {e}")
    exit(1)


# ✅ CONNECTION WITH RETRY LOGIC
def connect_to_server():
    for attempt in range(1, RECONNECT_ATTEMPTS + 1):
        try:
            print(f"🔄 Connecting to server (Attempt {attempt}/{RECONNECT_ATTEMPTS})...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)   # ⏱️ connection timeout

            secure_socket = context.wrap_socket(sock, server_hostname=HOST)
            secure_socket.connect((HOST, PORT))

            secure_socket.settimeout(None)   # reset to blocking after connect
            print("✅ Connected to server securely (SSL).\n")
            return secure_socket

        except ssl.SSLError as e:
            # SCENARIO: SSL handshake failed
            print(f"🔐 SSL Error on attempt {attempt}: {e}")

        except ConnectionRefusedError:
            # SCENARIO: Server not running
            print(f"❌ Connection refused on attempt {attempt} — is the server running?")

        except socket.timeout:
            # SCENARIO: Server unreachable / too slow
            print(f"⏱️  Connection timed out on attempt {attempt}.")

        except OSError as e:
            # SCENARIO: Network interface issue
            print(f"❌ OS/Network Error on attempt {attempt}: {e}")

        if attempt < RECONNECT_ATTEMPTS:
            print(f"   Retrying in {RECONNECT_DELAY}s...\n")
            time.sleep(RECONNECT_DELAY)

    print("❌ Could not connect to server after all attempts. Exiting.")
    exit(1)


secure_socket = connect_to_server()


# ✅ GENERATE RESPONSE FOR COMMAND
def generate_response(command):
    global light_status

    # ✅ STATUS
    if command == "STATUS":
        if device_name == "LIGHT":
            return f"Device: LIGHT | Status: {light_status}"
        return f"Device: {device_name} | Status: ACTIVE"

    # ✅ TIME
    elif command == "TIME":
        return f"Time: {time.ctime()}"

    # ✅ DATA
    elif command == "DATA":
        if device_name == "TEMP":
            temp = random.randint(20, 35)
            humidity = random.randint(40, 70)
            return (
                f"🌡️ Temp Device\n"
                f"Temp: {temp}°C\n"
                f"Humidity: {humidity}%"
            )
        elif device_name == "LIGHT":
            brightness = random.randint(0, 100)
            return (
                f"💡 Light Device\n"
                f"Status: {light_status}\n"
                f"Brightness: {brightness}%"
            )
        elif device_name == "MOTION":
            motion = random.choice(["Detected", "No Motion"])
            buzzer = "ON" if motion == "Detected" else "OFF"
            return (
                f"🚶 Motion Device\n"
                f"Motion: {motion}\n"
                f"Buzzer: {buzzer}"
            )

    # ✅ LIGHT CONTROL
    elif command in ("ON", "OFF"):
        if device_name == "LIGHT":
            light_status = command
            return f"Light turned {command}"
        else:
            # SCENARIO: ON/OFF sent to non-light device
            return f"⚠️ {device_name} does not support ON/OFF commands."

    # SCENARIO: Unknown command from server
    else:
        return f"⚠️ Unknown command received: '{command}'"


# ✅ MAIN RECEIVE LOOP — with full failure coverage
while True:
    try:
        data = secure_socket.recv(1024)

        # SCENARIO: Server closed the connection
        if not data:
            print("\n⚠️  Server closed the connection.")
            break

        try:
            command = data.decode('utf-8').strip()
        except UnicodeDecodeError:
            # SCENARIO: Corrupt/garbled command received
            print("⚠️  Received corrupt data from server. Ignoring.")
            continue

        if not command:
            # SCENARIO: Empty command (whitespace only)
            print("⚠️  Received empty command. Ignoring.")
            continue

        print(f"📨 Command received: {command}")

        response = generate_response(command)

        try:
            secure_socket.send(f"[{device_name}]\n{response}".encode('utf-8'))
        except BrokenPipeError:
            # SCENARIO: Server went down between recv and send
            print("❌ Lost connection while sending response (server may have crashed).")
            break
        except OSError as e:
            # SCENARIO: General send failure
            print(f"❌ Send error: {e}")
            break

    except socket.timeout:
        # SCENARIO: Server stopped sending commands (idle timeout)
        print("⏱️  No command received for a while. Still waiting...")
        continue

    except ssl.SSLError as e:
        # SCENARIO: SSL session disrupted mid-connection
        print(f"🔐 SSL Error during communication: {e}")
        break

    except ConnectionResetError:
        # SCENARIO: Server forcefully closed the connection
        print("❌ Connection reset by server (server may have crashed or restarted).")
        break

    except OSError as e:
        # SCENARIO: Network failure, cable unplugged, etc.
        print(f"❌ Network error: {e}")
        break

    except KeyboardInterrupt:
        # SCENARIO: User manually exits the client
        print("\n\n👋 Client shutting down by user request.")
        break

# ✅ CLEANUP
try:
    secure_socket.close()
    print("🔌 Connection closed cleanly.")
except Exception:
    pass