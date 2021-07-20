import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from sqlalchemy import Integer, ForeignKey, Column, INTEGER, String, JSON, DATETIME, FLOAT, TEXT
from sqlalchemy.orm import relationship

from setting import SQLALCHEMY_DATABASE_URI


app = Flask(__name__, static_url_path="/static")
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

db = SQLAlchemy(app)


class Brand(db.Model):
    __tablename__ = "brand"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid = Column(String(255), index=True)
    name = Column(String(255))
    name_en = Column(String(255))
    name_cn = Column(String(255))
    detail = Column(TEXT)
    count = Column(Integer)
    image_uuid = Column(String(500))
    category_uuid = Column(String(50))
    create_at = Column(DATETIME, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class Category(db.Model):
    __tablename__ = "category"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid = Column(String(255), index=True)
    name = Column(String(255))
    name_cn = Column(String(255))
    name_en = Column(String(255))
    detail = Column(TEXT)
    create_at = Column(DATETIME, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class Images(db.Model):
    __tablename__ = "images"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid = Column(String(255))
    watches_uuid = Column(String(255), index=True)
    image_name = Column(String(255))
    full_path = Column(String(255))
    order_id = Column(INTEGER)
    create_at = Column(DATETIME, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class Watches(db.Model):
    __tablename__ = "watches"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid = Column(String(255), index=True)
    category_uuid = Column(String(255), index=True)
    brand_uuid = Column(String(255), index=True)
    name = Column(String(255))
    name_en = Column(String(255))
    name_cn = Column(String(255))
    series = Column(String(255))
    series_cn = Column(String(255))
    series_en = Column(String(255))
    weight = Column(String(255))
    shipping_weight = Column(String(255))
    model = Column(String(255))
    movement = Column(String(255))
    power_reserve = Column(String(255))
    case_diameter = Column(String(255))
    case_thickness = Column(String(255))
    case_material = Column(String(255))
    case_material_resistance = Column(String(255))
    dial_color = Column(String(255))
    dial_material = Column(String(255))
    strap_color = Column(String(255))
    strap_material = Column(String(255))
    water_resistant = Column(String(255))
    annex = Column(TEXT)
    clasp_type = Column(String(255))
    price = Column(FLOAT(11))
    store = Column(INTEGER, default=100)
    detail = Column(TEXT)
    create_at = Column(DATETIME, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)
    status = Column(INTEGER, default=0)  # 0 需要付定金 1 不要定金

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class UserInfo(db.Model):
    __tablename__ = "user_info"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid = Column(String(255), index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    username = Column(String(255), unique=True)
    password = Column(String(255))
    email = Column(String(255))
    phone = Column(String(255))
    birthday = Column(String(255))
    country = Column(String(255))
    create_at = Column(DATETIME, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class Orders(db.Model):
    __tablename__ = "order"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid = Column(String(255), index=True)
    order_num = Column(String(255))
    # order_detail = Column(JSON)
    total = Column(FLOAT)
    deposit = Column(FLOAT)
    pay_methods = Column(String(255))
    status = Column(INTEGER, default=0)  # 0:未支付 1：已支付定金 2：已取消
    user_id = Column(INTEGER)
    address_id = Column(INTEGER)
    booking_time = Column(String(500))
    create_at = Column(DATETIME, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class OrderDetail(db.Model):
    __tablename__ = "order_detail"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    order_id = Column(String(50))
    product_name = Column(String(500))
    product_image = Column(String(5000))
    product_price = Column(FLOAT)
    product_number = Column(INTEGER)
    product_id = Column(INTEGER)
    total = Column(FLOAT)

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class ShoppingCar(db.Model):
    __tablename__ = "shopping_car"
    id = Column(INTEGER, autoincrement=True, primary_key=True)
    user_id = Column(INTEGER)
    product_id = Column(INTEGER, ForeignKey("watches.id"))
    count = Column(INTEGER)
    create_at = Column(DATETIME, default=datetime.datetime.now, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)
    shopping_product = relationship("Watches")

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class Favorite(db.Model):
    __tablename__ = "favorite"
    id = Column(INTEGER, autoincrement=True, primary_key=True)
    user_id = Column(INTEGER)
    product_id = Column(INTEGER, ForeignKey("watches.id"))
    create_at = Column(DATETIME, default=datetime.datetime.now, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)

    favorite_product = relationship("Watches")

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class Address(db.Model):
    __tablename__ = "address"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    user_id = Column(INTEGER)
    first_name = Column(String(255))
    last_name = Column(String(255))
    appellation = Column(String(255))
    area = Column(String(255))
    city = Column(String(255))
    district = Column(String(255))
    place = Column(String(255))
    mobile = Column(String(255))
    is_delete = Column(INTEGER, default=0)

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class Admin(db.Model):
    __tablename__ = "admin"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    username = Column(String(255))
    password = Column(String(255))
    role = Column(INTEGER, ForeignKey("role.id"))
    create_at = Column(DATETIME, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)
    admin_role = relationship("Role")  # backref反向关联

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict(
            (column_name, getattr(self, column_name, None)) \
            for column_name in column_name_list
        )


class Role(db.Model):
    __tablename__ = "role"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    role = Column(String(255))

    def to_dict(self):
        column_name_list = [
            value[0] for value in self._sa_instance_state.attrs.items()
        ]
        return dict((column_name, getattr(self, column_name, None)) for column_name in column_name_list)


if __name__ == '__main__':
    manager = Manager(app)
    migrate = Migrate(app, db)
    manager.add_command('db', MigrateCommand)
    manager.run()

# 1.python models.py db init
# 2.python models.py db migrate
# 3.python models.py db upgrade
