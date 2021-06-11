import json
import os
import time

import requests
from flask import Blueprint, request, jsonify, make_response, Response
from utils import generate_auth_token, check_login, hash_password, loads, create_excel, sender_email
from setting import IMG_SIZE, BASE_URL, IMG_PATH, PDF_PATH, FILE, merchantID, publicKey, privateKey, API_KEY, PUB_KEY
import uuid
import datetime
from models import db, Brand, Images, Category, Watches, UserInfo, Orders, OrderDetail
from sqlalchemy import text, extract, or_
from pay.pay import third_pay, client_token
from pay.stripe_pay import create_purchase


admin_api = Blueprint('admin', __name__)


@admin_api.route("/signin", methods=["POST"])
def login():
    username = request.json.get("username")
    password = request.json.get("password")
    if not all([username, password]):
        return jsonify({"code": 1002, "data": {"msg": "缺少參數"}})
    pass


@admin_api.route("/user", methods=["GET", "POST", "PUT", "DELETE"])
# @check_login
def user():
    method = request.method
    if method == "GET":
        uid = request.args.get("uuid")
        offset = request.args.get("offset", 20)
        page = request.args.get("page", 1)
        search = request.args.get("search")  # 模糊查找
        if search:
            user_obj = UserInfo.query.filter(UserInfo.username.like("%"+search+"%")).filter_by(delete_time=None).order_by(UserInfo.create_time.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
            user_list = loads(user_obj)
            ret = {"code": 200, "data":{"user_list": user_list}}
        else:
            if uid:
                user_obj = UserInfo.query.filter_by(uuid=uid, delete_time=None).first()
                user_list = loads(user_obj)
                ret = {"code": 200, "data": {"user_list": user_list}}
            else:
                user_obj = UserInfo.query.filter_by(delete_time=None).order_by(UserInfo.create_time.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
                user_list = loads(user_obj)
                ret = {"code": 200, "data": {"user_list": user_list}}
        return jsonify(ret)
    elif method == "PUT":
        data = request.json
        uid = data.get("uuid")
        username = data.get("username")
        password = data.get("password", "123456")
        email = data.get("email")
        phone = data.get("phone")
        user_obj = UserInfo.query.filter_by(uuid=uid).first()
        user_obj.username = username
        user_obj.password = password # hash_password(password)
        user_obj.email = email
        user_obj.phone = phone
        user_obj.update_time = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
        return jsonify(ret)
    elif method == "POST":
        data = request.json
        username = data.get("username")
        password = data.get("password", "123456")
        email = data.get("email")
        phone = data.get("phone")
        if not all([username, phone, email]):
            ret = {"code": 1002, "data": {"msg": "缺少必傳參數"}}
            return jsonify(ret)

        str_uuid = uuid.uuid4().hex
        user_obj = UserInfo(uuid=str_uuid, username=username, password=hash_password(password), email=email, phone=phone,
                            create_time=datetime.datetime.now())
        db.session.add(user_obj)
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "增加成功"}}

        return jsonify(ret)
    else:
        data = request.json
        uid = data.get("uuid")
        user_obj = UserInfo.query.filter_by(uuid=uid).first()
        user_obj.delete_time = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {"msg": "更改成功"}}
        return jsonify(ret)


@admin_api.route("/brand", methods=["GET", "POST", "PUT", "DELETE"])
# @check_login
def brand():
    method = request.method
    if method == "GET":
        uid = request.args.get("uuid")
        offset = request.args.get("offset", 20)
        page = request.args.get("page", 1)
        search = request.args.get("search")  # 模糊查找
        if search:
            brand_obj = Brand.query.filter(or_(Brand.name.like("%"+search+"%"), Brand.name_en.like("%"+search+"%"), Brand.name_cn.like("%"+search+"%"))).filter_by(delete_at=None).order_by(Brand.create_at.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
            brand_obj_count = Brand.query.filter(
                or_(Brand.name.like("%" + search + "%"), Brand.name_en.like("%" + search + "%"),
                    Brand.name_cn.like("%" + search + "%"))).filter_by(delete_at=None).count()
            brand_list = loads(brand_obj)
            ret = {"code": 200, "data": {"brand_list": brand_list, "count": brand_obj_count}, "msg": "success"}
        else:
            if uid:
                brand_obj = Brand.query.filter_by(uuid=uid, delete_at=None).first()
                brand_list = loads(brand_obj)
                ret = {"code": 200, "data": {"brand_list": brand_list}, "msg": "success"}
            else:
                brand_obj = Brand.query.filter_by(delete_at=None).order_by(Brand.create_at.desc()).limit(int(offset)).offset((int(page)-1)*int(offset)).all()
                brand_count = Brand.query.filter_by(delete_at=None).count()
                brand_list = loads(brand_obj)

                ret = {"code": 200, "data": {"brand_list": brand_list, "count": brand_count}, "msg": "success"}
        return jsonify(ret)
    elif method == "PUT":
        data = request.json
        uid = data.get("uuid")
        name = data.get("name")
        name_en = data.get("name_en")
        name_cn = data.get("name_cn")
        detail = data.get("detail")
        brand_obj = Brand.query.filter_by(uuid=uid).first()
        brand_obj.name = name
        brand_obj.name_en = name_en
        brand_obj.name_cn = name_cn
        brand_obj.detail = detail
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
        if not all([name, name_en, name_cn, detail]):
            ret = {"code": 1002, "data": {}, "msg": "缺少必傳參數"}
            return jsonify(ret)
        str_uuid = uuid.uuid4().hex
        user_obj = Brand(uuid=str_uuid, name=name, name_en=name_en, name_cn=name_cn,detail=detail,
                            create_at=datetime.datetime.now())
        db.session.add(user_obj)
        db.session.commit()
        ret = {"code": 200, "data": {}, "msg": "增加成功"}

        return jsonify(ret)
    else:
        data = request.json
        uid = data.get("uuid")
        user_obj = Brand.query.filter_by(uuid=uid).first()
        user_obj.delete_at = datetime.datetime.now()
        db.session.commit()
        ret = {"code": 200, "data": {}, "msg": "刪除成功"}
        return jsonify(ret)


@admin_api.route("/category", methods=["GET", "POST", "PUT", "DELETE"])
# @check_login
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
                category_list = Category.query.filter_by(delete_at=None, uuid=data.get("uuid"))
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


@admin_api.route("/watch", methods=["GET", "POST", "PUT", "DELETE"])
# @check_login
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
        url = "http://api.currencylayer.com/live?access_key=502b5f31ccef9c076feaaaf54c460e7d"
        response = requests.get(url).json()
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
                    ret = {"code": 200, "data": data_dict, "msg": "success"}
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
                                water_resistant=data.get("water_resistant"), annex=data.get("annex"),
                                clasp_type=data.get("clasp_type"), create_at=datetime.datetime.now(),)
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


