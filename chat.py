import base64
import random
import urllib
import uuid

from geventwebsocket.websocket import WebSocket, WebSocketError
import json
import time
import jwt
from models import app
from flask_uwsgi_websocket import GeventWebSocket


ws = GeventWebSocket(app)

# 存在线人数
user_socket_dict = {}
# 存未读消息， 每个人最多5条
user_socket_list = {}

# 后面升级多个管理员
# {chat_admin: [["xxx1", ojb1, '最后连接时间戳'], ["xxx2", obj2], ["xxx3", obj3], ["xxx4", obj4]], "user": ["obj", '最后连接时间戳']}"

key = "zhananbudanchou1234678"


def encode_session():
    # payload
    token_dict = {
        'iat': int(time.time()),  # 时间戳
        'exp': 60*5
    }

    # headers
    headers = {
        'alg': "HS256",  # 声明所使用的算法
    }
    jwt_token = jwt.encode(token_dict,  # payload, 有效载体
                           key=key,  # 进行加密签名的密钥
                           algorithm="HS256",  # 指明签名算法方式, 默认也是HS256
                           headers=headers  # json web token 数据结构包含两部分, payload(有效载体), headers(标头)
                           ).decode('ascii')  # python3 编码后得到 bytes, 再进行解码(指明解码的格式), 得到一个str

    return jwt_token


def decode_session(token):
    try:
        # 需要解析的 jwt        密钥                使用和加密时相同的算法
        data = jwt.decode(token, key, algorithms=['HS256'])
        return data
    except Exception as e:
        # 如果 jwt 被篡改过; 或者算法不正确; 如果设置有效时间, 过了有效期; 或者密钥不相同; 都会抛出相应的异常
        print(e)
        return False


# 对名字编码
def decode_url(data):
    try:
        # 解码
        name = urllib.parse.unquote(base64.b64decode(str.encode(data)).decode())
        print(name)
        return name
    except:
        return False


@ws.route('/ws/<username>')
def wsChat(ws, username):
    # 前端用window.btoa(encodeURI("哈哈哈哈"))编码
    # 对名字编码
    # 防止一些低级的恶意用户
    username = decode_url(username)
    user_socket = ws
    if not username:
        user_socket.close()
        return

    if not user_socket:
        return "请以WEBSOCKET方式连接"

    # 相同的人进来关闭上一次连接
    if user_socket_dict.get(username) and username != "chat_admin":
        user_socket_dict.get(username).close()
        print("已关闭当前连接", username)
        user_socket_dict[username] = user_socket
        # user_socket.send(json.dumps({"admin": random.choice(user_socket_dict.get("chat_admin"))}))
    else:
        # if username == "chat_admin":
        #     chat_msg = [uuid.uuid4().hex, user_socket, int(time.time())]
        #     user_socket_dict["chat_admin"].append(chat_msg)
        # else:
        #     user_socket_dict[username] = [user_socket, int(time.time())]
        user_socket_dict[username] = user_socket
    # user_socket_dict[username] = user_socket
    print(user_socket_dict)

    # 获取未读消息 重发给用户
    if username in user_socket_list:
        for item in user_socket_list.get(username):
            user_socket.send(item)
        try:
            del user_socket_list[username]
        except:
            pass
    while True:
        try:
            user_msg = user_socket.receive()
            if not user_msg:
                continue
            user_msg = json.loads(user_msg)
            print(user_msg)
            if user_msg.get("close"):
                # 如果close在user_socket_dict
                if user_socket_dict.get(user_msg.get("close")):
                    # 发送关闭消息
                    user_socket_dict.get("chat_admin").send(json.dumps({"code": 400, "data": user_msg.get("close")}))
                    user_socket_dict.get(user_msg.get("close")).send(json.dumps({"code": 400, "data": user_msg.get("close")}))
                    if user_socket_dict.get(user_msg.get("close")):
                        # 关闭
                        user_socket_dict.get(user_msg.get("close")).close()
            to_user_socket = user_socket_dict.get(user_msg.get("to_user"))
            send_msg = {
                "send_msg": user_msg.get("send_msg"),
                "send_user": username,
            }
            if to_user_socket:
                try:
                    to_user_socket.send(json.dumps(send_msg))
                except:
                    # 如果是报错说明此人已经下线
                    # 如果是客户端发送给管理员 管理员不存在
                    if user_msg.get("to_user") == "chat_admin":
                        user_socket.send(
                            json.dumps({"code": 600, "data": "當前管理員暫時離開，請嘗試用其他方式聯係(Email、FaceBook、Phone)"}))
                    # 暂存5条信息
                    if user_socket_list.get(user_msg.get("to_user")) and len(
                            user_socket_list[user_msg.get("to_user")]) < 5:
                        user_socket_list[user_msg.get("to_user")].append(json.dumps(send_msg))
                    else:
                        user_socket_list[user_msg.get("to_user")] = [json.dumps(send_msg)]
            else:
                # 如果是客户端发送给管理员 管理员不存在
                if user_msg.get("to_user") == "chat_admin":
                    user_socket.send(json.dumps({"code": 600, "data": "當前管理員暫時離開，請嘗試用其他方式聯係(Email、FaceBook、Phone)"}))
                # 暂存5条信息
                if user_socket_list.get(user_msg.get("to_user")) and len(user_socket_list[user_msg.get("to_user")])<5:
                    user_socket_list[user_msg.get("to_user")].append(json.dumps(send_msg))
                else:
                    user_socket_list[user_msg.get("to_user")] = [json.dumps(send_msg)]
        except WebSocketError as e:
            # # 删除关闭人员
            # del user_socket_dict[user_msg.get("close")]
            # print(user_socket_dict)
            # print(e)
            # 删除关闭人员
            if user_msg:
                if user_msg.get("close"):
                    user_socket = user_socket_dict.pop(user_msg.get("close"))
                    user_socket.close()
                    user_socket_dict.get("chat_admin").send(json.dumps({"code": 400, "data": username}))
                    print(user_socket_dict)
                    print(e)
                    return "connect error"
            if username != "chat_admin":
                print("主动关闭======")
                user_socket_dict.get("chat_admin").send(json.dumps({"code": 400, "data": username}))
                return "connect error"
            # 返回东西 防止TypeError
            return "connect error"
        except Exception as e:
            print("出错了：", e)
            # 返回东西 防止TypeError
            return "server error"


@app.route('/wsClose/<username>', methods=["GET"])
def wsClose(username):
    if user_socket_dict.get(username):
        try:
            user_socket = user_socket_dict.get(username)
            del user_socket_dict[username]
            user_socket.close()
        except:
            print("关闭出现异常")

    return {"code": 200, "data": "success"}
