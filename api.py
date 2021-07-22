import json
import os
import time

import requests
from flask import Blueprint, request, jsonify, make_response, Response
from utils import TEMPLATE

from utils import generate_auth_token, check_login, hash_password, loads, create_excel, sender_email, \
    generate_admin_auth_token, check_admin, timeMonth, timeD
from setting import rate as rates, IMG_SIZE, ADMIN_TIMEOUT, CLIENT_TIMEOUT, IMG_PATH, PDF_PATH, FILE, merchantID, \
    publicKey, privateKey, API_KEY, PUB_KEY, BASE_URL
import uuid
import datetime
from models import db, Brand, Images, Category, Watches, UserInfo, Orders, OrderDetail, Address, Favorite, ShoppingCar, \
    Admin, Role
from sqlalchemy import text, extract, or_, func
from pay.pay import third_pay, client_token
from pay.stripe_pay import create_purchase

rate = rates

admin_api = Blueprint('admin', __name__)


# client登錄
@admin_api.route("/signin", methods=["POST"])
def login():
    """
    客户端登录
    :return:
    """
    username = request.json.get("username")
    password = request.json.get("password")
    if not all([username, password]):
        return jsonify({"code": 1002, "data": {"msg": "缺少參數"}})
    is_user = UserInfo.query.filter_by(username=username, delete_at=None).first()
    if not is_user:
        return jsonify({"code": 2004, "data": {"msg": "用戶不存在"}})
    if is_user.password != hash_password(password):
        return jsonify({"code": 2005, "data": {"msg": "密碼錯誤"}})
    user_msg = {"name": username, "password": is_user.password}
    token = generate_auth_token(json.dumps(user_msg, ensure_ascii=False))
    user_data = is_user.to_dict()
    user_data["token"] = token
    return jsonify({"code": 200, "data": user_data})


# admin登錄
@admin_api.route("/adminSignin", methods=["POST"])
def admin_login():
    """
    客户端登录
    :return:
    """
    username = request.json.get("username")
    password = request.json.get("password")
    if not all([username, password]):
        return jsonify({"code": 1002, "data": {"msg": "缺少參數"}})
    is_user = Admin.query.filter_by(username=username, delete_at=None).first()
    if not is_user:
        return jsonify({"code": 2004, "data": {"msg": "用戶不存在"}})
    if is_user.password != hash_password(password):
        return jsonify({"code": 2005, "data": {"msg": "密碼錯誤"}})
    user_msgs = username + "&" + is_user.password + "&" + str(is_user.role)
    user_msg = {"username": username,  "password": is_user.password, "role": is_user.role}
    token = generate_admin_auth_token(user_msgs)
    user_msg["token"] = token
    user_msg["role_name"] = is_user.admin_role.role
    return jsonify({"code": 200, "data": user_msg})


# 管理員管理
@admin_api.route("/adminUser", methods=["GET", "POST", "PUT", "DELETE"])
@check_admin
def admin_user():
    method = request.method
    if method == "GET":
        uid = request.args.get("id")
        offset = request.args.get("offset", 20)
        page = request.args.get("page", 1)
        if uid:
            user_obj = Admin.query.filter_by(id=uid, delete_at=None).first()
            item_dict = {}
            item_dict["id"] = user_obj.id
            item_dict["username"] = user_obj.username
            item_dict["password"] = user_obj.password
            item_dict["role"] = user_obj.role
            item_dict["role_name"] = user_obj.admin_role.role
            ret = {"code": 200, "data": {"user_list": item_dict}}
        else:
            user_obj = Admin.query.filter_by(delete_at=None).order_by(Admin.id.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
            count = Admin.query.filter_by(delete_at=None).count()
            user_list = []
            for item in user_obj:
                item_dict = {}
                item_dict["id"] = item.id
                item_dict["username"] = item.username
                item_dict["password"] = item.password
                item_dict["role"] = item.role
                item_dict["role_name"] = item.admin_role.role
                user_list.append(item_dict)
            print(user_list)
            ret = {"code": 200, "data": {"user_list": user_list, "count": count}}
        return jsonify(ret)
    elif method == "PUT":
        data = request.json
        uid = data.get("id")
        password = data.get("password", "123456")
        username = data.get("username")
        role = data.get("role")
        if not all([username, password, role]):
            ret = {"code": 1002, "data": {"msg": "缺少必傳參數"}}
            return jsonify(ret)
        if role == 1:
            ret = {"code": 1003, "data": {"msg": "一個系統中只能有一個超級管理員"}}
            return jsonify(ret)
        is_obj = Admin.query.filter(Admin.id!=uid).filter_by(username=username, delete_at=None).first()
        if is_obj:
            ret = {"code": 1004, "data": {"msg": "此用户已存在"}}
            return jsonify(ret)
        user_obj = Admin.query.filter_by(id=uid).first()
        user_obj.password = hash_password(password)
        user_obj.username = username
        user_obj.role = role
        user_obj.update_at = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
        return jsonify(ret)
    elif method == "POST":
        data = request.json
        username = data.get("username")
        password = data.get("password", "123456")
        role = data.get("role")
        if not all([username, password, role]):
            ret = {"code": 1002, "data": {"msg": "缺少必傳參數"}}
            return jsonify(ret)
        if role == 1:
            ret = {"code": 1003, "data": {"msg": "一個系統中只能有一個超級管理員"}}
            return jsonify(ret)
        is_obj = Admin.query.filter_by(username=username, delete_at=None).first()
        if is_obj:
            ret = {"code": 1004, "data": {"msg": "此用户已存在"}}
            return jsonify(ret)
        user_obj = Admin(username=username, password=hash_password(password), role=role, create_at=datetime.datetime.now())
        db.session.add(user_obj)
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "增加成功"}}

        return jsonify(ret)
    else:
        data = request.json
        uid = data.get("id")
        user_obj = Admin.query.filter_by(id=uid).first()
        user_obj.delete_at = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
        return jsonify(ret)


# 獲取權限
@admin_api.route("/role", methods=["GET"])
@check_admin
def role():
    role_obj = Role.query.all()
    role_list = loads(role_obj)
    ret = {"code": 200, "data": {"role_list": role_list}}
    return jsonify(ret)


@admin_api.route("/client/user", methods=["GET"])
@check_login
def client_user():
    uid = request.args.get("uuid")
    user_obj = UserInfo.query.filter_by(uuid=uid, delete_at=None).first()
    user_list = loads(user_obj)
    ret = {"code": 200, "data": {"user_list": user_list}}
    return jsonify(ret)

# 注册
@admin_api.route("/client/create/user", methods=["POST"])
def client_create_user():
    data = request.json
    username = data.get("username")
    password = data.get("password", "123456")
    email = data.get("email")
    phone = data.get("phone")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    birthday = data.get("birthday")
    country = data.get("country")
    if not all([username, phone, email]):
        ret = {"code": 1002, "data": {"msg": "缺少必傳參數"}}
        return jsonify(ret)
    is_obj = UserInfo.query.filter_by(username=username, delete_at=None).first()
    if is_obj:
        ret = {"code": 1004, "data": {"msg": "此用户已存在"}}
        return jsonify(ret)
    str_uuid = uuid.uuid4().hex
    user_obj = UserInfo(uuid=str_uuid, username=username, password=hash_password(password), email=email, phone=phone,
                        first_name=first_name, last_name=last_name, birthday=birthday, country=country, create_at=datetime.datetime.now())
    db.session.add(user_obj)
    db.session.commit()
    ret = {"code": 200, "data": {"msg": "增加成功"}}

    return jsonify(ret)

# 编辑
@admin_api.route("/client/edit/user", methods=["PUT"])
@check_login
def client_edit_user():
    data = request.json
    uid = data.get("uuid")
    email = data.get("email")
    phone = data.get("phone")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    birthday = data.get("birthday")
    country = data.get("country")
    user_obj = UserInfo.query.filter_by(uuid=uid).first()
    if user_obj:
        user_obj.email = email
        user_obj.phone = phone
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        user_obj.birthday = birthday
        user_obj.country = country
        user_obj.update_at = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
    else:
        ret = {"code": 1003, "data": {"msg": "用戶不存在"}}
    return jsonify(ret)


@admin_api.route("/client/edit/pwd", methods=["PUT"])
@check_login
def client_edit_pwd():
    data = request.json
    uid = data.get("uuid")
    password = data.get("password", "123456")
    user_obj = UserInfo.query.filter_by(uuid=uid).first()
    if user_obj:
        user_obj.password = hash_password(password)
        user_obj.update_at = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
    else:
        ret = {"code": 1003, "data": {"msg": "用戶不存在"}}
    return jsonify(ret)


