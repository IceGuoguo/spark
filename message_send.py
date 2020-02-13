# -*- coding:utf-8 -*-
# 短信图文发送
import datetime
from datetime import datetime, date, timedelta
import json
import pymssql
import random
import requests
from functions import write_log


# 消息推送接口
url_basic = "http://10.20.99.192:80/"
url_string = "v2/cgi-bin/message/custom/send?access_token="


# 创建token的接口
url_get_token = "http://10.20.99.192:80/admin-api/v2/token/create"



# 获取token，我们会把定时刷新的token写到一张表里
def get_token():
    sql = "select access_token from access_token where uid = 'yzl_client'"
    conn = pymssql.connect(server="", user="", password="", database="")
    cursor = conn.cursor()
    print(sql)
    cursor.execute(sql)
    row = cursor.fetchone()
    access_token = row[0]
    conn.close()
    return access_token


# 随机使用如下图片中的一张
def get_img_url():
    img_url = [] # 图片信息的地址，需要使用可于外网访问到的链接，建议使用开放平台cdn https://hm.longqueyun.com/doc/cdnhub/cdnhub-guide/intro
    n = random.randint(1, 5) - 1 # 5张里面选一张
    return img_url[n]

# 获取名单
def get_uid_yf():
    info = [    ]  # 发送的名单
    return info


# 读数据库记录短信内容的表
def get_information():
    info = ""
    today = "{0}-{1}-{2} 00:00:00.000".format(str(datetime.now().year), str(datetime.now().month),
                                              str(datetime.now().day))
    sql = "select top 1 convert(nvarchar(500),MessageContent) from message_content2_std where MessageDate = '" + \
          today + "' order by stamp desc" # 首先读取记录短信内容的表
    conn = pymssql.connect(server='', user='', password='', database='')
    cursor = conn.cursor()
    print(sql)
    cursor.execute(sql)
    row = cursor.fetchone()
    if row is not None:
        info = row[0]
        additional_info = ""
        has_formal_message = True
    else:
        has_formal_message = False
    cursor.close()
    conn.close()
    sql2 = "select top 1 convert(nvarchar(500),MessageContent), convert(nvarchar(500),AdditionalContent)" \
           " from message_content2_yzl where MessageDate = '" + today + "' order by stamp desc" # 读取是否有附加信息
    conn2 = pymssql.connect(server='', user='', password='', database='')
    cursor2 = conn2.cursor()
    print(sql2)
    cursor2.execute(sql2)
    row2 = cursor2.fetchone()
    if row2 is not None:
        additional_info = row2[1]
        has_artificial_message = True
    else:
        has_artificial_message = False
    cursor2.close()
    conn2.close()
    if has_formal_message or has_artificial_message:
        # message截取字符串分段
        message = info.split("。")[0] + "。\n\n" + info.split("。")[1].split(";")[0] + ";\n\n" + \
                  info.split("。")[1].split(';')[1] + ";" + info.split("。")[1].split(';')[2] + "。"
        if additional_info is not None and additional_info != '':
            message += "\n\n" + additional_info  # 短信后附加语句
    else:
        message = "error"  # 无正式短信时
    return message


# 点击跳转使用的链接
def return_url():
    # today = datetime.datetime.now()
    yesterday = (date.today() + timedelta(days=-1)).strftime("%Y%m%d")
    basic_url = 'yzl-wp://' # 云助理访问地址
    url_add = '?date=' + yesterday # 后缀
    url = basic_url + url_add
    print(url)
    return url


# 读标志位判断是否发送
def get_flag():
    sql = "select flag from a_message_flag where name = 'tuwen'"
    conn = pymssql.connect(server='', user='', password='', database='')
    cursor = conn.cursor()
    print(sql)
    cursor.execute(sql)
    row = cursor.fetchone()
    status = row[0]
    cursor.close()
    conn.close()
    return status


if __name__ == '__main__':
    token = get_token()
    img = get_img_url()
    url = url_basic + url_string + token
    person = get_uid_yf()
    information = get_information()
    flag = get_flag()
    if information != "error" and flag:
        num = 0
        for index in range(len(person)):
            # 调用信息推送接口的入参请写成如下的形式
			data = {
                "touser": person[index], # 工号
                "msgtype": "news", # news表示图文消息
                "news": {
                    "articles": [
                        {
                            "title": "<h4>保费快报</h4><p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;＞请点击图片查看详细信息</p>", # 标题，支持html标签表达的形式
                            "description": information, # 内容
                            "picurl": img, # 上方的图片
                            "url": return_url(), # 点击跳转使用的链接
                        }
                    ]
                },
                "copy": 1, # 是否可复制，1表示不能，0表示可以
                "share": 1,# 是否可转发，1表示不能，0表示可以
                "reply": 1,# 是否可回复，1表示不能，0表示可以
                "watermark": 0# 是否有水印，1表示无，0表示有
            }
            response = requests.post(url, json=data)
            res = json.loads(response.text)
            if res['errcode'] == 0:
                write_log(1, person[index], "tuwen") # 这里是写log
            else:
                write_log(0, person[index], "tuwen")
        print("message sent yet")
    else:
        print("no message to send.")
