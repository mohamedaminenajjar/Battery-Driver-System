from threading import Thread, Event
import socket
import logging
import battery_driver
import queue

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GatewayConfig:
    def __init__(self, ip, port, can_port_number, baudrate):
        self.ip = ip
        self.port = port
        self.can_port_number = can_port_number
        self.baudrate = baudrate
        self.response_msg_size = 1024

    def configure_gateway(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # Set a timeout for the connection attempt
            logging.info("Attempting to connect to the gateway...")
            sock.connect((self.ip, self.port))
            
            logging.info(f"Connected to {self.ip}:{self.port}")

            self.send_command(sock, f"CAN {self.can_port_number} STOP\r\n")
            self.send_command(sock, f"CAN {self.can_port_number} INIT STD {self.baudrate}\n")
            self.send_command(sock, f"CAN {self.can_port_number} FILTER ADD EXT 0x000 0x000\n")
            self.send_command(sock, f"CAN {self.can_port_number} START\n")
            logging.info("Gateway configured successfully.")

            self.send_command(sock, f"CAN {self.can_port_number} STATUS\n")
            logging.info("Checked CAN port status.")

            return sock

        except (socket.error, socket.timeout) as e:
            logging.error(f"Failed to connect or send command to gateway: {e}")
            return None

    def send_command(self, sock, command):
        try:
            sock.send(command.encode('ascii'))
            response = sock.recv(self.response_msg_size).decode('ascii')
            logging.info(f"Sent: {command.strip()}")
            logging.info(f"Received: {response.strip()}")
            return response
        except (socket.error, socket.timeout) as e:
            logging.error(f"Failed to send command: {e}")
            return None

class MessageParser:
    def __init__(self, raw_message):
        self.raw_message = raw_message
        self.port = None
        self.message_format = None
        self.identifier = None
        self.data_bytes = None
        self.dlc = None
        self.parse_message()

    def parse_message(self):
        try:
            # Split the raw message by spaces
            parts = self.raw_message.split()

            # Ensure the message starts with 'M'
            if parts[0] != 'M':
                raise ValueError(f"Invalid message start: {parts[0]}")

            # Extract the fields
            self.port = int(parts[1])
            self.message_format = parts[2]
            self.identifier = int(parts[3], 16)  # Convert the identifier from hex to int

            # If there are data bytes, they should be separated by spaces and dlc should be after '|'
            if len(parts) > 4:
                data_and_dlc = ' '.join(parts[4:]).split('|')
                self.data_bytes = data_and_dlc[0].strip()
                if len(data_and_dlc) > 1:
                    self.dlc = int(data_and_dlc[1].replace("dlc=", "").strip())
                else:
                    self.dlc = len(self.data_bytes.split())  # If no dlc provided, infer from data bytes length
            else:
                self.data_bytes = ""
                self.dlc = 0

        except ValueError as e:
            logging.error(f"Failed to parse message: {e}")
            raise

    def __repr__(self):
        return (f"MessageParser(port={self.port}, format={self.message_format}, "
                f"identifier={self.identifier}, data_bytes={self.data_bytes}, dlc={self.dlc})")

def receive_messages(sock, message_queue, stop_event):
    try:
        while not stop_event.is_set():
            response = sock.recv(1024).decode('ascii')
            if response:
                logging.info(f"Received raw message: {response.strip()}")
                message_queue.put(response.strip())
    except (socket.error, socket.timeout) as e:
        logging.error(f"Error receiving data from gateway: {e}")
    finally:
        sock.close()
        logging.info("Connection closed")

def process_messages(message_queue, start_driver_event):
    while not start_driver_event.is_set() or not message_queue.empty():
        try:
            raw_message = message_queue.get(timeout=1)  # Adjust timeout as needed
            parser = MessageParser(raw_message)
            logging.info(f"Parsed message: {parser}")

            if parser.identifier in {0x12C21020, 0x12C21021, 0x12C21022}:
                start_driver_event.set()  # Signal to start the battery driver

        except queue.Empty:
            continue  # Continue looping if the queue is empty

if __name__ == "__main__":
    stop_event = Event()
    start_driver_event = Event()
    message_queue = queue.Queue()

    gateway = GatewayConfig('192.168.1.20', 19228, 1, 250)
    sock = gateway.configure_gateway()

    if sock is None:
        logging.error("Failed to configure the gateway.")
    else:
        receiver_thread = Thread(target=receive_messages, args=(sock, message_queue, stop_event))
        processor_thread = Thread(target=process_messages, args=(message_queue, start_driver_event))

        receiver_thread.start()
        processor_thread.start()

        logging.info("Waiting for a valid battery message...")
        start_driver_event.wait()  # Wait for the event to start the battery driver

        battery_driver_thread = Thread(target=battery_driver.battery_driver, args=(message_queue,))
        battery_driver_thread.start()

        # Join threads to wait for their completion
        receiver_thread.join()
        processor_thread.join()
        battery_driver_thread.join()

        stop_event.set()  # Ensure the stop event is set if needed