# 用戶信息
@admin_api.route("/user", methods=["GET", "POST", "PUT", "DELETE"])
@check_admin
def user():
    method = request.method
    if method == "GET":
        uid = request.args.get("uuid")
        offset = request.args.get("offset", 20)
        page = request.args.get("page", 1)
        search = request.args.get("search")  # 模糊查找
        if search:
            user_obj = UserInfo.query.filter(UserInfo.username.like("%"+search+"%")).filter_by(delete_at=None).order_by(UserInfo.create_at.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
            user_list = loads(user_obj)
            ret = {"code": 200, "data":{"user_list": user_list}}
        else:
            if uid:
                user_obj = UserInfo.query.filter_by(uuid=uid, delete_at=None).first()
                user_list = loads(user_obj)
                ret = {"code": 200, "data": {"user_list": user_list}}
            else:
                user_obj = UserInfo.query.filter_by(delete_at=None).order_by(UserInfo.id.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
                count = UserInfo.query.filter_by(delete_at=None).count()
                user_list = loads(user_obj)
                print(user_list)
                ret = {"code": 200, "data": {"user_list": user_list, "count": count}}
        return jsonify(ret)
    elif method == "PUT":
        data = request.json
        uid = data.get("uuid")
        password = data.get("password", "123456")
        email = data.get("email")
        phone = data.get("phone")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        birthday = data.get("birthday")
        country = data.get("country")
        user_obj = UserInfo.query.filter_by(uuid=uid).first()
        user_obj.password = hash_password(password)
        user_obj.email = email
        user_obj.phone = phone
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        user_obj.birthday = birthday
        user_obj.country = country
        user_obj.update_at = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
        return jsonify(ret)
    elif method == "POST":
        data = request.json
        username = data.get("username")
        password = data.get("password", "123456")
        email = data.get("email")
        phone = data.get("phone")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        birthday = data.get("birthday")
        country = data.get("country")
        if not all([username, phone, email]):
            ret = {"code": 1002, "data": {"msg": "缺少必傳參數"}}
            return jsonify(ret)
        is_obj = UserInfo.query.filter_by(username=username, delete_at=None).first()
        if is_obj:
            ret = {"code": 1004, "data": {"msg": "此用户已存在"}}
            return jsonify(ret)
        str_uuid = uuid.uuid4().hex
        user_obj = UserInfo(uuid=str_uuid, username=username, password=hash_password(password), email=email, phone=phone,
                            first_name=first_name, last_name=last_name, birthday=birthday, country=country, create_at=datetime.datetime.now())
        db.session.add(user_obj)
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "增加成功"}}

        return jsonify(ret)
    else:
        data = request.json
        uid = data.get("uuid")
        user_obj = UserInfo.query.filter_by(uuid=uid).first()
        user_obj.delete_at = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
        return jsonify(ret)


# 地址
@admin_api.route("/address", methods=["GET", "POST", "PUT", "DELETE"])
@check_login
def address():
    method = request.method
    if method == "GET":
        user_id = request.args.get("user_id")
        page = request.args.get("page", 1)
        offset = request.args.get("offset", 5)
        id = request.args.get("id")
        if user_id:
            addr_obj = Address.query.filter_by(user_id=user_id, is_delete=0).order_by(Address.id.desc()).limit(
                int(offset)).offset((int(page) - 1) * int(offset)).all()
            addr_list = loads(addr_obj)
            print(addr_list)
            ret = {"code": 200, "data": {"address_list": addr_list}}
            return jsonify(ret)

        if id:
            addr_obj = Address.query.filter_by(id=id, is_delete=0).first()
            if addr_obj:
                addr_list = addr_obj.to_dict()
                print(addr_list)
            else:
                addr_list = {}
            ret = {"code": 200, "data": addr_list}
            return jsonify(ret)
        else:
            return jsonify({"code": 4005, "data": {"msg": "缺少參數"}})
    elif method == "PUT":
        data = request.json
        uid = data.get("id")
        first_name = data.get("first_name", "123456")
        last_name = data.get("last_name")
        appellation = data.get("appellation")
        area = data.get("area")
        city = data.get("city")
        district = data.get("district")
        place = data.get("place")
        mobile = data.get("mobile")
        user_obj = Address.query.filter_by(id=uid).first()
        user_obj.appellation = appellation
        user_obj.area = area
        user_obj.city = city
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        user_obj.district = district
        user_obj.place = place
        user_obj.mobile = mobile
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
        return jsonify(ret)
    elif method == "POST":
        data = request.json
        user_id = data.get("user_id")
        first_name = data.get("first_name", "123456")
        last_name = data.get("last_name")
        appellation = data.get("appellation")
        area = data.get("area")
        city = data.get("city")
        district = data.get("district")
        place = data.get("place")
        mobile = data.get("mobile")
        if not all([mobile, first_name, appellation, area, district]):
            ret = {"code": 1002, "data": {"msg": "缺少必傳參數"}}
            return jsonify(ret)
        user_obj = Address(user_id=user_id, first_name=first_name, last_name=last_name, appellation=appellation, area=area,
                            city=city, district=district, place=place, mobile=mobile)
        db.session.add(user_obj)
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "增加成功"}}

        return jsonify(ret)
    else:
        data = request.json
        uid = data.get("id")
        user_obj = Address.query.filter_by(id=uid).first()
        user_obj.is_delete = 1
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
        return jsonify(ret)


# 最喜歡
@admin_api.route("/favorite", methods=["GET", "POST", "DELETE"])
@check_login
def favorite():
    method = request.method
    if method == "GET":
        user_id = request.args.get("user_id")
        page = request.args.get("page", 1)
        offset = request.args.get("offset", 5)
        if user_id:
            favorite_obj = Favorite.query.filter_by(user_id=user_id, delete_at=None).order_by(Favorite.id.desc()).limit(
                int(offset)).offset((int(page) - 1) * int(offset)).all()
            favorite_list = []
            for item in favorite_obj:
                item_dict = {}
                item_dict["user_id"] = item.user_id
                item_dict["id"] = item.id
                item_dict["product_id"] = item.product_id
                item_dict["favorite_product"] = {
                    "price": item.favorite_product.price,
                    "id": item.favorite_product.id,
                    "uuid": item.favorite_product.uuid,
                    "name": item.favorite_product.name,
                    "name_en": item.favorite_product.name_en,
                    "name_cn": item.favorite_product.name_cn,
                    "images": loads(Images.query.filter_by(watches_uuid=item.favorite_product.uuid).first())
                } # item.favorite_product.to_dict()
                favorite_list.append(item_dict)
            print(favorite_list)
            count = Favorite.query.filter_by(user_id=user_id, delete_at=None).count()
            ret = {"code": 200, "data": {"favorite_list": favorite_list, "count": count}}
            return jsonify(ret)
        else:
            return jsonify({"code": 4005, "data": {"msg": "缺少參數"}})
    elif method == "POST":
        data = request.json
        user_id = data.get("user_id")
        product_id = data.get("product_id")
        if not all([product_id, user_id]):
            ret = {"code": 1002, "data": {"msg": "缺少必傳參數"}}
            return jsonify(ret)
        is_obj = Favorite.query.filter_by(user_id=user_id, product_id=product_id).first()
        if not is_obj:
            user_obj = Favorite(user_id=user_id, product_id=product_id)
            db.session.add(user_obj)
            db.session.commit()
        ret = {"code": 200, "data": {"msg": "增加成功"}}
        return jsonify(ret)
    else:
        data = request.json
        uid = data.get("id")
        user_obj = Favorite.query.filter_by(id=uid).first()
        # user_obj.delete_at = datetime.datetime.now()
        if user_obj:
            db.session.delete(user_obj)
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
        return jsonify(ret)


# 購物車
@admin_api.route("/shoppingCar", methods=["GET", "POST", "PUT", "DELETE"])
@check_login
def shopping_car():
    method = request.method
    if method == "GET":
        user_id = request.args.get("user_id")
        page = request.args.get("page", 1)
        offset = request.args.get("offset", 5)
        id = request.args.get("id")
        if user_id:
            addr_obj = ShoppingCar.query.filter_by(user_id=user_id, delete_at=None).order_by(ShoppingCar.id.desc()).limit(
                int(offset)).offset((int(page) - 1) * int(offset)).all()
            addr_list = []
            for item in addr_obj:
                item_dict = {}
                item_dict["user_id"] = item.user_id
                item_dict["id"] = item.id
                item_dict["count"] = item.count
                item_dict["product_id"] = item.product_id
                item_dict["shopping_product"] = {
                    "price": item.shopping_product.price,
                    "id": item.shopping_product.id,
                    "uuid": item.shopping_product.uuid,
                    "name": item.shopping_product.name,
                    "name_en": item.shopping_product.name_en,
                    "name_cn": item.shopping_product.name_cn,
                    "images": loads(Images.query.filter_by(watches_uuid=item.shopping_product.uuid).first())
                } # item.shopping_product.to_dict()
                # item_dict["images"] = loads(Images.query.filter_by(watches_uuid=item.shopping_product.uuid).all())
                addr_list.append(item_dict)
            print(addr_list)
            count = ShoppingCar.query.filter_by(user_id=user_id, delete_at=None).count()
            ret = {"code": 200, "data": {"car_list": addr_list, "count": count}}
            return jsonify(ret)
        if id:
            addr_obj = ShoppingCar.query.filter_by(id=id, delete_at=None).first()
            if addr_obj:
                addr_list = {}
                addr_list["user_id"] = addr_obj.user_id
                addr_list["id"] = addr_obj.id
                addr_list["count"] = addr_obj.count
                addr_list["product_id"] = addr_obj.product_id
                addr_list["shopping_product"] = addr_obj.shopping_product.to_dict()
            else:
                addr_list = {}
            ret = {"code": 200, "data": addr_list}
            return jsonify(ret)
        else:
            return jsonify({"code": 4005, "data": {"msg": "缺少參數"}})
    elif method == "PUT":
        data = request.json
        uid = data.get("id")
        count = data.get("count")
        user_obj = ShoppingCar.query.filter_by(id=uid).first()
        user_obj.count = count
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
        return jsonify(ret)
    elif method == "POST":
        data = request.json
        user_id = data.get("user_id")
        product_id = data.get("product_id")
        count = data.get("count", 1)
        if not all([user_id, product_id, count]):
            ret = {"code": 1002, "data": {"msg": "缺少必傳參數"}}
            return jsonify(ret)
        user_obj = ShoppingCar.query.filter_by(user_id=user_id, product_id=product_id).first()
        if user_obj:
            user_obj.count += count
        else:
            user_obj = ShoppingCar(user_id=user_id, product_id=product_id, count=count)
        db.session.add(user_obj)
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "增加成功"}}

        return jsonify(ret)
    else:
        data = request.json
        uid = data.get("id")
        user_obj = ShoppingCar.query.filter_by(id=uid).first()
        if user_obj:
            # user_obj.delete_at = datetime.datetime.now()
            db.session.delete(user_obj)
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "刪除成功"}}
        return jsonify(ret)


