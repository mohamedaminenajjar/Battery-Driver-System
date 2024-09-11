import logging
import queue

from interface import MessageParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BatteryDataProcessor:
    def __init__(self):
        self.data_fields = {
            0x12C21020: self.process_message_0x12C21020,
            0x12C21021: self.process_message_0x12C21021,
            0x12C21022: self.process_message_0x12C21022,
        }

    def process_message(self, message_id, data):
        if message_id in self.data_fields:
            return self.data_fields[message_id](data)
        else:
            logging.warning(f"Unknown message ID: {message_id}")
            return None

    def process_message_0x12C21020(self, data):
        raw_data = bytes.fromhex(data)
        voltage = int.from_bytes(raw_data[0:2], byteorder='big') * 1.0
        current = int.from_bytes(raw_data[2:4], byteorder='big', signed=True) * 0.01
        soc = int.from_bytes(raw_data[4:6], byteorder='big') * 0.01
        soh = int.from_bytes(raw_data[6:8], byteorder='big') * 0.01

        return {
            'voltage': voltage,
            'current': current,
            'state_of_charge': soc,
            'state_of_health': soh
        }

    def process_message_0x12C21021(self, data):
        raw_data = bytes.fromhex(data)

        # Extracting the status byte
        status_byte = raw_data[0]

        # Extracting the power contactor status
        power_contactor_status = (status_byte & 0b00000010) >> 1
        power_contactor_status = 'closed' if power_contactor_status == 1 else 'open'

        byte_for_end_of_charge = raw_data[1]
        byte_for_heater_status = raw_data[1]

        end_of_charge = (byte_for_end_of_charge & 0b00000010) >> 1
        end_of_charge = 'end of charge (Battery full)' if end_of_charge == 1 else 'not end of charge'

        heater_status = (byte_for_heater_status & 0b00000100) >> 2
        heater_status = 'active' if heater_status == 1 else 'not active'

        bms_board_temp = raw_data[5] - 40
        battery_bank_1_temp = raw_data[6] - 40
        battery_bank_2_temp = raw_data[7] - 40

        return {
            'power_contactor_status': power_contactor_status,
            'end_of_charge': end_of_charge,
            'heater_status': heater_status,
            'bms_board_temp': bms_board_temp,
            'battery_bank_1_temp': battery_bank_1_temp,
            'battery_bank_2_temp': battery_bank_2_temp
        }

    #def process_message_0x12C21022(self, data):
    #    raw_data = bytes.fromhex(data)
    #    voltage = int.from_bytes(raw_data[0:2], byteorder='big') * 1.0
    #    current = int.from_bytes(raw_data[2:4], byteorder='big', signed=True) * 0.01
    #    soc = int.from_bytes(raw_data[4:6], byteorder='big') * 0.01
    #    soh = int.from_bytes(raw_data[6:8], byteorder='big') * 0.01
#
    #    return {
    #        'voltage': voltage,
    #        'current': current,
    #        'state_of_charge': soc,
    #        'state_of_health': soh
    #    }

def battery_driver(queue):
    processor = BatteryDataProcessor()
    
    while True:
        try:
            raw_message = queue.get(timeout=5)  # Adjust timeout as needed
            parser = MessageParser(raw_message)  # Create a MessageParser instance to parse the raw message
            logging.info(f"Received message for processing: {parser}")

            if parser.message_id in {0x12C21020, 0x12C21021, 0x12C21022}:
                result = processor.process_message(parser.message_id, parser.message_data)
                if result:
                    logging.info(f"Processed data: {result}")
                else:
                    logging.warning(f"Failed to process message with ID: {parser.message_id}")

        except queue.Empty:
            logging.debug("Queue is empty, waiting for more messages.")
        except Exception as e:
            logging.error(f"Error in battery_driver: {e}")
