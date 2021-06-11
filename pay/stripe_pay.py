import os
import stripe
from setting import API_KEY, PUB_KEY


stripe.api_key = API_KEY


def create_purchase(amount, cur, user, source, desc):
    """
    记录用户信息 下次进入直接支付
    if not user[0]["customer_id"]:
        # 数据库中不存在customer_id 新建保存新建用户customerID
        customer = stripe.Customer.create(
            source=source,
            email=user[0]["email"],
            # phone=user[0]["phone"],
        )
        # card_1IkLAVEqCGWI4DfRJFXx9aL1 cus_JN5LRp8VkaxfQV
        res = FlaskAPI.save_customer(user[0]["id"], customer.id, "stripe")
        print(customer.id)
        result = stripe.Charge.create(
            amount=int(amount*100),
            currency=cur,
            customer=customer.id,  # customer["id"],
            # source=source, # source["id"], #如果需要測試更改成   source="tok_amex",  <===不使用token直接運行 用作讓你測試功能
            description=desc, #這個之後就是根據買什麼產品放產品名字 數量  放進去
            #receipt_email ="abc@gmail.com [客戶電郵]",  #發送一個收條
        )
    else:
        result = stripe.Charge.create(
            amount=int(amount*100),
            currency=cur,
            # payment_method="mastercard",
            customer=user[0]["customer_id"],  # customer["id"],
            # source=source,  # source["id"], #如果需要測試更改成   source="tok_amex",  <===不使用token直接運行 用作讓你測試功能
            description=desc,  # 這個之後就是根據買什麼產品放產品名字 數量  放進去
            # receipt_email ="abc@gmail.com [客戶電郵]",  #發送一個收條
        )
    """
    # 不使用记录用户信息
    result = stripe.Charge.create(
        amount=int(amount * 100),
        currency=cur,
        source=source,
        description=desc,  # 這個之後就是根據買什麼產品放產品名字 數量  放進去
        # receipt_email ="abc@gmail.com [客戶電郵]",  #發送一個收條
    )
    print("支付结果:", result)

    if result.status == "succeeded":
        return "succeeded"
    else:
        return "error"


def create_source(cardNumber, ownerInfo):
    """
    建立支付联系
    :param cardNumber:卡号
    :param ownerInfo:用户信息
    :return:
    """
    res_source = stripe.Source.create(
        cardNumber=cardNumber,
        ownerInfo=ownerInfo
    )
    if res_source:
        return res_source["id"]
    else:
        return ""


def find_customer(customer_id):
    """
    查询用户
    :param customer_id: cus_JMlIMHYECO8qIg
    :return: cus_JMlIMHYECO8qIg
    """
    res = stripe.Customer.retrieve(customer_id)
    if res:
        return res
    else:
        return False


def create_customer(email, phone, address, name):
    """
    建立用户
    :param userInfo:
    :return:
    """
    customer = stripe.Customer.create(
        email=email,
        phone=phone,
        address={"city": address},
        name=name
    )
    if customer:
        return customer["id"]
    else:
        return ""


def find_card(customer_id):
    """
    查看所有卡
    :param customer_id:
    :return:
    """
    res_card_list = stripe.Customer.list_sources(
        customer_id,
        limit=3
    )
    if res_card_list:
        return res_card_list["data"]
    else:
        return


def create_card(card, month, year, cvc, method="card") -> str:
    """
    通过卡号建立支付方式
    :param card: 卡号 "4242424242424242"
    :param month: 月份 "5"
    :param year: 年份 "2020"
    :param cvc: "314"
    :param method: 支付类型  "card"
    :return: 支付id  "pm_1IkuPD2eZvKYlo2CDOZXb0qG"
    """
    res = stripe.PaymentMethod.create(
        type=method,
        card={
            "number": card,
            "exp_month": month,
            "exp_year": year,
            "cvc": cvc,
        })
    return res


def connect_card_to_customer(card_id, customer_id):
    """
     PaymentMethod
    :return:
    """
    res = stripe.PaymentMethod.attach(
        card_id,
        customer=customer_id,
    )
    stripe.Customer.modify(
        customer_id,
        invoice_settings={
            'default_payment_method': card_id,
        },
    )
    return res


def create_product_price(product_id, price, count=1, cur="hkd", interval="month"):
    """
    建立价格
    :param product_id:
    :param price: 200
    :param cur: 'usd'
    :return:
    """
    res = stripe.Price.create(
        product=product_id,
        unit_amount=int(price*100),
        currency=cur,
        recurring={
            "aggregate_usage": None,
            "interval": interval,
            "interval_count": count,
            "usage_type": "licensed"
      },
    )
    return res


def create_installment_pay(price_list, cus_id, start_time, end_time, month):
    """
    分期支付
    :param price_list:[{
            'price': price_id,
            'quantity': count
        }]
    :param cus_id:
    :return:
    """
    # ===== 延遲收款 ======
    subscription = stripe.Subscription.create(
        customer=cus_id,
        items=price_list,
        cancel_at=end_time,
        # billing_cycle_anchor=end_time,
        # cancel_at_period_end=True
    )
    return subscription

    # ====  分期付款 =====
    # 該分期付款會收取一次20$的佣金
    # subscription = stripe.SubscriptionSchedule.create(
    #     customer=cus_id,
    #     start_date=start_time,
    #     end_behavior="release",
    #     phases=[
    #         {
    #             "items": price_list,
    #             "end_date": end_time,
    #             # "iterations": month,
    #         },
    #     ],
    # )
    # return subscription


def create_subscription_pay(price_list, cus_id):
    """
    訂閲支付
    :param price_list:[{
            'price': price_id,
            'quantity': count
        }]
    :param cus_id:
    :return:
    """
    # ===== 订阅收款 ======
    subscription = stripe.Subscription.create(
        customer=cus_id,
        items=price_list,
        cancel_at_period_end=True
    )
    return subscription


def cancel_subscription_pay(sub_id):
    subscription = stripe.Subscription.delete(sub_id)
    return subscription


# 预留发票功能
def send_invoice(sub_id):
    sub = stripe.Subscription.retrieve(sub_id)
    latest_invoice = sub.get("latest_invoice")
    # 发送发票
    invoice = stripe.Invoice.send_invoice(
      latest_invoice,
    )
    return invoice