# 品牌
@admin_api.route("/client/brand", methods=["GET"])
# @check_login
def client_brand():
    uid = request.args.get("uuid")
    offset = request.args.get("offset", 20)
    page = request.args.get("page", 1)
    search = request.args.get("search")  # 模糊查找
    category_uuid = request.args.get("category_uuid")
    if category_uuid:
        brand_obj_list = Brand.query.filter_by(category_uuid=category_uuid, delete_at=None).all()
        count = Brand.query.filter_by(category_uuid=category_uuid, delete_at=None).count()
        brand_list = []
        for brand_obj in brand_obj_list:
            item_dict = brand_obj.to_dict()
            item_dict["images"] = item_dict["images"] = loads(Images.query.filter_by(uuid=brand_obj.image_uuid).first())
            brand_list.append(item_dict)
        ret = {"code": 200, "data": {"brand_list": brand_list, "count": count}, "msg": "success"}
        return jsonify(ret)
    if search:
        brand_obj = Brand.query.filter(or_(Brand.name.like("%"+search+"%"), Brand.name_en.like("%"+search+"%"), Brand.name_cn.like("%"+search+"%"))).filter_by(delete_at=None).order_by(Brand.create_at.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
        brand_obj_count = Brand.query.filter(
            or_(Brand.name.like("%" + search + "%"), Brand.name_en.like("%" + search + "%"),
                Brand.name_cn.like("%" + search + "%"))).filter_by(delete_at=None).count()
        # brand_list = loads(brand_obj)
        brand_list = []
        for item in brand_obj:
            item_dict = item.to_dict()
            item_dict["images"] = loads(Images.query.filter_by(uuid=item.image_uuid).first())
            brand_list.append(item_dict)
        ret = {"code": 200, "data": {"brand_list": brand_list, "count": brand_obj_count}, "msg": "success"}
    else:
        if uid:
            brand_obj = Brand.query.filter_by(uuid=uid, delete_at=None).first()
            # brand_list = loads(brand_obj)
            brand_list = []
            if brand_obj:
                item_dict = brand_obj.to_dict()
                item_dict["images"] = item_dict["images"] = loads(Images.query.filter_by(uuid=brand_obj.image_uuid).first())
                brand_list.append(item_dict)
            ret = {"code": 200, "data": {"brand_list": brand_list}, "msg": "success"}
        else:
            brand_obj = Brand.query.filter_by(delete_at=None).order_by(Brand.create_at.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
            brand_count = Brand.query.filter_by(delete_at=None).count()
            brand_list = []
            for item in brand_obj:
                item_dict = item.to_dict()
                item_dict["images"] = loads(Images.query.filter_by(uuid=item.image_uuid).first())
                brand_list.append(item_dict)
            ret = {"code": 200, "data": {"brand_list": brand_list, "count": brand_count}, "msg": "success"}
    return jsonify(ret)


# 品牌
@admin_api.route("/brand", methods=["GET", "POST", "PUT", "DELETE"])
@check_admin
def brand():
    method = request.method
    if method == "GET":
        uid = request.args.get("uuid")
        offset = request.args.get("offset", 20)
        page = request.args.get("page", 1)
        search = request.args.get("search")  # 模糊查找
        category_uuid = request.args.get("category_uuid")
        if category_uuid:
            brand_obj_list = Brand.query.filter_by(category_uuid=category_uuid, delete_at=None).all()
            count = Brand.query.filter_by(category_uuid=category_uuid, delete_at=None).count()
            brand_list = []
            for brand_obj in brand_obj_list:
                item_dict = brand_obj.to_dict()
                item_dict["images"] = item_dict["images"] = loads(
                    Images.query.filter_by(uuid=brand_obj.image_uuid).first())
                brand_list.append(item_dict)
            ret = {"code": 200, "data": {"brand_list": brand_list, "count": count}, "msg": "success"}
            return jsonify(ret)
        if search:
            brand_obj = Brand.query.filter(or_(Brand.name.like("%"+search+"%"), Brand.name_en.like("%"+search+"%"), Brand.name_cn.like("%"+search+"%"))).filter_by(delete_at=None).order_by(Brand.create_at.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
            brand_obj_count = Brand.query.filter(
                or_(Brand.name.like("%" + search + "%"), Brand.name_en.like("%" + search + "%"),
                    Brand.name_cn.like("%" + search + "%"))).filter_by(delete_at=None).count()
            brand_list = []
            for item in brand_obj:
                item_dict = item.to_dict()
                item_dict["images"] = loads(Images.query.filter_by(uuid=item.image_uuid).first())
                brand_list.append(item_dict)
            ret = {"code": 200, "data": {"brand_list": brand_list, "count": brand_obj_count}, "msg": "success"}
        else:
            if uid:
                brand_obj = Brand.query.filter_by(uuid=uid, delete_at=None).first()
                brand_list = []
                if brand_obj:
                    item_dict = brand_obj.to_dict()
                    item_dict["images"] = loads(Images.query.filter_by(uuid=brand_obj.image_uuid).first())
                    brand_list.append(item_dict)
                ret = {"code": 200, "data": {"brand_list": brand_list}, "msg": "success"}
            else:
                brand_obj = Brand.query.filter_by(delete_at=None).order_by(Brand.create_at.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
                brand_count = Brand.query.filter_by(delete_at=None).count()
                brand_list = []
                for item in brand_obj:
                    item_dict = item.to_dict()
                    item_dict["images"] = loads(Images.query.filter_by(uuid=item.image_uuid).first())
                    brand_list.append(item_dict)
                ret = {"code": 200, "data": {"brand_list": brand_list, "count": brand_count}, "msg": "success"}
        return jsonify(ret)
    elif method == "PUT":
        data = request.json
        uid = data.get("uuid")
        name = data.get("name")
        name_en = data.get("name_en")
        name_cn = data.get("name_cn")
        detail = data.get("detail")
        image_uuid = data.get("image_uuid")
        count = data.get("count")
        brand_obj = Brand.query.filter_by(uuid=uid).first()
        brand_obj.name = name
        brand_obj.name_en = name_en
        brand_obj.name_cn = name_cn
        brand_obj.detail = detail
        brand_obj.image_uuid = image_uuid
        brand_obj.count = count
        brand_obj.update_at = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {}, "msg": "更改成功"}
        return jsonify(ret)
    elif method == "POST":
        data = request.json
        name = data.get("name")
        name_en = data.get("name_en")
        name_cn = data.get("name_cn")
        detail = data.get("detail")
        image_uuid = data.get("image_uuid")
        count = data.get("count", 100)
        if not all([name, name_en, name_cn, detail]):
            ret = {"code": 1002, "data": {}, "msg": "缺少必傳參數"}
            return jsonify(ret)
        str_uuid = uuid.uuid4().hex
        user_obj = Brand(uuid=str_uuid, name=name, count=count, image_uuid=image_uuid, name_en=name_en, name_cn=name_cn,detail=detail,
                            create_at=datetime.datetime.now())
        db.session.add(user_obj)
        db.session.commit()
        ret = {"code": 200, "data": str_uuid, "msg": "增加成功"}

        return jsonify(ret)
    else:
        data = request.json
        uid = data.get("uuid")
        user_obj = Brand.query.filter_by(uuid=uid).first()
        user_obj.delete_at = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {}, "msg": "刪除成功"}
        return jsonify(ret)


# 分類
@admin_api.route("/client/category", methods=["GET"])
# @check_login
def client_category():
    """
    訂單
    :return:
    """
    data = request.args
    offset = data.get("offset", 20)
    page = data.get("page", 1)
    search = data.get("search")
    if search:
        category_list = Category.query.filter(or_(Category.name.like("%"+search+"%"), Category.name_cn.like("%"+search+"%"), Category.name_en.like("%"+search+"%"))).filter_by(delete_at=None).order_by(Category.create_at.desc(), Category.id.desc()).offset((int(page)-1)*int(offset)).limit(int(offset)).all()
        count = Category.query.filter(or_(Category.name.like("%"+search+"%"), Category.name_cn.like("%"+search+"%"), Category.name_en.like("%"+search+"%"))).filter_by(delete_at=None).count()
        ret = {"code": 200, "data": {"category_list":loads(category_list), "count": count}, "msg": "success"}
    else:
        if data.get("uuid"):
            category_list = Category.query.filter_by(delete_at=None, uuid=data.get("uuid")).first()
            ret = {"code": 200, "data": {"category_list":loads(category_list)}, "msg": "success"}
        else:
            category_list = Category.query.filter_by(delete_at=None).order_by(Category.create_at.desc(), Category.id.desc()).offset((int(page)-1)*int(offset)).limit(int(offset)).all()
            count = Category.query.filter_by(delete_at=None).count()
            ret = {"code": 200, "data": {"category_list": loads(category_list), "count": count}, "msg": "success"}
    return jsonify(ret)



# 分類
@admin_api.route("/category", methods=["GET", "POST", "PUT", "DELETE"])
@check_admin
def category():
    """
    訂單
    :return:
    """
    method = request.method
    data = request.json
    if method == "GET":
        data = request.args
        offset = data.get("offset", 20)
        page = data.get("page", 1)
        search = data.get("search")
        if search:
            category_list = Category.query.filter(or_(Category.name.like("%"+search+"%"), Category.name_cn.like("%"+search+"%"), Category.name_en.like("%"+search+"%"))).filter_by(delete_at=None).order_by(Category.create_at.desc(), Category.id.desc()).offset((int(page)-1)*int(offset)).limit(int(offset)).all()
            count = Category.query.filter(or_(Category.name.like("%"+search+"%"), Category.name_cn.like("%"+search+"%"), Category.name_en.like("%"+search+"%"))).filter_by(delete_at=None).count()
            ret = {"code": 200, "data": {"category_list":loads(category_list), "count": count}, "msg": "success"}
        else:
            if data.get("uuid"):
                category_list = Category.query.filter_by(delete_at=None, uuid=data.get("uuid")).first()
                ret = {"code": 200, "data": {"category_list":loads(category_list)}, "msg": "success"}
            else:
                category_list = Category.query.filter_by(delete_at=None).order_by(Category.create_at.desc(), Category.id.desc()).offset((int(page)-1)*int(offset)).limit(int(offset)).all()
                count = Category.query.filter_by(delete_at=None).count()
                ret = {"code": 200, "data": {"category_list": loads(category_list), "count": count}, "msg": "success"}
        return jsonify(ret)
    elif method == "PUT":
        if data.get("uuid"):
            try:
                category_obj = Category.query.filter_by(delete_at=None, uuid=data.get("uuid")).first()
                # 更新订单
                category_obj.name = data.get("name")
                category_obj.name_cn = data.get("name_cn")
                category_obj.name_en = data.get("name_en")
                category_obj.detail = data.get("detail")
                category_obj.remark = data.get("remark")
                db.session.commit()
                ret = {"code": 200, "data": {}, "msg": "更改成功"}
            except Exception as e:
                ret = {"code": 1002, "data": {}, "msg": "參數異常"}
        else:
            ret = {"code": 1002, "data": {}, "msg": "更改失敗"}
        return jsonify(ret)
    elif method == "POST":
        if data:
            str_uuid = uuid.uuid4().hex
            try:
                category_obj = Category(uuid=str_uuid, name=data.get("name"), name_cn=data.get("name_cn"), name_en=data.get("name_en"), detail=data.get("detail"), create_at=datetime.datetime.now())
                db.session.add(category_obj)
                db.session.commit()
                ret = {"code": 200, "data": {}, "msg": "創建成功"}
            except Exception as e:
                db.session.rollback()
                print(e)
                ret = {"code": 1002, "data": {}, "msg": "創建網絡異常"}
        else:
            ret = {"code": 1002, "data": {}, "msg": "創建失敗"}
        return jsonify(ret)
    else:
        uid = data.get("uuid")
        if uid:
            category_obj = Category.query.filter_by(uuid=uid, delete_at=None).first()
            category_obj.delete_at = datetime.datetime.now()
            db.session.commit()
            ret = {"code": 200, "data": {}, "msg": "刪除成功"}
        else:
            ret = {"code": 1002, "data": {}, "msg": "刪除失敗"}
        return jsonify(ret)


# 產品
@admin_api.route("/client/watch", methods=["GET"])
# @check_login
def client_watch():
    """
    采購訂單
    :return:
    """
    data = request.args
    offset = data.get("offset", 20)
    page = data.get("page", 1)
    search = data.get("search")
    # url = "http://api.currencylayer.com/live?access_key=502b5f31ccef9c076feaaaf54c460e7d"
    # response = requests.get(url).json()
    # print(response)
    # quotes = response["quotes"]
    # quotes = {"USDHKD": 10, "USD": 1, "USDEUR": 0.9, "USDAUD": 2, "USDCNY": 6}
    with open("rate.json", "r", encoding="utf-8") as f:
        file = f.read()
    response = json.loads(file)
    quotes = response["quotes"]
    print(quotes)
    # 模糊查
    if search:
        water_obj = Watches.query.filter(or_(Watches.name.like("%" + search + "%"),
                                             Watches.name_en.like("%" + search + "%"), Watches.name_cn.like("%"+search+"%"))).filter_by(
            delete_at=None).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(
            int(offset)).all()
        # order_list = db.session(Watches, Images).query(Watches.uuid==Images.watches_uuid).filter(or_(Watches.name.like("%" + search + "%"),
        #                                      Watches.name_en.like("%" + search + "%"), Watches.name_cn.like("%"+search+"%"))).filter_by(
        #     delete_at=None).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(
        #     int(offset)).all()
        watch_list = []
        for item in water_obj:
            item_dict = item.to_dict()
            USD = item_dict["price"] / quotes["USDHKD"]
            item_dict["price_list"] = {"USD": USD, "USDEUR":USD * quotes["USDEUR"], "USDAUD": USD*quotes["USDAUD"], "USDCNY": USD*quotes["USDCNY"]}
            images = Images.query.filter_by(watches_uuid=item_dict["uuid"]).all()
            item_dict["images"] = loads(images)
            watch_list.append(item_dict)
        count = Watches.query.filter(or_(Watches.name.like("%" + search + "%"),
                                             Watches.name_en.like("%" + search + "%"), Watches.name_cn.like("%"+search+"%"))).filter_by(
            delete_at=None).count()
        ret = {"code": 200, "data": {"watch_list": watch_list, "count": count}, "msg": "success"}
        return jsonify(ret)
    else:
        if data.get("uuid"):
            # waters_list = Watches.query.filter_by(delete_at=None, uuid=data.get("uuid")).first()
            print(data.get("uuid"))
            waters_list = db.session.query(Watches, Brand, Category).filter(Brand.uuid==Watches.brand_uuid, Category.uuid==Watches.category_uuid).filter(Watches.uuid==data.get("uuid")).first()
            if waters_list:
                data_dict = waters_list[0].to_dict()
                USD = data_dict["price"] / quotes["USDHKD"]
                data_dict["price_list"] = {"USD": USD, "USDEUR": USD * quotes["USDEUR"],"USDAUD": USD * quotes["USDAUD"], "USDCNY": USD * quotes["USDCNY"]}
                images = Images.query.filter_by(watches_uuid=data_dict["uuid"]).all()
                data_dict["images"] = loads(images)
                data_dict["brand"] = waters_list[1].to_dict()
                # category = Category.query.filter_by(uuid=data_dict["category_uuid"]).first()
                data_dict["category"] = waters_list[2].to_dict()
                # 隨機獲取5個
                relate_data = Watches.query.filter_by(brand_uuid=waters_list[1].uuid).order_by(func.rand()).limit(5)
                relate_list = []
                for item in relate_data:
                    item_dict = item.to_dict()
                    images = Images.query.filter_by(watches_uuid=item_dict["uuid"]).all()
                    item_dict["images"] = loads(images)
                    relate_list.append(item_dict)
                ret = {"code": 200, "data": data_dict, "relate_data": relate_list, "msg": "success"}
            else:
                ret = {"code": 200, "data": [], "msg": "无此商品"}
        elif data.get("brand_uuid"):
            water_list = Watches.query.filter_by(delete_at=None, brand_uuid=data.get("brand_uuid")).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(int(offset)).all()
            count = Watches.query.filter_by(delete_at=None, brand_uuid=data.get("brand_uuid")).count()
            data_list = []
            for item in water_list:
                water_dict = item.to_dict()
                USD = water_dict["price"] / quotes["USDHKD"]
                water_dict["price_list"] = {"USD": USD, "USDEUR": USD * quotes["USDEUR"],"USDAUD": USD * quotes["USDAUD"], "USDCNY": USD * quotes["USDCNY"]}
                images = Images.query.filter_by(watches_uuid=water_dict["uuid"]).all()
                water_dict["images"] = loads(images)
                data_list.append(water_dict)
            ret = {"code": 200, "data": {"watch_list": data_list, "count": count}, "msg": "success" }
        elif data.get("category_uuid"):
            water_list = Watches.query.filter_by(delete_at=None, category_uuid=data.get("category_uuid")).order_by(Watches.create_at.desc(),Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(int(offset)).all()
            # water_list = db.session.query(Watches, Images).query(Watches.uuid == Images.watches_uuid).filter(Watches.delete_at==None, Watches.brand_uuid==data.get("brand_uuid")).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(int(offset)).all()
            count = Watches.query.filter_by(delete_at=None, category_uuid=data.get("category_uuid")).count()
            data_list = []
            for item in water_list:
                water_dict = item.to_dict()
                USD = water_dict["price"] / quotes["USDHKD"]
                water_dict["price_list"] = {"USD": USD, "USDEUR": USD * quotes["USDEUR"],"USDAUD": USD * quotes["USDAUD"], "USDCNY": USD * quotes["USDCNY"]}
                images = Images.query.filter_by(watches_uuid=water_dict["uuid"]).all()
                water_dict["images"] = loads(images)
                data_list.append(water_dict)
            ret = {"code": 200, "data": {"watch_list": data_list, "count": count}, "msg": "success"}
        else:
            water_list = Watches.query.filter_by(delete_at=None).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page)-1)*int(offset)).limit(int(offset)).all()
            count = Watches.query.filter_by(delete_at=None).count()
            data_list = []
            for item in water_list:
                water_dict = item.to_dict()
                USD = water_dict["price"] / quotes["USDHKD"]
                water_dict["price_list"] = {"USD": USD, "USDEUR": USD * quotes["USDEUR"], "USDAUD": USD * quotes["USDAUD"], "USDCNY": USD * quotes["USDCNY"]}
                images = Images.query.filter_by(watches_uuid=water_dict["uuid"]).all()
                water_dict["images"] = loads(images)
                data_list.append(water_dict)
            ret = {"code": 200, "data": {"watch_list":data_list, "count": count}, "msg": "success"}
        return jsonify(ret)


