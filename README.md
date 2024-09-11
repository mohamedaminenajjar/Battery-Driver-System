# 🔋 Battery Gateway Communication Driver for PGuard Robot

## 🌟 General Description
This project implements a communication driver between a battery and a gateway in the PGuard robot. The system enables the reception of CAN protocol data from the battery, processes and parses the received data, and then transmits it via a socket interface for further use. This setup ensures efficient and real-time monitoring of battery status, including voltage, current, and state of charge.

## 📁 Project Structure
The project consists of two main components:

1. 🔌 *CAN Data Reception*  
   The gateway receives data from the battery using the CAN protocol and processes various messages to extract meaningful battery metrics.

2. 🌐 *Socket Data Transmission*  
   Parsed data from the CAN messages is transmitted via a socket to external systems for further processing and analysis.

## 📂 Code Files

### battery_driver.py
This file contains the BatteryDataProcessor class, responsible for handling CAN messages and extracting data such as voltage, current, state of charge (SOC), state of health (SOH), and temperature readings.

Key functions include:

- process_message_0x12C21020: Parses data related to battery voltage, current, SOC, and SOH.
- process_message_0x12C21021: Handles status information such as power contactor status and temperature.
- battery_driver: Main function to continuously process messages from the CAN bus.

### interface.py
This file handles the configuration and communication between the gateway and the battery. It also sets up the socket connection for transmitting parsed data.

Key functions include:

- GatewayConfig: Configures the gateway for CAN communication, setting up CAN filters and initializing the connection.
- MessageParser: Parses raw CAN messages received from the gateway.
- receive_messages: Listens for incoming CAN messages and passes them to the message queue for processing.

## 📝 How to Use

### Set Up the Gateway:
1. Configure the gateway with the correct IP address, port, CAN port number, and baud rate.
2. Ensure the gateway is connected to the battery using the CAN protocol.

## Contact 📧

For any questions or inquiries, please contact:
- Email: [mohamedamine.najjar@isimg.tn](https://mail.google.com/mail/u/0/?fs=1&tf=cm&source=mailto&to=mohamedamine.najjar@isimg.tn)
- LinkedIn: [Mohamed Amine Najjar](https://www.linkedin.com/in/mohamed-amine-najjar-2808a726b/)

---

Happy coding! 😊
