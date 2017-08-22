from gpiozero import MCP3008
from time import sleep
from datetime import datetime
from common import getDB
import threading

class LDR():
	def __init__(self, channel):
		self.ldr = MCP3008(channel=channel)
	
	def readValue(self):
		value = None
		ldr = self.ldr
		
		try:
			value = ldr.value
			if value:
				value = round((1024 / value) % 1024)
		except:
			pass
		
		return value
	
	def loop(self):
		sql = ('INSERT INTO Light (datetime,value) VALUES (%(datetime)s,%(value)s)')
		
		db = None
		cursor = None
		while True:
			if not db:
				db = getDB()
				
			date_time = datetime.now()
			
			try:
				cursor = db.cursor()
				ldr_value = self.readValue()
				if ldr_value:
					data = {
						'datetime': date_time,
						'value': ldr_value
					}
					cursor.execute(sql,data)
					db.commit()
			except:
				pass
					
			sleep(30)
			
		db.close()