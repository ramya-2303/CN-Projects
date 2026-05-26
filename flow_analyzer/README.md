# SDN Flow Analyzer

A Software Defined Networking (SDN) mini project using the POX controller to monitor OpenFlow switch flow statistics.

## Features

- Detects OpenFlow switch connections
- Requests flow statistics from switches
- Identifies active and unused flow rules
- Displays packet count information
- Uses POX controller framework

## Technologies Used

- Python
- POX Controller
- OpenFlow Protocol
- WSL (Windows Subsystem for Linux)

## Project Structure

```text
flow_analyzer
 ├── flow_analyzer.py
 ├── README.md
 └── output.png
```

## How It Works

- The POX controller listens for switch connections.
- Once connected, it requests flow statistics.
- Flow entries are analyzed using packet counts.
- Rules are classified as:
  - ACTIVE
  - UNUSED

## Requirements

- Ubuntu/WSL
- Python 3
- POX Controller
- OpenFlow-enabled switch or Mininet

## How to Run

### Step 1: Open WSL Terminal

```bash
cd ~/pox
```

### Step 2: Run POX Controller

```bash
./pox.py log.level --DEBUG flow_analyzer
```

### Step 3: Start Mininet

Open another terminal and run:

```bash
sudo mn --topo single,3 --controller remote
```

## Sample Output

![Output](output.png)
