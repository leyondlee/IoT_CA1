from multiprocessing import Process
import MySQLdb
import settings

def getDB():
	host = settings.DB_HOST
	port = settings.DB_PORT
	user = settings.DB_USER
	password = settings.DB_PASSWORD
	defaultdb = settings.DB_DEFAULTDB
	
	db = None
	try:
		db = MySQLdb.connect(host=host, port=port, user=user, passwd=password, db=defaultdb)
	except:
		pass
		
	return db

def createTables():
	createlight_sql = """CREATE TABLE `Light` (
		`id` int(11) NOT NULL AUTO_INCREMENT,
		`datetime` datetime NOT NULL,
		`value` int(11) NOT NULL,
		PRIMARY KEY (`id`)
	)"""
	
	createth_sql = """CREATE TABLE `TempHumidity` (
		`id` int(11) NOT NULL AUTO_INCREMENT,
		`datetime` datetime NOT NULL,
		`Humidity` float NOT NULL,
		`Temperature` float NOT NULL,
		PRIMARY KEY (`id`)
	)"""
	
	db = getDB()
	if db:
		try:
			cursor = db.cursor()
			cursor.execute(createlight_sql)
			cursor.execute(createth_sql)
			db.commit()
		except:
			pass

def startProcess(function):
	process = Process(target=function)
	process.start()
	
	return process
	
def terminateProcess(process):
	if process:
		try:
			process.terminate()
		except:
			pass
	
def processAlive(process):
	alive = False
	if process:
		try:
			alive = process.is_alive()
		except:
			pass
			
	return alive