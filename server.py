from flask import Flask
from gevent.pywsgi import WSGIServer
from flask import Flask, request, render_template, send_from_directory, make_response
from common import getDB, startProcess, processAlive, createTables, terminateProcess
from gpiozero import PWMLED
from dht11 import DHT11
from ldr import LDR
import gevent
import gevent.monkey
import json
import picamera
import io
import settings

gevent.monkey.patch_all()

app = Flask(__name__)

debug = settings.DEBUG
dht11_pin = settings.DHT11_PIN
ldr_channel = settings.LDR_CHANNEL
led_pins = settings.LED_PINS

leds = {}
for pin in led_pins:
	try:
		leds[str(pin)] = PWMLED(pin)
	except:
		pass

dht = None
ldr = None
dht_process = None
ldr_process = None
camera = None

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/controlpanel')
def controlpanel():
	templateDate = {
		'leds': leds
	}
	
	return render_template('controlpanel.html', **templateDate)

@app.route('/controlpanel/light/<pin>')
def getLightValue(pin):
	led = leds[pin]
	result = {'Value':led.value}
	
	return json.dumps(result)

@app.route('/controlpanel/light/<pin>/set', defaults={'value': 0})
@app.route('/controlpanel/light/<pin>/set/<value>')
def setLightValue(pin,value):
	led = leds[pin]
	try:
		value = float(value)
		if value > 1:
			value = 1
		elif value < 0:
			value = 0
		
		led.value = value
	except:
		pass
		
	return ('', 204)

@app.route('/controlpanel/camera/<status>')
def setcamera(status):
	global camera
	try:
		if status == 'ON':
			camera = picamera.PiCamera()
		elif status == 'OFF':
			camera.close()
			camera = None
	except:
		pass
		
	return ('', 204)
	
@app.route('/controlpanel/camera/status')
def camerastatus():
	global camera
	status = 0
	if camera:
		status = 1
		
	result = {"Status":status}
	
	return json.dumps(result)

@app.route('/controlpanel/camera/capture')
def cameracapture():
	global camera
	
	image = None
	response = ('', 204)
	try:
		if not camera:
			camera = picamera.PiCamera()
		
		stream = io.BytesIO()
		camera.capture(stream,'jpeg')
		image = stream.getvalue()
		response = make_response(image)
		response.headers['Content-Type'] = 'image/jpeg'
	except:
		pass
	
	return response
	
@app.route('/settings')
def settings():
	return render_template('settings.html')

@app.route('/lightdata')
def lightdata():
	db = getDB()
	dict = {}
	if db:
		try:
			cursor = db.cursor()
			
			sql = 'SELECT * FROM Light'
			cursor.execute(sql)
			lightresults = cursor.fetchall()
			
			dict['cols'] = [
				{'id': 'timestamp', 'label': 'Timestamp', 'type': 'datetime'},
				{'id': 'value', 'label': 'Light Value', 'type': 'number'}
			]
			
			list = []
			for r in lightresults:
				datetime = r[1]
				d = {'c': [
					{'v': 'Date({},{},{},{},{},{})'.format(datetime.year,datetime.month,datetime.day,datetime.hour,datetime.minute,datetime.second)},
					{'v': r[2]}
				]}
				list.append(d)
			
			dict['rows'] = list
		except:
			pass
		
		db.close()
		
	return json.dumps(dict)

@app.route('/lightdata/latest')
def lightdatalatest():
	global ldr
	
	dict = {}
	try:
		value = ldr.readValue()
		
		dict['Value'] = value
	except:
		pass
	
	return json.dumps(dict)	

@app.route('/lightdata/table')
def lightdatatable():
	db = getDB()
	list = []
	if db:
		try:
			cursor = db.cursor()
			
			sql = 'SELECT * FROM Light'
			cursor.execute(sql)
			results = cursor.fetchall()
			
			for i,r in enumerate(results):
				d = {
					'count': (i + 1),
					'datetime': str(r[1]),
					'value': r[2]
				}
				list.append(d)
		except:
			pass
		
		db.close()
		
	return json.dumps(list)

@app.route('/lightmonitor')
def lightmonitor():
	status = processAlive(ldr_process)
	data = {'Status':status}
	
	return json.dumps(data)

@app.route('/lightmonitor/<status>')
def lightmonitorset(status):
	global ldr_process
	if status == 'ON':
		if not processAlive(ldr_process):
			ldr_process = startProcess(ldr.loop)
	elif status == 'OFF':
		terminateProcess(ldr_process)
		
	return ('', 204)
	
@app.route('/thdata')
def thdata():
	db = getDB()
	dict = {}
	if db:
		cursor = db.cursor()
		
		try:
			sql = 'SELECT * FROM TempHumidity'
			cursor.execute(sql)
			lightresults = cursor.fetchall()
			
			dict['cols'] = [
				{'id': 'timestamp', 'label': 'Timestamp', 'type': 'datetime'},
				{'id': 'humidity', 'label': 'Humidity', 'type': 'number'},
				{'id': 'temperature', 'label': 'Temperature', 'type': 'number'}
			]
			
			list = []
			for r in lightresults:
				datetime = r[1]
				d = {'c': [
					{'v': 'Date({},{},{},{},{},{})'.format(datetime.year,datetime.month,datetime.day,datetime.hour,datetime.minute,datetime.second)},
					{'v': r[2]},
					{'v': r[3]}
				]}
				list.append(d)
			
			dict['rows'] = list
		except:
			pass
		
		db.close()
		
	return json.dumps(dict)

@app.route('/thdata/latest')
def thdatalatest():
	global dht
	
	dict = {}
	try:
		value = dht.readValue()
		
		dict['Humidity'] = value[0]
		dict['Temperature'] = value[1]
	except:
		pass
		
	return json.dumps(dict)

@app.route('/thdata/table')
def thdatatable():
	db = getDB()
	list = []
	if db:
		try:
			cursor = db.cursor()
			
			sql = 'SELECT * FROM TempHumidity'
			cursor.execute(sql)
			results = cursor.fetchall()
			
			for i,r in enumerate(results):
				d = {
					'count': (i + 1),
					'datetime': str(r[1]),
					'temperature': r[2],
					'humidity': r[3]
				}
				list.append(d)
		except:
			pass
		
		db.close()
		
	return json.dumps(list)
	
@app.route('/thmonitor')
def thmonitor():
	status = processAlive(dht_process)
	data = {'Status':status}
	
	return json.dumps(data)
	
@app.route('/thmonitor/<status>')
def thmonitorset(status):
	global dht_process
	if status == 'ON':
		if not processAlive(dht_process):
			dht_process = startProcess(dht.loop)
	elif status == 'OFF':
		terminateProcess(dht_process)
		
	return ('', 204)
	
if __name__ == "__main__":
	createTables()
	
	dht = DHT11(dht11_pin)
	ldr = LDR(ldr_channel)
	
	dht_process = startProcess(dht.loop)
	ldr_process = startProcess(ldr.loop)
	
	try:
		http_server = WSGIServer(('0.0.0.0',8001),app)
		app.debug = debug
		http_server.serve_forever()
	except Exception as e:
		print('Exception: {}'.format(e))