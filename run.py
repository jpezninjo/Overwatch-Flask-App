# run.py

from app import app

if __name__ == '__main__':
	if app.debug:
		handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
		handler.setLevel(logging.INFO)
		app.logger.addHandler(handler)

	app.run(port=5000, threaded=True)