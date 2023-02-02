# coding:utf-8
import hashlib
from multiprocessing import Queue

import openai
import requests
import xmltodict
from django.http import HttpResponse
# Create your views here.
from django.views.decorators.csrf import csrf_exempt

from Vx_Reply.Common.VxReplyNews import DefTime
from Vx_Reply.Common.Vx_masid import Masid


@csrf_exempt
def Reply(request):
    # get请求是用来校验
    if request.method == "GET":
        # 获取三个微信三个字段
        signature = request.GET.get("signature", )
        timestamp = request.GET.get("timestamp", )
        nonce = request.GET.get("nonce", )
        echostr = request.GET.get("echostr", )
        # 进行排序
        al_list = ["anyiqiang243", timestamp, nonce]
        al_list.sort()
        all_data = "".join(al_list)
        # 组合为字符串后进行sha1加密
        all_data = hashlib.sha1(all_data.encode("utf-8")).hexdigest()
        # 如果校验无误则直接返回加密密码否则返回错误
        if all_data == signature:
            return HttpResponse(echostr)
        return HttpResponse("错误")
    else:
        # 整理获取的xml数据转换为xml字典类型
        xml_dict = xmltodict.parse(request.body.decode())
        # 获取对应数据
        MassgeType = xml_dict['xml']["MsgType"]  # 消息类型，文本为text
        openid = xml_dict['xml']["FromUserName"]  # 发送方帐号（一个OpenID）
        createTime = xml_dict['xml']["CreateTime"]  # 消息创建时间 （整型）
        openai.api_key = "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"  #

        # 校验是不是超时5S没有回复
        if Masid(xml_dict["xml"]["MsgId"]).Query_id():
            print("超过5S回复失败！")
            return HttpResponse("")
        # 判断如果有消息则进行调用接口回复，如果没有消息则回复 "我没听懂，请重新输入"
        else:
            text = "我没听懂，请重新输入"
        # 判断用户输入的类型
        if MassgeType == 'text' and xml_dict['xml']['Content']:
            # 如果为text则返回text
            # 创建安全列表存储多进程数据
            q = Queue()
            # 获取数据
            text = DefTime(q, xml_dict['xml']['Content'])
        elif MassgeType == "location":
            # 如果为位置消息则存储
            Lacation_w = xml_dict['xml']['Location_X']  # 获取维度
            Lacation_j = xml_dict['xml']['Location_Y']  # 获取精度
            Label = xml_dict['xml']["Label"]
            re = requests.get(
                url=fr"https://api.caiyunapp.com/v2.6/TAkhjf8d1nlSlspN/{Lacation_j},{Lacation_w}/realtime")
            re_js = re.json()
            weather = {"CLEAR_DAY": "晴（白天）", "CLEAR_NIGHT": "晴（夜间）", "PARTLY_CLOUDY_DAY": "多云（白天）",
                       "PARTLY_CLOUDY_NIGHT": "多云（夜间）",
                       "CLOUDY": "阴",
                       "LIGHT_HAZE": "轻度雾霾", "MODERATE_HAZE": "中度雾霾", "HEAVY_HAZE": "重度雾霾", "LIGHT_RAIN": "小雨",
                       "MODERATE_RAIN": "中雨",
                       "HEAVY_RAIN": "大雨", "STORM_RAIN": "暴雨", "FOG": "雾", "LIGHT_SNOW": "小雪", "MODERATE_SNOW": "中雪",
                       "HEAVY_SNOW": "大雪", "STORM_SNOW": "暴雪", "DUST": "浮尘", "SAND": "沙尘", "WIND": "大风"}
            text = "您所在地区为:{0},体感温度为:{1}度,风速{2}级,天气为:{3}".format(Label, re_js['result']['realtime']["apparent_temperature"],
                                                               re_js['result']["realtime"]["wind"]["speed"],
                                                               weather[re_js["result"]["realtime"]["skycon"]])
        else:
            text = "抱歉，我除了文字啥也不会！"

        print("输入消息:", "", "\n回复:", text)
        xml = f"""<xml>
                            <ToUserName><![CDATA[{openid}]]></ToUserName>
                            <FromUserName><![CDATA[gh_3ef9e08d4393]]></FromUserName>
                            <CreateTime>{createTime}</CreateTime>
                            <MsgType><![CDATA[text]]></MsgType>
                            <Content><![CDATA[{text}]]></Content>
                    </xml>"""
        print("回复成功")
        return HttpResponse(xml, content_type="text/xml")
