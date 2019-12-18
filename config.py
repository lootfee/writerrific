import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__) )
load_dotenv()

class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
	SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	POSTS_PER_PAGE = 20
	UPLOADED_PHOTOS_DEST = os.getcwd() + '/app/static/uploads'
	MAIL_SERVER = os.getenv('MAIL_SERVER')
	MAIL_PORT = int(os.getenv('MAIL_PORT') or 25)
	MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') is not None
	MAIL_USERNAME = os.getenv('MAIL_USERNAME')
	MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
	ADMINS = ['support@writerrific.com']
	