from time import sleep
from datetime import datetime
from common import getDB
import Adafruit_DHT

class DHT11():
	def __init__(self, pin):
		self.pin = pin
	
	def readValue(self):
		value = None
		pin = self.pin
		
		try:
			value = Adafruit_DHT.read_retry(11,pin)
		except:
			pass
		
		return value
	
	def loop(self):
		sql = ('INSERT INTO TempHumidity (datetime,Humidity,Temperature) VALUES (%(datetime)s,%(humidity)s,%(temperature)s)')
		
		db = None
		cursor = None
		while True:
			if not db:
				db = getDB()
			
			date_time = datetime.now()
			
			try:
				cursor = db.cursor()
				humidity, temperature = self.readValue()
				if humidity and temperature:
					data = {
						'datetime': date_time,
						'humidity': humidity,
						'temperature': temperature
					}
					
					cursor.execute(sql,data)
					db.commit()
			except:
				pass
					
			sleep(30)
			
		db.close()