# 產品
@admin_api.route("/watch", methods=["GET", "POST", "PUT", "DELETE"])
@check_admin
def watch():
    """
    采購訂單
    :return:
    """
    method = request.method
    data = request.json
    if method == "GET":
        data = request.args
        offset = data.get("offset", 20)
        page = data.get("page", 1)
        search = data.get("search")
        # url = "http://api.currencylayer.com/live?access_key=502b5f31ccef9c076feaaaf54c460e7d"
        # response = requests.get(url).json()
        # quotes = response["quotes"]
        # quotes = {"USDHKD": 10, "USD": 1, "USDEUR": 0.9, "USDAUD": 2, "USDCNY": 6}
        with open("rate.json", "r", encoding="utf-8") as f:
            file = f.read()
        response = json.loads(file)
        quotes = response["quotes"]
        print(quotes)
        # 模糊查
        if search:
            water_obj = Watches.query.filter(or_(Watches.name.like("%" + search + "%"),
                                                 Watches.name_en.like("%" + search + "%"), Watches.name_cn.like("%"+search+"%"))).filter_by(
                delete_at=None).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(
                int(offset)).all()
            # order_list = db.session(Watches, Images).query(Watches.uuid==Images.watches_uuid).filter(or_(Watches.name.like("%" + search + "%"),
            #                                      Watches.name_en.like("%" + search + "%"), Watches.name_cn.like("%"+search+"%"))).filter_by(
            #     delete_at=None).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(
            #     int(offset)).all()
            watch_list = []
            for item in water_obj:
                item_dict = item.to_dict()
                USD = item_dict["price"] / quotes["USDHKD"]
                item_dict["price_list"] = {"USD": USD, "USDEUR":USD * quotes["USDEUR"], "USDAUD": USD*quotes["USDAUD"], "USDCNY": USD*quotes["USDCNY"]}
                images = Images.query.filter_by(watches_uuid=item_dict["uuid"]).all()
                item_dict["images"] = loads(images)
                watch_list.append(item_dict)
            count = Watches.query.filter(or_(Watches.name.like("%" + search + "%"),
                                                 Watches.name_en.like("%" + search + "%"), Watches.name_cn.like("%"+search+"%"))).filter_by(
                delete_at=None).count()
            ret = {"code": 200, "data": {"watch_list": watch_list, "count": count}, "msg": "success"}
            return jsonify(ret)
        else:
            if data.get("uuid"):
                # waters_list = Watches.query.filter_by(delete_at=None, uuid=data.get("uuid")).first()
                print(data.get("uuid"))
                waters_list = db.session.query(Watches, Brand, Category).filter(Brand.uuid==Watches.brand_uuid, Category.uuid==Watches.category_uuid).filter(Watches.uuid==data.get("uuid")).first()
                if waters_list:
                    data_dict = waters_list[0].to_dict()
                    USD = data_dict["price"] / quotes["USDHKD"]
                    data_dict["price_list"] = {"USD": USD, "USDEUR": USD * quotes["USDEUR"],"USDAUD": USD * quotes["USDAUD"], "USDCNY": USD * quotes["USDCNY"]}
                    images = Images.query.filter_by(watches_uuid=data_dict["uuid"]).all()
                    data_dict["images"] = loads(images)
                    data_dict["brand"] = waters_list[1].to_dict()
                    # category = Category.query.filter_by(uuid=data_dict["category_uuid"]).first()
                    data_dict["category"] = waters_list[2].to_dict()
                    # 隨機獲取5個
                    relate_data = Watches.query.filter_by(brand_uuid=waters_list[1].uuid).order_by(func.rand()).limit(5)
                    relate_list = []
                    for item in relate_data:
                        item_dict = item.to_dict()
                        images = Images.query.filter_by(watches_uuid=item_dict["uuid"]).all()
                        item_dict["images"] = loads(images)
                        relate_list.append(item_dict)
                    ret = {"code": 200, "data": data_dict, "relate_data": relate_list, "msg": "success"}
                else:
                    ret = {"code": 200, "data": [], "msg": "无此商品"}
            elif data.get("brand_uuid"):
                water_list = Watches.query.filter_by(delete_at=None, brand_uuid=data.get("brand_uuid")).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(int(offset)).all()
                count = Watches.query.filter_by(delete_at=None, brand_uuid=data.get("brand_uuid")).count()
                data_list = []
                for item in water_list:
                    water_dict = item.to_dict()
                    USD = water_dict["price"] / quotes["USDHKD"]
                    water_dict["price_list"] = {"USD": USD, "USDEUR": USD * quotes["USDEUR"],"USDAUD": USD * quotes["USDAUD"], "USDCNY": USD * quotes["USDCNY"]}
                    images = Images.query.filter_by(watches_uuid=water_dict["uuid"]).all()
                    water_dict["images"] = loads(images)
                    data_list.append(water_dict)
                ret = {"code": 200, "data": {"watch_list": data_list, "count": count}, "msg": "success" }
            elif data.get("category_uuid"):
                water_list = Watches.query.filter_by(delete_at=None, category_uuid=data.get("category_uuid")).order_by(Watches.create_at.desc(),Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(int(offset)).all()
                # water_list = db.session.query(Watches, Images).query(Watches.uuid == Images.watches_uuid).filter(Watches.delete_at==None, Watches.brand_uuid==data.get("brand_uuid")).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(int(offset)).all()
                count = Watches.query.filter_by(delete_at=None, category_uuid=data.get("category_uuid")).count()
                data_list = []
                for item in water_list:
                    water_dict = item.to_dict()
                    USD = water_dict["price"] / quotes["USDHKD"]
                    water_dict["price_list"] = {"USD": USD, "USDEUR": USD * quotes["USDEUR"],"USDAUD": USD * quotes["USDAUD"], "USDCNY": USD * quotes["USDCNY"]}
                    images = Images.query.filter_by(watches_uuid=water_dict["uuid"]).all()
                    water_dict["images"] = loads(images)
                    data_list.append(water_dict)
                ret = {"code": 200, "data": {"watch_list": data_list, "count": count}, "msg": "success"}
            else:
                water_list = Watches.query.filter_by(delete_at=None).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page)-1)*int(offset)).limit(int(offset)).all()
                count = Watches.query.filter_by(delete_at=None).count()
                data_list = []
                for item in water_list:
                    water_dict = item.to_dict()
                    USD = water_dict["price"] / quotes["USDHKD"]
                    water_dict["price_list"] = {"USD": USD, "USDEUR": USD * quotes["USDEUR"], "USDAUD": USD * quotes["USDAUD"], "USDCNY": USD * quotes["USDCNY"]}
                    images = Images.query.filter_by(watches_uuid=water_dict["uuid"]).all()
                    water_dict["images"] = loads(images)
                    data_list.append(water_dict)
                ret = {"code": 200, "data": {"watch_list":data_list, "count": count}, "msg": "success"}
            return jsonify(ret)
    elif method == "PUT":
        if data.get("uuid"):
            watch_obj = Watches.query.filter_by(delete_at=None, uuid=data.get("uuid")).first()
            watch_obj.category_uuid = data.get("category_uuid")
            watch_obj.brand_uuid = data.get("brand_uuid")
            watch_obj.name = data.get("name")
            watch_obj.name_en = data.get("name_en")
            watch_obj.name_cn = data.get("name_cn")
            watch_obj.series = data.get("series")
            watch_obj.series_cn = data.get("series_cn")
            watch_obj.series_en = data.get("series_en")
            watch_obj.weight = data.get("weight")
            watch_obj.shipping_weight = data.get("shipping_weight")
            watch_obj.model = data.get("model")
            watch_obj.movement = data.get("movement")
            watch_obj.power_reserve = data.get("power_reserve")
            watch_obj.case_thickness = data.get("case_thickness")

            watch_obj.case_material = data.get("case_material")
            watch_obj.case_material_resistance = data.get("case_material_resistance")
            watch_obj.dial_color = data.get("dial_color")
            watch_obj.dial_material = data.get("dial_material")
            watch_obj.strap_color = data.get("strap_color")
            watch_obj.strap_material = data.get("strap_material")
            watch_obj.case_material = data.get("case_material")

            watch_obj.water_resistant = data.get("water_resistant")
            watch_obj.annex = data.get("annex")
            watch_obj.clasp_type = data.get("clasp_type")
            watch_obj.update_at = datetime.datetime.now()
            watch_obj.price = data.get("price")
            watch_obj.detail = data.get("detail")
            watch_obj.status = data.get("status")
            db.session.commit()
            ret = {"code": 200, "data": {}, "msg": "更改成功"}
        else:
            ret = {"code": 1002, "data": {}, "msg": "更改失敗"}
        return jsonify(ret)
    elif method == "POST":
        if data:
            str_uuid = uuid.uuid4().hex
            watch_obj = Watches(uuid=str_uuid, price=data.get("price"), category_uuid=data.get("category_uuid"),
                                brand_uuid=data.get("brand_uuid"), name=data.get("name"),
                                name_en=data.get("name_en"), name_cn=data.get("name_cn"),
                                series=data.get("series"), series_cn=data.get("series_cn"),
                                series_en=data.get("series_en"), weight=data.get("weight"),
                                shipping_weight=data.get("shipping_weight"), model=data.get("model"),
                                movement=data.get("movement"), power_reserve=data.get("power_reserve"),
                                case_diameter=data.get("case_diameter"), case_thickness=data.get("case_thickness"),
                                case_material=data.get("case_material"), case_material_resistance=data.get("case_material_resistance"),
                                dial_color=data.get("dial_color"), dial_material=data.get("dial_material"),
                                strap_color=data.get("strap_color"), strap_material=data.get("strap_material"),
                                water_resistant=data.get("water_resistant"), annex=data.get("annex"), status=data.get("status"),
                                clasp_type=data.get("clasp_type"), create_at=datetime.datetime.now(),detail=data.get("detail"))
            db.session.add(watch_obj)
            db.session.commit()
            ret = {"code": 200, "data": {"uuid": str_uuid}, "msg": "創建成功"}
        else:
            ret = {"code": 1002, "data": {}, "msg": "創建失敗"}
        return jsonify(ret)
    else:
        uid = data.get("uuid")
        if uid:
            watch_obj = Watches.query.filter_by(uuid=uid).first()
            watch_obj.delete_at = datetime.datetime.now()
            db.session.commit()
            ret = {"code": 200, "data": {}, "msg": "刪除成功"}
        else:
            ret = {"code": 1002, "data": {}, "msg": "刪除失敗"}
        return jsonify(ret)

