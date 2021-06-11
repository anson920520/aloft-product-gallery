FROM zhengquantao/python-nginx:3.8

RUN mkdir /root/wholeChina

COPY . /root/wholeChina

WORKDIR /root/wholeChina

COPY nginx.conf /etc/nginx/nginx.conf

# 升级pip
RUN pip3 install --upgrade pip -i  https://mirrors.aliyun.com/pypi/simple

# pip读取requirements.txt内容安装所需的库
RUN pip3 install -r requirements.txt -i  https://mirrors.aliyun.com/pypi/simple


ENTRYPOINT bash /root/wholeChina/env.sh && uwsgi -i /root/wholeChina/uwsgi.ini  && nginx -g 'daemon off;'


# run command
# 8.docker run --name wholechina -p 7031:7031 -p 7032:7032 -p 7033:7033 -p 7035:7035 --link wc-mysql:wc-mysql -e ADMIN_IP="http://127.0.0.1:7031/" -e CLIENT_IP="http://127.0.0.1:7031/" -d wholechina