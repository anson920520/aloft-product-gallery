import json

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from setting import ACCESS_KEY


class Timer:

    def change(self):

        executors = {
            "default": ProcessPoolExecutor(5)
        }

        scheduler = BlockingScheduler(executors=executors)
        scheduler.add_job(func=reset_rate, trigger='cron', day='*', hour='9', minute='1', second='1', misfire_grace_time=3600)
        scheduler.start()


def reset_rate():
    '''
    每個天重置一次汇率
    :return:
    '''
    url = "http://api.currencylayer.com/live?access_key={}&format=1".format(ACCESS_KEY)

    response = requests.get(url).json()
    print(ACCESS_KEY)
    if response.get("success"):
        with open("rate.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(response, ensure_ascii=True))
        quotes = response["quotes"]
        print(quotes)


if __name__=="__main__":

    Timer().change()