# 模糊搜索
@admin_api.route("/search/watch", methods=["GET"])
# @check_login
def search():
    """
    采購訂單
    :return:
    """

    data = request.args
    offset = data.get("offset", 20)
    page = data.get("page", 1)
    searchs = data.get("keywords")
    search = data.get("keyword")

    # 模糊查
    if searchs:
        # url = "http://api.currencylayer.com/live?access_key=502b5f31ccef9c076feaaaf54c460e7d"
        # response = requests.get(url).json()
        # quotes = response["quotes"]
        with open("rate.json", "r", encoding="utf-8") as f:
            file = f.read()
        response = json.loads(file)
        quotes = response["quotes"]
        # quotes = {"USDHKD": 10, "USD": 1, "USDEUR": 0.9, "USDAUD": 2, "USDCNY": 6}
        #print(quotes)
        water_obj = Watches.query.filter(or_(Watches.model.like("%"+searchs+"%"),Watches.name.like("%" + searchs + "%"),
                                             Watches.name_en.like("%" + searchs + "%"), Watches.name_cn.like("%"+searchs+"%"))).filter_by(
            delete_at=None).order_by(Watches.create_at.desc(), Watches.id.desc()).offset((int(page) - 1) * int(offset)).limit(
            int(offset)).all()
        watch_list = []
        for item in water_obj:
            item_dict = item.to_dict()
            USD = item_dict["price"] / quotes["USDHKD"]
            item_dict["price_list"] = {"USD": USD, "USDEUR":USD * quotes["USDEUR"], "USDAUD": USD*quotes["USDAUD"], "USDCNY": USD*quotes["USDCNY"]}
            images = Images.query.filter_by(watches_uuid=item_dict["uuid"]).all()
            item_dict["images"] = loads(images)
            watch_list.append(item_dict)
        count = Watches.query.filter(or_(Watches.model.like("%"+searchs+"%"), Watches.name.like("%" + searchs + "%"),
                                             Watches.name_en.like("%" + searchs + "%"), Watches.name_cn.like("%"+searchs+"%"))).filter_by(
            delete_at=None).count()
        ret = {"code": 200, "data": {"watch_list": watch_list, "count": count}, "msg": "success"}
        return jsonify(ret)

    if search:
        # water_obj = db.session.query(Watches, Brand, Category).filter(Watches.brand_uuid == Brand.uuid,
        #                                                               Watches.category_uuid == Category.uuid).filter(
        #     or_(Watches.name.like("%" + search + "%"), Watches.name_en.like("%" + search + "%"),
        #         Watches.name_cn.like("%" + search + "%"), Category.name.like("%" + search + "%"),
        #         Category.name_en.like("%" + search + "%"), Category.name_cn.like("%" + search + "%"),
        #         Brand.name.like("%" + search + "%"), Brand.name_en.like("%" + search + "%"),
        #         Brand.name_cn.like("%" + search + "%"))).filter_by(
        #     delete_at=None).order_by(Watches.create_at.desc(), Watches.id.desc()).offset(
        #     (int(page) - 1) * int(offset)).limit(
        #     int(offset)).all()
        water_obj = Watches.query.filter(or_(Watches.model.like("%"+search+"%"), Watches.name.like("%" + search + "%"),
                                             Watches.name_en.like("%" + search + "%"),
                                             Watches.name_cn.like("%" + search + "%"))).filter_by(
            delete_at=None).order_by(Watches.create_at.desc(), Watches.id.desc()).offset(
            (int(page) - 1) * int(offset)).limit(
            int(offset)).all()
        ProductNamesList = []
        ProductNamesListDict = []
        for one_res in water_obj:
            if one_res.name not in ProductNamesList:
                ProductNamesList.append(one_res.name)
                ProductNamesListDict.append(
                    {"name": one_res.name, "id": one_res.id, "uuid": one_res.uuid, "status": 1})

        result = {"data": ProductNamesListDict}
        return jsonify(result)


