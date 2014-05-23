import sys
sys.path.append('/home/pi/quick2wire-python-api')
import quick2wire.i2c as i2c

ADDRESS = 0x18
TEMPERATURE_REGISTER = 0x05

def readTemperature():
	with i2c.I2CMaster() as bus:
		read_results = bus.transaction(i2c.writing_bytes(ADDRESS, TEMPERATURE_REGISTER), i2c.reading(ADDRESS, 2))

		upperByte = read_results[0][0]
		lowerByte = read_results[0][1]

		upperByte &= 0x1F

		if ((upperByte & 0x10) == 0x10):
			upperByte &= 0x0F
			temperature = 256 - (upperByte * 16 + lowerByte / 16)
		else:
			temperature = (upperByte * 16 + lowerByte / 16)

		return temperature
		
if __name__ == "__main__":
    print(readTemperature())