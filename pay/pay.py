import braintree
from setting import merchantID, publicKey, privateKey


gateway = braintree.BraintreeGateway(
        braintree.Configuration(
            braintree.Environment.Sandbox,
            merchant_id=merchantID,
            public_key=publicKey,
            private_key=privateKey,
            timeout=120
        )
    )


# 生成token
def client_token(customer_id):
    # customer_id = "477961038"
    if customer_id:
        token = gateway.client_token.generate({
            "customer_id": customer_id
        })
    else:
        token = gateway.client_token.generate()
    return token


# 支付
def third_pay(amount, nonce_from_the_client, user_msg):
    # json_data = request.get_json(force=True)
    # nonce_from_the_client = request.form.get('payment_method_nonce')
    # print(nonce_from_the_client)

    result = gateway.transaction.sale({
        "amount": amount,
        "payment_method_nonce": nonce_from_the_client,
        # "device_data": device_data_from_the_client,
        "options": {
            "submit_for_settlement": True
        }
    })

    if result.is_success == True:
        print(result)
        print("支付成功*********")
        # 创建支付用户 获取支付customer_id
        # result = gateway.customer.create({
        #     "first_name": user_msg[0]["name"],
        #     "last_name": user_msg[0]["last_name"],
        #     "email": user_msg[0]["email"],
        #     "phone": user_msg[0]["phone"],
        #     "website": "www.example.com"
        # })
        if result.is_success:
            # 保存用戶customer.id
            print("222222222", result.customer.id)
            # print(result)
            # res = "" # FlaskAPI.save_customer(user_msg[0]["id"], result.customer.id)
            # if res == "success":
            #     result = gateway.payment_method.create({
            #         "customer_id": result.customer.id,
            #         "payment_method_nonce": nonce_from_the_client,
            #     })
            #     print(result, '創建成功！')
            # else:
            #     print("创建用户失败~")

        res = True
    else:
        print("支付出问题了*********")
        # print(result.errors.deep_errors)
        # print(result.transaction.processor_response_type)
        # print(result.transaction.processor_response_code)
        # print(result.transaction.processor_response_text)
        # print(result.transaction.gateway_rejection_reason)
        # print(result.transaction.currency_iso_code)
        res = True

    return res