<<<<<<< HEAD
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
        sql = "select * from weather_id where id = %s"
        self.cursor.execute(sql, [str_data])
        datelist = self.cursor.fetchall()
        return datelist

    def updata_table(self, str_data, x, y, id):
        """更新表"""
        sql = "update weather_id set newtime = %s,x=%s,y=%s where id =%s"
        self.cursor.execute(sql, [str_data, x, y, id])
        self.conn.commit()

    def inster_table(self, a, b, c, d):
        """新增数据"""
        sql = "INSERT into weather_id VALUES(%s,%s,%s,%s)"
        self.cursor.execute(sql, [a, b, c, d])
        self.conn.commit()

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
    re = requests.get(url="https://v.api.aa1.cn/api/api-xiaoai/talk.php", params=params)
    try:
        re_text = re.text
    except Exception as e:
        q.put("阿偶，小爱出问题了，请联系管理员109014645@qq.com")
        raise e
    if re_text and re_text != "\n":
        q.put(re_text.replace("\n", ""))
    else:
        q.put("小爱也不会呢")
    print("所需时间为:", (datetime.now() - time1).seconds)


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
        self.xml_dict = xml_dict
        self.Lacation_w = xml_dict['xml']['Location_X']  # 获取维度
        self.Lacation_j = xml_dict['xml']['Location_Y']  # 获取精度
        self.Label = xml_dict['xml']["Label"]  # 获取地方

    def set_weather(self):
        """获取天气"""
        sq = Sql()  # 连接数据库
        st_id = self.xml_dict['xml']["FromUserName"]
        dateti = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 获取当前时间
        id_data = sq.select_table(st_id)  # 获取用户信息
        if id_data:
            sq.updata_table(dateti, str(self.Lacation_j), str(self.Lacation_w), st_id)
            sq.close()
            return "您的位置已更新，您可以发送：天气  即可获取当前天气信息"
        else:
            sq.inster_table(st_id, dateti, self.Lacation_j,
                            self.Lacation_w)
            sq.close()
            return "您的位置已记录，您可以发送：天气  即可获取当前天气信息"


def get_weather(xml_dict):
    sq = Sql()  # 连接数据库
    st_id = xml_dict['xml']["FromUserName"]
    id_data = sq.select_table(st_id)  # 获取用户信息
    if id_data:
        Lacation_j = id_data[0][2]
        Lacation_w = id_data[0][3]
    else:
        return "抱歉您需要先发一下位置才能获取"
    re = requests.get(
        url=fr"https://api.caiyunapp.com/v2.6/TAkhjf8d1nlSlspN/{Lacation_j},{Lacation_w}/realtime")
    weather = {"CLEAR_DAY": "晴（白天）", "CLEAR_NIGHT": "晴（夜间）", "PARTLY_CLOUDY_DAY": "多云（白天）",
               "PARTLY_CLOUDY_NIGHT": "多云（夜间）",
               "CLOUDY": "阴",
               "LIGHT_HAZE": "轻度雾霾", "MODERATE_HAZE": "中度雾霾", "HEAVY_HAZE": "重度雾霾", "LIGHT_RAIN": "小雨",
               "MODERATE_RAIN": "中雨",
               "HEAVY_RAIN": "大雨", "STORM_RAIN": "暴雨", "FOG": "雾", "LIGHT_SNOW": "小雪", "MODERATE_SNOW": "中雪",
               "HEAVY_SNOW": "大雪", "STORM_SNOW": "暴雪", "DUST": "浮尘", "SAND": "沙尘", "WIND": "大风"}
    re_js = re.json()  # 获取天气的JSON格式
    text = "您所在地区体感温度为:{0}度,风速{1}级,天气为:{2}".format(
        re_js['result']['realtime']["apparent_temperature"],
        re_js['result']["realtime"]["wind"]["speed"],
        weather[re_js["result"]["realtime"]["skycon"]])
    return text