# 上傳圖片
@admin_api.route("/image", methods=["GET", "POST", "PUT", "DELETE"])
@check_admin
def upload():
    """
    上傳圖片
    :return:
    """
    method = request.method
    if method == "GET":
        uid = request.args.get("uuid")
        watches_uuid = request.args.get("watches_uuid")
        page = request.args.get("page", 1)
        offset = request.args.get("offset", 20)
        if uid:
            image = Images.query.filter_by(uuid=uid).first()
            ret = {"code": 200, "data": {"image_list":loads(image)}, "msg": "查询成功"}
        else:
            if watches_uuid:
                image = Images.query.filter_by(watches_uuid=watches_uuid).all()
                ret = {"code": 200, "data": {"image_list":loads(image)}, "msg": "查询成功"}
            else:
                image = Images.query.limit(offset).offset((int(page)-1)*int(offset)).all()
                count = Images.query.count()
                ret = {"code": 200, "data": {"image_list":loads(image), "count": count}, "msg": "查询成功"}
        return jsonify(ret)
    elif method == "POST":
        image = request.files.get("file")
        uid = request.form.get("watches_uuid")
        print(uid)
        # image_name = request.form.get("image_name")
        try:
            size = len(image.read())
            if size >= 5*1024*1024:
                data = {"code": 1001, "data": {"msg": "請上轉圖片小於3M"}}
                return jsonify(data)
            str_uid = uuid.uuid4().hex
            filename = str_uid + "." + image.filename.split(".")[-1]
            upload_path = os.path.join(os.path.abspath("static"), IMG_PATH, filename)
            try:
                image.seek(0)
                image.save(upload_path)
                img_obj = Images(uuid=str_uid, watches_uuid=uid, image_name=filename, full_path=upload_path, create_at=datetime.datetime.now())
                db.session.add(img_obj)
                db.session.commit()
                data = {"code": 200, "data": loads(img_obj), "msg": "上傳成功"}
                return jsonify(data)
            except Exception as e:
                print(e)
                data = {"code": 1002, "msg": "上傳失敗"}
                return jsonify(data)
        except Exception as e:
            data = {"code": 1002, "msg": "上傳失敗"}
        return jsonify(data)
    elif method == "PUT":
        data = request.json
        img_obj = Images.query.filter_by(uuid=data.get("uuid")).first()
        img_obj.watches_uuid = data.get("watches_uuid"),
        img_obj.image_name = data.get("image_name"),
        img_obj.full_path = data.get("full_path"),
        img_obj.update_at = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "msg": "更改成功"}
        return jsonify(ret)
    else:
        data = request.json
        img_obj = Images.query.filter_by(uuid=data.get("uuid"))
        if img_obj:
            try:
                full_path = img_obj.first().full_path
                os.remove(full_path)
                img_obj.delete()
                db.session.commit()
                ret = {"code": 200, "msg": "删除成功"}
            except:
                ret = {"code": 4002, "msg": "删除失敗"}
        else:
            ret = {"code": 4003, "msg": "文件不存在"}

        return jsonify(ret)


