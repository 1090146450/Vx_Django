import threading
import time
from datetime import datetime
from functools import wraps
from multiprocessing import Process, Queue

import requests


def get_reply(q, strnews):
    """请求AI接口并返回数据"""
    data = {"model": "text-davinci-003",
            "prompt": strnews,
            "temperature": 0.1,
            "max_tokens": 300,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            }
    headers = {'content-type': 'application/json',
               'Authorization': 'Bearer ' + "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"}
    time1 = datetime.now()
    res = requests.post(url="https://api.openai.com/v1/completions", json=data, headers=headers)
    print("所需时间为:", (datetime.now() - time1).seconds)
    res = res.json()
    q.put(res["choices"][0]["text"].replace("\n", ""))


def DefTime(q, *args, **kwargs):
    """创建多进程"""
    pr = Process(target=get_reply, args=(q, *args,), kwargs=kwargs, daemon=True)
    pr.start()  # 运行本来函数
    time.sleep(4)  # 等待4S进程
    if pr.is_alive():  # 判断进程是否完成要是完成则返回值，要是没完成则说太难了
        pr.terminate()
        return "太难了，回答不上来"
    else:
        text = q.get(timeout=2)
        if text:
            return text
        else:
            return "太难了啊！！我就一个机器人别这么为难我QAQ"
