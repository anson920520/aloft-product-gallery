from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from sqlalchemy import Integer, ForeignKey, Column, INTEGER, String, JSON, DATETIME, FLOAT, TEXT
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
    uuid = Column(String(255))
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


class UserInfo(db.Model):
    __tablename__ = "user_info"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid = Column(String(255))
    username = Column(String(255))
    password = Column(String(255))
    email = Column(String(255))
    phone = Column(String(255))
    create_at = Column(DATETIME, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)


class Orders(db.Model):
    __tablename__ = "order"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid = Column(String(255))
    order_num = Column(String(255))
    order_detail = Column(JSON)
    total = Column(INTEGER)
    pay_methods = Column(String(255))
    user_id = Column(INTEGER)
    create_at = Column(DATETIME, nullable=True)
    update_at = Column(DATETIME, nullable=True)
    delete_at = Column(DATETIME, nullable=True)


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


if __name__ == '__main__':
    manager = Manager(app)
    migrate = Migrate(app, db)
    manager.add_command('db', MigrateCommand)
    manager.run()

# 1.python models.py db init
# 2.python models.py db migrate
# 3.python models.py db upgrade
