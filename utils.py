import base64
import datetime
import hashlib
import io

import jwt
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
import random
import string

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
            data = Admin_JMQ.loads(token)
            key_data = bytes(data, encoding="utf-8")
            key_data = base64.decodebytes(key_data)
            user_info_bytes = ENCRY_UTIL.decrypt(key_data)
            user_info = user_info_bytes.decode('utf-8')
            if user_info:
                return func(*args, **kwargs)
            else:
                return jsonify("token error")
        except KeyError:
            return jsonify({"code": 200, "data": {"msg": "缺少token"}})
        except SignatureExpired:
            return jsonify({"code": 200, "data": {"msg": "token過期"}})
        except BadSignature:
            return jsonify({"code": 200, "data": {"msg": "token錯誤"}})
        except Exception as e:
            return jsonify({"code": 200, "data": {"msg": "token錯誤"}})
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
            return jsonify({"code": 200, "data": {"msg": "缺少token"}})
        except SignatureExpired:
            return jsonify({"code": 200, "data": {"msg": "token過期"}})
        except BadSignature:
            return jsonify({"code": 200, "data": {"msg": "token錯誤"}})
        except Exception as e:
            return jsonify({"code": 200, "data": {"msg": "token錯誤"}})
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

