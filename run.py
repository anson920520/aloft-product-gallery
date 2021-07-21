from setting import HOST, PORT
from models import app
from api import admin_api
from flask import request


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
        headers = request.headers.get('Access-Control-Request-Headers')
        if headers:
            response.headers['Access-Control-Allow-Headers'] = headers
    return response


app.register_blueprint(admin_api, url_prefix='/admin')

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True, gevent=10)