=======
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
        self.conn = pymysql.connect(host="101.42.5.22", port=3306, user="root", password="woTMzhenShuai666",db="vx_data")
        self.cursor = self.conn.cursor()

    def create_table(self, str_data):
        """新建表"""
        self.cursor.execute(str_data)

    def select_table(self, str_data):
        """查询表"""
        sql = "select * from weather_id where id = %s"
        self.cursor.execute(sql, [str_data])
        datelist = self.cursor.fetchall()
        return datelist

    def updata_table(self, str_data, x, y, id):
        """更新表"""
        sql = "update weather_id set newtime = %s,x=%s,y=%s where id =%s"
        self.cursor.execute(sql, [str_data, x, y, id])
        self.conn.commit()

    def inster_table(self, a, b, c, d):
        """新增数据"""
        sql = "INSERT into weather_id VALUES(%s,%s,%s,%s)"
        self.cursor.execute(sql, [a, b, c, d])
        self.conn.commit()

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
    re = requests.get(url="https://v.api.aa1.cn/api/api-xiaoai/talk.php", params=params)
    try:
        re_text = re.text
    except Exception as e:
        q.put("阿偶，小爱出问题了，请联系管理员109014645@qq.com")
        raise e
    if re_text and re_text != "\n":
        q.put(re_text.replace("\n", ""))
    else:
        q.put("小爱也不会呢")
    print("所需时间为:", (datetime.now() - time1).seconds)


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
        self.xml_dict = xml_dict
        self.Lacation_w = xml_dict['xml']['Location_X']  # 获取维度
        self.Lacation_j = xml_dict['xml']['Location_Y']  # 获取精度
        self.Label = xml_dict['xml']["Label"]  # 获取地方

    def set_weather(self):
        """获取天气"""
        sq = Sql()  # 连接数据库
        st_id = self.xml_dict['xml']["FromUserName"]
        dateti = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 获取当前时间
        id_data = sq.select_table(st_id)  # 获取用户信息
        if id_data:
            sq.updata_table(dateti, str(self.Lacation_j), str(self.Lacation_w), st_id)
            sq.close()
            return "您的位置已更新，您可以发送：天气  即可获取当前天气信息"
        else:
            sq.inster_table(st_id, dateti, self.Lacation_j,
                            self.Lacation_w)
            sq.close()
            return "您的位置已记录，您可以发送：天气  即可获取当前天气信息"


def get_weather(xml_dict):
    sq = Sql()  # 连接数据库
    st_id = xml_dict['xml']["FromUserName"]
    id_data = sq.select_table(st_id)  # 获取用户信息
    if id_data:
        Lacation_j = id_data[0][2]
        Lacation_w = id_data[0][3]
    else:
        return "抱歉您需要先发一下位置才能获取"
    re = requests.get(
        url=fr"https://api.caiyunapp.com/v2.6/TAkhjf8d1nlSlspN/{Lacation_j},{Lacation_w}/realtime")
    weather = {"CLEAR_DAY": "晴（白天）", "CLEAR_NIGHT": "晴（夜间）", "PARTLY_CLOUDY_DAY": "多云（白天）",
               "PARTLY_CLOUDY_NIGHT": "多云（夜间）",
               "CLOUDY": "阴",
               "LIGHT_HAZE": "轻度雾霾", "MODERATE_HAZE": "中度雾霾", "HEAVY_HAZE": "重度雾霾", "LIGHT_RAIN": "小雨",
               "MODERATE_RAIN": "中雨",
               "HEAVY_RAIN": "大雨", "STORM_RAIN": "暴雨", "FOG": "雾", "LIGHT_SNOW": "小雪", "MODERATE_SNOW": "中雪",
               "HEAVY_SNOW": "大雪", "STORM_SNOW": "暴雪", "DUST": "浮尘", "SAND": "沙尘", "WIND": "大风"}
    re_js = re.json()  # 获取天气的JSON格式
    text = "您所在地区体感温度为:{0}度,风速{1}级,天气为:{2}".format(
        re_js['result']['realtime']["apparent_temperature"],
        re_js['result']["realtime"]["wind"]["speed"],
        weather[re_js["result"]["realtime"]["skycon"]])
    return text
>>>>>>> 完善了报错以及打包最新版本python3.9.1
