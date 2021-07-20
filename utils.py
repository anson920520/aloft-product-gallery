import base64
import datetime
import hashlib
import io
import time

import xlsxwriter

from setting import JWT_KEYS, ADMIN_TIMEOUT, CLIENT_TIMEOUT, SALT, ADMIN_JWT_KEYS
from functools import wraps
from flask import request, jsonify
from pyDes import *
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from smtplib import SMTP
from email.mime.text import MIMEText
from email.header import Header

ENCRY_UTIL = des(b"DESCRYPT", CBC, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)

S_JMQ = Serializer(JWT_KEYS, expires_in=CLIENT_TIMEOUT*3600)
Admin_JMQ = Serializer(ADMIN_JWT_KEYS, expires_in=ADMIN_TIMEOUT*3600)


def generate_auth_token(data):
    key_data = ENCRY_UTIL.encrypt(data)
    key_data = base64.encodebytes(key_data)
    key_data = str(key_data, encoding="utf-8")
    return S_JMQ.dumps(key_data).decode("utf-8")


def generate_admin_auth_token(data):
    key_data = ENCRY_UTIL.encrypt(data)
    key_data = base64.encodebytes(key_data)
    key_data = str(key_data, encoding="utf-8")
    return Admin_JMQ.dumps(key_data).decode("utf-8")


def check_login(func):
    @wraps(func)
    def is_login(*args, **kwargs):
        try:
            token = request.headers["Authorization"]
            data = S_JMQ.loads(token)
            key_data = bytes(data, encoding="utf-8")
            key_data = base64.decodebytes(key_data)
            user_info_bytes = ENCRY_UTIL.decrypt(key_data)
            user_info = user_info_bytes
            if user_info:
                return func(*args, **kwargs)
            else:
                return jsonify("token error")
        except KeyError:
            return jsonify({"code": 1003, "data": {"msg": "缺少token"}})
        except SignatureExpired:
            return jsonify({"code": 1005, "data": {"msg": "token過期"}})
        except BadSignature:
            return jsonify({"code": 4000, "data": {"msg": "token錯誤"}})
        except Exception as e:
            print(e)
            return jsonify({"code": 3000, "data": {"msg": "數據錯誤"}})
    return is_login


def check_admin(func):
    @wraps(func)
    def is_admin(*args, **kwargs):
        try:
            token = request.headers["Authorization"]
            data = Admin_JMQ.loads(token)
            key_data = bytes(data, encoding="utf-8")
            key_data = base64.decodebytes(key_data)
            user_info_bytes = ENCRY_UTIL.decrypt(key_data)
            user_info = user_info_bytes.decode('utf-8')
            user_dict = eval(user_info)
            if user_dict["role"] == 1:
                return func(*args, **kwargs)
            elif user_dict["role"] == 2:
                # 權限2 不能刪除
                if request.method == "DELETE":
                    return jsonify({"code": 4004, "data": {"msg": "你沒有權限"}})
                else:
                    return func(*args, **kwargs)
            elif user_dict["role"] == 3:
                if request.method != "GET":
                    # 權限3 只能看
                    return jsonify({"code": 4004, "data": {"msg": "你沒有權限"}})
                else:
                    return func(*args, **kwargs)
            else:
                return jsonify("token error")
        except KeyError:
            return jsonify({"code": 1003, "data": {"msg": "缺少token"}})
        except SignatureExpired:
            return jsonify({"code": 1005, "data": {"msg": "token過期"}})
        except BadSignature:
            return jsonify({"code": 4000, "data": {"msg": "token錯誤"}})
        except Exception as e:
            print(e)
            return jsonify({"code": 3000, "data": {"msg": "數據錯誤"}})
    return is_admin


def loads(data):
    res = []
    if isinstance(data, list):
        for item in data:
            try:
                res.append(item.to_dict())
            except:
                pass
    else:
        try:
            res.append(data.to_dict())
        except:
            pass
    return res


def hash_password(pwd):
    hashs = hashlib.md5(SALT)
    hashs.update(bytes(str(pwd), encoding='utf-8'))
    hash_pwd = hashs.hexdigest()
    return hash_pwd


