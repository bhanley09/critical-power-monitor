from pymodbus.client import ModbusSerialClient

# Change this after you plug in the USB-RS485 cable.
# Check Windows Device Manager → Ports (COM & LPT)
PORT = "COM3"

BAUD_RATES = [9600, 19200]
PARITIES = ["N", "E", "O"]  # None, Even, Odd
STOP_BITS = [1, 2]
SLAVE_IDS = range(1, 11)

TEST_REGISTER = 0
TEST_COUNT = 10


def try_connection(baudrate, parity, stopbits, slave_id):
    print(f"\nTrying: port={PORT}, baud={baudrate}, parity={parity}, stopbits={stopbits}, slave={slave_id}")

    client = ModbusSerialClient(
        port=PORT,
        baudrate=baudrate,
        parity=parity,
        stopbits=stopbits,
        bytesize=8,
        timeout=2
    )

    if not client.connect():
        print("Could not open serial port.")
        return

    try:
        result = client.read_holding_registers(
            address=TEST_REGISTER,
            count=TEST_COUNT,
            slave=slave_id
        )

        if result.isError():
            print("No valid response.")
        else:
            print("SUCCESS - controller responded!")
            print(f"Registers: {result.registers}")

    except Exception as error:
        print(f"Error: {error}")

    finally:
        client.close()


print("Starting Kohler Decision-Maker Modbus scan...")
print("Use Ctrl + C to stop.\n")

for baud in BAUD_RATES:
    for parity in PARITIES:
        for stopbits in STOP_BITS:
            for slave_id in SLAVE_IDS:
                try_connection(baud, parity, stopbits, slave_id)

print("\nScan complete.")