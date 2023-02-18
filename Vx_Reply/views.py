# coding:utf-8
import hashlib
from multiprocessing import Queue

import openai
import xmltodict
from django.http import HttpResponse
# Create your views here.
from django.views.decorators.csrf import csrf_exempt

from Vx_Reply.Common.VxReplyNews import DefTime, Location, get_weather
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
        # 判断用户输入的类型
        if MassgeType == 'text' and xml_dict['xml']['Content']:
            # 如果为text则返回text
            if xml_dict['xml']['Content'] == "天气":
                text = get_weather(xml_dict)
            else:
                # 创建安全列表存储多进程数据
                q = Queue()
                # 获取数据
                text = DefTime(q, xml_dict['xml']['Content'])
                print("输入消息:", xml_dict['xml']['Content'], "\n回复:", text)
        elif MassgeType == "location":
            # 如果为位置消息则存储
            la = Location(xml_dict)
            text = la.set_weather()
        else:
            text = "抱歉，我除了文字啥也不会！"

        xml = f"""<xml>
                            <ToUserName><![CDATA[{openid}]]></ToUserName>
                            <FromUserName><![CDATA[gh_3ef9e08d4393]]></FromUserName>
                            <CreateTime>{createTime}</CreateTime>
                            <MsgType><![CDATA[text]]></MsgType>
                            <Content><![CDATA[{text}]]></Content>
                    </xml>"""
        print("回复成功")
        return HttpResponse(xml, content_type="text/xml")
