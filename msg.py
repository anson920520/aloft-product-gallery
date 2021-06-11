from flask import jsonify


class Message:
    @staticmethod
    def true_msg(returnmsg, data=None, token=0):
        if token == 0:
            msg = {
                "status": 200,
                "msg": returnmsg,
                "data": data
            }
        else:
            msg = {
                "status": 200,
                "msg": returnmsg,
                "data": data,
                "token": token,
                "token_type": str(type(token))
            }

        return jsonify(msg)

    @staticmethod
    def error_msg(returnmsg, code=460):
        msg = {
            "status": code,
            "msg": returnmsg
        }
        return jsonify(msg)