# 获取支付token
@admin_api.route('/get/token', methods=['GET'])
@check_login
def get_pay_token():
    data = request.args
    methods = data.get("methods")
    # user_id = g.user_id
    if methods == "braintree":
        # client_token 返回付款的token
        customer_id = data.get("customer_id") if data else None
        # 如果没有customer_id到数据库中查找该用户是否存在customer_id 存在就直接用
        token = client_token(customer_id)
        return jsonify({"code": "200", "token": token, "message": "success"})
    elif methods == "stripe":
        card_list = []
        data = {"code": "200", "token": PUB_KEY, "cart_list": card_list}
        return jsonify(data)
    else:
        return jsonify({"code": "200", "token": client_token, "message": "success"})

# 支付
@admin_api.route("/pay", methods=["POST"])
@check_login
def pay():
    """
    支付
    :return:
    """
    data_json = request.json
    methods = data_json.get("methods")
    payment_method_nonce = data_json.get("payment_method_nonce")
    token = data_json.get("token")
    product_list = data_json.get("product")  # 數組 [[1, 2]]
    user_id = data_json.get("user_id")
    address = data_json.get("address_id", 1)
    booking_time = data_json.get("booking_time")
    total = 0
    order_num = "WAS" + str(int(time.time()))
    desc_list = "[Watch]"+order_num+" "
    data_msg = ""
    product_detail_list = []
    print(product_list)
    for item in product_list:
        wat = Watches.query.filter(Watches.id==item[0]).first()
        if wat.status == 1:
            return jsonify({"code": 2002, "data": {"msg": wat.name+" 該產品不需要付定金"}})
        images = Images.query.filter_by(watches_uuid=wat.uuid).all()
        if wat.store < item[1]:
            return jsonify({"code": 2001, "data": {"msg": wat.name+"庫產不足"}})
        product_detail_list.append({"product_name": wat.name, "product_image": loads(images), "product_price": wat.price, "product_number": item[1], "product_id": wat.id, "total": wat.price * item[1]})
        desc_list += wat.name + "|"
        total += wat.price * item[1]

    is_pay = False
    if is_pay == False:
        j = 0
        # 支付不成功 不下执行 重试5次
        while j < 5:
            if methods == "braintree":
                result = third_pay(str(rate/100*total), payment_method_nonce, data_msg)
                if result != True:
                    error_msg = result
                else:
                    is_pay = True
                    break
            elif methods == "stripe":
                print(total, data_msg, token, desc_list)
                result = create_purchase(rate/100*total,"hkd",data_msg,token,"".join(desc_list),  # 這個之後就是根據買什麼產品放產品名字 數量  放進去
                    # receipt_email ="abc@gmail.com [客戶電郵]",  #發送一個收條
                )
                if result != "succeeded":
                    pass
                else:
                    is_pay = True
                    break
            if result != True or result != "succeeded":
                pass
            else:
                is_pay = True
                break
            j += 1
        # 循环5次退出后 判断是否支付成功
        if is_pay != True:
            result = {"code": 601, "msg": "支付超時"}
            return jsonify(result)
    # order_num = "WAS"+str(int(time.time()))
    uid = uuid.uuid4().hex
    # 建立訂單
    order_obj = Orders(uuid=uid, order_num=order_num, booking_time=booking_time, deposit=rate/100*total, total=total, pay_methods=methods, status=1, user_id=user_id, create_at=datetime.datetime.now())
    orm_list = []
    orm_list.append(order_obj)
    for item in product_detail_list:
        print(item)
        # 減庫存
        wa_obj = Watches.query.filter_by(id=item["product_id"]).first()
        wa_obj.store = wa_obj.store - item["product_number"]
        orm_list.append(wa_obj)
        # 增加詳情
        obj = OrderDetail(order_id=order_num, product_name=item["product_name"], product_image=json.dumps(item["product_image"]), product_price=item["product_price"], product_number=item["product_number"], total=item["total"], product_id=item["product_id"])
        orm_list.append(obj)
        user_obj = UserInfo.query.filter_by(id=user_id).first()
        template = TEMPLATE.format(order_num, booking_time, BASE_URL+item["product_image"][0]["image_name"], item["product_name"], rate/100*total, total)
        sender_email([user_obj.email], template)
        # 刪除購物車
        # car_obj = ShoppingCar.query.filter_by(user_id=user_id, product_id=item["product_id"]).first()
        # if car_obj:
        #     db.session.delete(car_obj)
    db.session.add_all(orm_list)
    db.session.commit()
    db.session.close()
    return {"code": 200, "data": {"order_num": order_num, "msg": "支付成功"}}


# 计算价格
@admin_api.route("/compute/price", methods=["POST"])
def compute_price():
    data_json = request.json
    product_list = data_json.get("product")  # 數組 [[1, 2]]
    total = 0
    print(product_list)
    for item in product_list:
        wat = Watches.query.filter(Watches.id == item[0]).first()
        if wat:
            if wat.store < item[1]:
                return jsonify({"code": 2001, "data": {"msg": wat.name + "庫產不足"}})
            total += wat.price * item[1]
    ret = {"code": 200, "data": {"total": total, "deposit": rate/100*total}}
    return jsonify(ret)

# 普通用戶查看訂單
@admin_api.route("/client/order", methods=["GET"])
@check_login
def client_order():
    data = request.args
    offset = data.get("offset", 20)
    page = data.get("page", 1)
    search = data.get("search")
    user_id = data.get("user_id")
    if search:
        # order_list = Orders.query.filter(Orders.user_id==user_id).filter(
        #     or_(Orders.order_num.like("%" + search + "%"), Orders.name.like("%" + search + "%"))).filter_by(
        #     delete_at=None).order_by(Orders.create_at.desc(), Orders.id.desc()).offset(
        #     (int(page) - 1) * int(offset)).limit(int(offset)).all()
        order_list = db.session.query(Orders, OrderDetail).filter(Orders.order_num==OrderDetail.order_id).filter(Orders.user_id == user_id).filter(
            or_(Orders.order_num.like("%" + search + "%"))).filter_by(
            delete_at=None).order_by(Orders.create_at.desc(), Orders.id.desc()).offset(
            (int(page) - 1) * int(offset)).limit(int(offset)).all()
        order_lists = []
        for item in order_list:
            item_dict = item[0].to_dict()
            item_dict["detail"] = item[1].to_dict()
            order_lists.append(item_dict)
        count = Orders.query.filter(Orders.user_id==user_id).filter_by(delete_at=None).filter(
            or_(Orders.order_num.like("%" + search + "%"))).count()
        ret = {"code": 200, "data": order_lists, "count": count}
    else:
        if data.get("order_num"):
            order_obj = Orders.query.filter(Orders.user_id==user_id).filter_by(delete_at=None, order_num=data.get("order_num")).first()
            order_data = order_obj.to_dict()
            order_detail = OrderDetail.query.filter_by(order_id=order_obj.order_num).all()
            order_data["detail"] = loads(order_detail)
            # order_address = Address.query.filter_by(id=order_obj.address_id).all()
            # order_data["address"] = loads(order_address)
            ret = {"code": 200, "data": order_data}
        else:
            # order_list = Orders.query.filter(Orders.user_id==user_id).filter_by(delete_at=None).order_by(Orders.create_at.desc(),
            #                                                              Orders.id.desc()).offset(
            #     (int(page) - 1) * int(offset)).limit(int(offset)).all()
            order_list = db.session.query(Orders, OrderDetail).filter(Orders.order_num==OrderDetail.order_id).filter(Orders.user_id == user_id).filter_by(delete_at=None).order_by(
                Orders.create_at.desc(),
                Orders.id.desc()).offset(
                (int(page) - 1) * int(offset)).limit(int(offset)).all()
            order_lists = []
            for item in order_list:
                item_dict = item[0].to_dict()
                item_dict["detail"] = item[1].to_dict()
                order_lists.append(item_dict)
            count = Orders.query.filter(Orders.user_id==user_id).filter_by(delete_at=None).count()
            ret = {"code": 200, "data": order_lists, "count": count}
    return jsonify(ret)


