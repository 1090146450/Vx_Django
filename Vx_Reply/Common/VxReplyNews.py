import threading
import time
from datetime import datetime
from functools import wraps
from multiprocessing import Process, Queue

import pymysql
import requests


class Sql():
    """数据库连接"""

    def __init__(self, ):
        """连接数据库"""
        self.conn = pymysql.connect(host="101.42.5.22", port=3306, user="root", password="99e278a1c0aa18c2",
                                    db="vx_data")
        self.cursor = self.conn.cursor()

    def create_table(self, str_data):
        """新建表"""
        self.cursor.execute(str_data)

    def select_table(self, str_data):
        """查询表"""
        self.cursor.execute(str_data)
        datelist = self.cursor.fetchall()
        return datelist

    def close(self):
        """退出查询"""
        self.cursor.close()
        self.conn.close()


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
    print(res)
    q.put(res["choices"][0]["text"].replace("\n", ""))


def XiaoAi(q, strnews):
    """请求小爱同学接口"""
    params = {"type": "text", "msg": strnews}
    time1 = datetime.now()
    re = requests.get(url="https://xiaoapi.cn/API/lt_xiaoai.php", params=params)
    try:
        re_json = re.json()
    except Exception:
        q.put("阿偶，小爱出问题了，请联系管理员109014645@qq.com")
    print("所需时间为:", (datetime.now() - time1).seconds)
    q.put(re_json["data"]['txt'])


def DefTime(q, *args, **kwargs):
    """创建多进程"""
    pr = Process(target=XiaoAi, args=(q, *args,), kwargs=kwargs, daemon=True)
    pr.start()  # 运行本来函数
    time.sleep(4)  # 等待4S进程
    if pr.is_alive():  # 判断进程是否完成要是完成则返回值，要是没完成则说太难了
        pr.terminate()
        return "小爱也回答不上来了55"
    else:
        text = q.get(timeout=2)
        if text:
            return text
        else:
            return "太难了啊！！我就一个机器人别这么为难我QAQ"


class Location():
    """地理位置处理"""

    def __init__(self, xml_dict):
        """获取经纬度"""
        self.Lacation_w = xml_dict['xml']['Location_X']  # 获取维度
        self.Lacation_j = xml_dict['xml']['Location_Y']  # 获取精度
        self.Label = xml_dict['xml']["Label"]  # 获取地方

    def re_weather(self):
        """获取天气"""
        re = requests.get(
            url=fr"https://api.caiyunapp.com/v2.6/TAkhjf8d1nlSlspN/{self.Lacation_j},{self.Lacation_w}/realtime")
        weather = {"CLEAR_DAY": "晴（白天）", "CLEAR_NIGHT": "晴（夜间）", "PARTLY_CLOUDY_DAY": "多云（白天）",
                   "PARTLY_CLOUDY_NIGHT": "多云（夜间）",
                   "CLOUDY": "阴",
                   "LIGHT_HAZE": "轻度雾霾", "MODERATE_HAZE": "中度雾霾", "HEAVY_HAZE": "重度雾霾", "LIGHT_RAIN": "小雨",
                   "MODERATE_RAIN": "中雨",
                   "HEAVY_RAIN": "大雨", "STORM_RAIN": "暴雨", "FOG": "雾", "LIGHT_SNOW": "小雪", "MODERATE_SNOW": "中雪",
                   "HEAVY_SNOW": "大雪", "STORM_SNOW": "暴雪", "DUST": "浮尘", "SAND": "沙尘", "WIND": "大风"}
        re_js = re.json()  # 获取天气的JSON格式
        sq = Sql()  # 连接数据库
        sql = "select id from weather_vx where id = {1}".format(self.xml_dict['xml']["FromUserName"])  # 进行查询
        dateti = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 获取当前时间
        id_data = sq.select_table(sql)  # 获取用户信息
        if id_data:
            sql = "INSERT into weather_id VALUES({1},{2},{3},{4})".format()
            sq.create_table()
            return "您的位置已更新，您可以发送：天气  即可获取当前天气信息"
        else:

            return "您的位置已记录，您可以发送：天气  即可获取当前天气信息"
        text = "您所在地区为:{0},体感温度为:{1}度,风速{2}级,天气为:{3}".format(self.Label,
                                                             re_js['result']['realtime']["apparent_temperature"],
                                                             re_js['result']["realtime"]["wind"]["speed"],
                                                             weather[re_js["result"]["realtime"]["skycon"]])
