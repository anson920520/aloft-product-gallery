import configparser
import os

# 基礎配置
conf = configparser.ConfigParser()
curpath = os.path.dirname(os.path.realpath(__file__))
cfgpath = os.path.join(curpath, 'config.ini')
# cfgpath = os.path.join(curpath, 'config-dev.ini')

conf.read(cfgpath, encoding='utf-8')
sections = conf.sections()

pay = conf.items('pay')
print(pay)

stripe_pay = conf.items('stripe_pay')

mysql = conf.items('mysql')
print(mysql)

client = conf.items('client')
print(client)


# 数据库信息

SQLALCHEMY_DATABASE_URI = mysql[0][1]

# 图片、PDF信息、首页json文件
HOST = client[0][1]
PORT = client[1][1]
DEBUG = client[2][1]
IMG_SIZE = eval(client[3][1])
# BASE_URL = "http://192.168.1.115:5006/static/"   # os.getenv("ADMIN_IP")
# docker
BASE_URL = client[4][1]
IMG_PATH = client[5][1]
PDF_PATH = client[6][1]
FILE = client[7][1]

# 加密信息
SALT = b"CHINA"
JWT_KEYS = "WATCHS"
TIMEOUT = 3600*9


merchantID = pay[0][1]
publicKey = pay[1][1]
privateKey = pay[2][1]
sandBoxToken = pay[3][1]
productionToken = pay[4][1]


API_KEY = stripe_pay[0][1]
PUB_KEY = stripe_pay[1][1]