# 管理員查看訂單
@admin_api.route("/order", methods=["GET", "POST", "PUT", "DELETE"])
@check_admin
def order():
    """
    訂單
    :return:
    """
    method = request.method
    if method == "GET":
        data = request.args
        offset = data.get("offset", 20)
        page = data.get("page", 1)
        search = data.get("search")
        if search:
            order_list = db.session.query(Orders, OrderDetail).filter(Orders.order_num == OrderDetail.order_id).filter(or_(Orders.order_num.like("%"+search+"%"))).filter_by(delete_at=None).order_by(Orders.create_at.desc(), Orders.id.desc()).offset((int(page)-1)*int(offset)).limit(int(offset)).all()
            count = Orders.query.filter(or_(Orders.order_num.like("%"+search+"%"))).filter_by(delete_at=None).count()
            order_lists = []
            for item in order_list:
                item_dict = item[0].to_dict()
                item_dict["detail"] = item[1].to_dict()
                order_lists.append(item_dict)
            ret = {"code": 200, "data": order_lists, "count": count}
        else:
            if data.get("order_num"):
                order_obj = Orders.query.filter_by(delete_at=None, order_num=data.get("order_num")).first()
                order_data = order_obj.to_dict()
                order_detail = OrderDetail.query.filter_by(order_id=order_obj.order_num).all()
                order_data["detail"] = loads(order_detail)
                # order_address = Address.query.filter_by(id=order_obj.address_id).all()
                # order_data["address"] = loads(order_address)
                ret = {"code": 200, "data": order_data}
            else:
                order_list = db.session.query(Orders, OrderDetail).filter(Orders.order_num == OrderDetail.order_id).filter_by(delete_at=None).order_by(Orders.create_at.desc(), Orders.id.desc()).offset((int(page)-1)*int(offset)).limit(int(offset)).all()
                order_lists = []
                for item in order_list:
                    item_dict = item[0].to_dict()
                    item_dict["detail"] = item[1].to_dict()
                    order_lists.append(item_dict)
                count = Orders.query.filter_by(delete_at=None).count()
                ret = {"code": 200, "data": order_lists, "count": count}
        return jsonify(ret)
    elif method == "PUT":
        # 取消訂單  返還數量
        json_data = request.json
        uid = json_data.get("uuid")
        status = json_data.get("status")
        orm_list = []
        order_obj = Orders.query.filter_by(uuid=uid).first()
        order_obj.status = status
        orm_list.append(order_obj)
        order_list = OrderDetail.query.filter_by(order_id=order_obj.order_num).all()
        for item in order_list:
            wat_obj = Watches.query.filter_by(id=item.product_id).first()
            wat_obj.store = wat_obj.store + item.product_number
            orm_list.append(wat_obj)
        db.session.add_all(orm_list)
        db.session.commit()
        db.session.close()
        return {"code": 200, "data": {"msg": "訂單取消成功"}}
    elif method == "POST":
        data_json = request.json
        product_list = data_json.get("product")  # 數組 [[1, 2]]
        user_id = data_json.get("user_id")
        product_detail_list = []
        total = 0
        print(product_list)
        for item in product_list:
            wat = Watches.query.filter(Watches.id == item[0]).first()
            images = Images.query.filter_by(watches_uuid=wat.uuid).all()
            if wat.store < item[1]:
                return jsonify({"code": 2001, "data": {"msg": wat.name + "庫產不足"}})
            product_detail_list.append(
                {"product_name": wat.name, "product_image": loads(images), "product_price": wat.price,
                 "product_number": item[1], "product_id": wat.id, "total": wat.price * item[1]})
            total +=  wat.price * item[1]
        order_num = "WAS" + str(int(time.time()))
        uid = uuid.uuid4().hex
        # 建立訂單
        order_obj = Orders(uuid=uid, order_num=order_num, deposit=rate / 100 * total, total=total, pay_methods="stripe",
                           status=1, user_id=user_id,  create_at=datetime.datetime.now())
        orm_list = []
        orm_list.append(order_obj)
        for item in product_detail_list:
            print(item)
            # 減庫存
            wa_obj = Watches.query.filter_by(id=item["product_id"]).first()
            wa_obj.store = wa_obj.store - item["product_number"]
            orm_list.append(wa_obj)
            # 增加詳情
            obj = OrderDetail(order_id=order_num, product_name=item["product_name"],
                              product_image=json.dumps(item["product_image"]), product_price=item["product_price"],
                              product_number=item["product_number"], total=item["total"], product_id=item["product_id"])
            orm_list.append(obj)
            # 刪除購物車
            # car_obj = ShoppingCar.query.filter_by(user_id=user_id, water_id=item["product_id"]).first()
            # car_obj.delete_at = datetime.datetime.now()
            # orm_list.append(car_obj)
        db.session.add_all(orm_list)
        db.session.commit()
        db.session.close()
        return {"code": 200, "data": {"order_num": order_num, "msg": "创建订单成功"}}
    else:
        # 取消訂單  返還數量
        json_data = request.json
        uid = json_data.get("uuid")
        status = json_data.get("status")
        orm_list = []
        order_obj = Orders.query.filter_by(uuid=uid).first()
        order_obj.delete_at = datetime.datetime.now()
        db.session.commit()
        db.session.close()
        return {"code": 200, "data": {"msg": "訂單取消成功"}}



# 管理端更新配置
@admin_api.route("/setting", methods=["GET", "PUT"])
@check_admin
def settings():
    """
    訂單
    :return:
    """
    method = request.method
    if method == "GET":
        with open("data.json", "r") as f:
            file = eval(f.read())
        return jsonify({"code": 200, "data": file})
    else:
        # 取消訂單  返還數量
        json_data = request.json
        ADMIN_TIMEOUT = json_data.get("admin_timeout", 3)
        CLIENT_TIMEOUT = json_data.get("client_timeout", 3)
        rates = json_data.get("rate", 10)
        global rate
        import setting
        setattr(setting, "ADMIN_TIMEOUT", ADMIN_TIMEOUT)
        setattr(setting, "CLIENT_TIMEOUT", CLIENT_TIMEOUT)
        rate = rates
        content = {"admin_timeout": ADMIN_TIMEOUT, "client_timeout": CLIENT_TIMEOUT, "rate": rate}
        with open("data.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(content, ensure_ascii=False))
        return jsonify({"code": 200, "data": {"msg": "更改成功"}})


# 統計數量
@admin_api.route("/statistics/count", methods=["GET"])
@check_admin
def statistics_count():
    category_uuid = request.args.get("category_uuid")
    brand_uuid = request.args.get("brand_uuid")
    if category_uuid:
        count = Watches.query.filter_by(category_uuid=category_uuid).count()
        return jsonify({"code": 200, "count": count})
    if brand_uuid:
        count = Watches.query.filter_by(brand_uuid=brand_uuid).count()
        return jsonify({"code": 200, "count": count})


@admin_api.route("/client/setting", methods=["GET"])
def client_settings():
    """
    訂單
    :return:
    """
    method = request.method
    if method == "GET":
        with open("data.json", "r") as f:
            file = eval(f.read())
        return jsonify({"code": 200, "data": file})


@admin_api.route('/statistic/calculate')
@check_admin
def count():

    try:
        order_count = Orders.query.count()
        # 本月月初和月末
        time_start, time_end = timeMonth()
        time_date_start = timeD(time_start)
        time_date_end = timeD(time_end)
        # 本月礼品兑换数量
        month_order_count = Orders.query.filter(Orders.create_at >= time_date_start).filter(Orders.create_at <= time_date_end).filter_by(delete_at=None).count()

        product_count = Watches.query.filter_by(delete_at=None).count()

        category_count = Category.query.filter_by(delete_at=None).count()
        brand_count = Brand.query.filter_by(delete_at=None).count()

        month_sale_product = db.session.query(OrderDetail.product_id, func.count(OrderDetail.product_number)).filter(Orders.order_num==OrderDetail.order_id).filter(
            Orders.create_at >= time_date_start). \
            filter(Orders.create_at <= time_date_end).group_by(OrderDetail.product_id).order_by(
            func.count(OrderDetail.product_number).desc()).limit(10).all()

        month_product_list = []
        for one in month_sale_product:
            product_id = one[0]
            qty = one[1]
            product = Watches.query.filter_by(id=product_id).filter_by(delete_at=None).first()
            if product:
                product_dict = product.to_dict()
                image_list = Images.query.filter_by(watches_uuid=product_dict["uuid"]).all()
                product_dict["image"] = loads(image_list)
                product_dict["qty"] = qty
                month_product_list.append(product_dict)
            else:
                continue
    except Exception as e:
        print(e)

    result = {"statistic": {
        "monthlyOrderTotal": month_order_count,
        "orderTotal": order_count,
        "monthlyRankProduct": month_product_list,
        "productTotal": product_count,
        "categoryTotal": category_count,
        "brandTotal": brand_count
    }}

    return jsonify(result)