def sender_email(receiver: list, message: str) -> bool:
    mail_server = 'smtp.qq.com'
    port = 25
    sender = '1483906080@qq.com'
    sender_pass_code = 'yghetjokovjufijc'
    # mail_msg = random.sample(string.digits, 5)
    # check_email_code = ''  # 要发送的内容
    # for item in mail_msg:
    #     check_email_code += str(item)

    msg = MIMEText(message, 'html', 'utf-8')  # 正文 ， MIME的subtype纯文本， 编码
    msg['From'] = "鴻華餐飲供應有限公司"
    # msg['From'] = sender
    # msg['To'] = receiver
    msg['Subject'] = Header('鴻華餐飲供應有限公司', 'utf-8')
    server = SMTP(mail_server, port)
    try:
        # server.set_debuglevel(1)  # 打印出SMTP服务器的交互信息
        server.login(sender, sender_pass_code)
        server.sendmail(sender, receiver, msg.as_string())  # 发送者, 接收人(可以是多个人，用list群发), 正文转成str
        server.quit()
        return True
    except Exception as e:
        server.quit()
        return False


def create_excel(xlsdate, onelist, fields_list, name):
    """
    生成表格
    :param xlsdate: excel名称
    :param onelist: list[dict]
    :param fields_list: list[dict.keys]
    :return: excel文件流
    """
    filename = xlsdate
    fp = io.BytesIO()
    # workbook = xlwt.Workbook(fp)
    workbook = xlsxwriter.Workbook(fp)
    no_book_sheet = workbook.add_worksheet(name=name)
    for field in range(0, len(fields_list)):
        no_book_sheet.write(0, field, fields_list[field])

    for row in range(1, len(onelist) + 1):
        for col in range(0, len(fields_list)):
            no_book_sheet.write(row, col, u'%s' % onelist[row-1].get(fields_list[col]))

    workbook.close()
    fp.seek(0)
    return (fp, filename)


def year_month():
    a = datetime.datetime.now().year
    print(a)
    print(type(a))
    y_m = []
    for x in range(1, 13):
        dt_start = (datetime.datetime(a, x, 1)).strftime("%Y-%m-%d")
        if 12 == x:
            dt_end = (datetime.datetime(a, 12, 31)).strftime("%Y-%m-%d")
        else:
            dt_end = (datetime.datetime(a, x + 1, 1) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        y_m_tuple = list()
        y_m_tuple.append(dt_start)
        y_m_tuple.append(dt_end)
        y_m.append(y_m_tuple)

    return y_m


def timeS(data):
    timeArray = time.strptime(data, "%Y-%m-%d")
    timeStamp = int(time.mktime(timeArray))
    return timeStamp

def timeD(data):
    dateArray = datetime.datetime.fromtimestamp(data)
    otherStyleTime = dateArray.strftime("%Y-%m-%d %H:%M:%S")
    return otherStyleTime


# 本月第一天到最后一天时间搓
def timeMonth():
    now = datetime.datetime.now()
    # 每月新增会员
    this_month_start = datetime.datetime(now.year, now.month, 1)
    this_month_start = this_month_start.strftime('%Y-%m-%d')
    time_start = timeS(this_month_start)
    this_month_end = datetime.datetime(now.year, now.month + 1, 1) - datetime.timedelta(
        days=1) + datetime.timedelta(
        hours=23, minutes=59, seconds=59)
    this_month_end = this_month_end.strftime('%Y-%m-%d')
    time_end = timeS(this_month_end)
    return time_start, time_end


# 上个月的第一天---最后一天时间搓
def lastMonth():
    now = datetime.datetime.now()
    this_month_start = datetime.datetime(now.year, now.month, 1)
    last_month_end = this_month_start - datetime.timedelta(days=1) + datetime.timedelta(
        hours=23, minutes=59, seconds=59)
    last_month_start = datetime.datetime(last_month_end.year, last_month_end.month, 1)
    last_month_end = last_month_end.strftime('%Y-%m-%d')
    last_month_start = last_month_start.strftime('%Y-%m-%d')
    time_end = timeS(last_month_end)
    time_start = timeS(last_month_start)
    return time_start, time_end