@admin_api.route("/image", methods=["GET", "POST", "PUT", "DELETE"])
# @check_login
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
            if size >= IMG_SIZE:
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
        except:
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
# @check_login
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


@admin_api.route("/pay", methods=["POST"])
# @check_login
def pay():
    """
    上傳圖片
    :return:
    """
    data_json = request.json
    methods = data_json.get("methods")
    payment_method_nonce = data_json.get("payment_method_nonce")
    token = data_json.get("token")
    product_list = data_json.get("product")  # 數組 [[1, 2]]
    user_id = data_json.get("user_id")
    total = 0
    desc_list = ""
    data_msg = ""
    product_detail_list = []
    print(product_list)
    for item in product_list:
        wat = Watches.query.filter(Watches.id==item[0]).first()
        images = Images.query.filter_by(watches_uuid=wat.uuid).all()
        product_detail_list.append({"product_name": wat.name, "product_image": loads(images), "product_price": wat.price, "product_number": item[1], "product_id": wat.id, "total": wat.price * item[1]})
        desc_list += wat.name + "|"
        total += wat.price * item[1]

    is_pay = False
    if is_pay == False:
        j = 0
        # 支付不成功 不下执行 重试5次

        while j < 5:
            if methods == "braintree":
                result = third_pay(str(total), payment_method_nonce, data_msg)
                if result != True:
                    error_msg = result
                else:
                    is_pay = True
                    break
            elif methods == "stripe":
                print(total, data_msg, token, desc_list)
                result = create_purchase(total,"hkd",data_msg,token,"".join(desc_list),  # 這個之後就是根據買什麼產品放產品名字 數量  放進去
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
    order_num = "WAS"+str(int(time.time()))
    uid = uuid.uuid4().hex
    order_obj = Orders(uuid=uid, order_num=order_num, total=total, pay_methods="pay", user_id=user_id, create_at=datetime.datetime.now())
    orm_list = []
    orm_list.append(order_obj)
    for item in product_detail_list:
        print(item)
        obj = OrderDetail(order_id=order_num, product_name=item["product_name"], product_image=json.dumps(item["product_image"]), product_price=item["product_price"], product_number=item["product_number"], total=item["total"], product_id=item["product_id"])
        orm_list.append(obj)
    db.session.add_all(orm_list)
    db.session.commit()
    db.session.close()
    return {"code": 200, "msg": "支付成功"}


@admin_api.route("/order", methods=["GET", "POST", "PUT", "DELETE"])
# @check_login
def order():
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
            order_list = Orders.query.filter(or_(Orders.order_num.like("%"+search+"%"), Orders.name.like("%"+search+"%"))).filter_by(delete_at=None).order_by(Orders.create_at.desc(), Orders.id.desc()).offset((int(page)-1)*int(offset)).limit(int(offset)).all()
            count = Orders.query.filter_by(delete_at=None).count()
            ret = {"code": 200, "data": loads(order_list), "count": count}
        else:
            if data.get("order_num"):
                order_obj = Orders.query.filter_by(delete_at=None, order_num=data.get("order_num")).first()
                order_data = order_obj.to_dict()
                order_detail = OrderDetail.query.filter_by(order_id=order_obj.order_num).all()
                order_data["detail"] = loads(order_detail)
                ret = {"code": 200, "data": order_data}
            else:
                order_list = Orders.query.filter_by(delete_at=None).order_by(Orders.create_at.desc(), Orders.id.desc()).offset((int(page)-1)*int(offset)).limit(int(offset)).all()
                count = Orders.query.filter_by(delete_at=None).count()
                ret = {"code": 200, "data": loads(order_list), "count": count}
        return jsonify(ret)


