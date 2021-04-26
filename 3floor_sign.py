import requests
import hashlib
import sys
import json
import os
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 配置各种key
# Server酱申请的skey
SCKEY = os.environ["SCKEY"]
# 钉钉机器人的 webhook
webhook = os.environ["dingding"]

# 配置通知方式 0=dingding 1=weixin 其他为不推送
notice = os.environ["notice"]
#手机号或邮箱
username = os.environ["username"]
#密码明文
password = os.environ["password"]

global content  #设置一个全局参数存储打印信息
contents = ''

def output(content):
    global contents
    contents += '  \n' + str(content)
    print(content)


def md5(password):
    m = hashlib.md5()
    b = password.encode(encoding='utf-8')
    m.update(b)
    password_md5 = m.hexdigest()
    return password_md5


def login():
    password_md5 = md5(password)
    url = 'http://floor.huluxia.com/account/login/ANDROID/4.0?device_code=1'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'account': username,
        'login_type': '2',
        'password': password_md5,
    }
    response = requests.post(url=url, data=data, headers=headers, verify=False)
    key = json.loads(response.text)['_key']
    nick = json.loads(response.text)['user']['nick']
    userID = json.loads(response.text)['user']['userID']
    output('[+]用户：' + nick + ';userID:' + str(userID))
    #output(key)
    return userID, key


def get_level(userID, key):
    url = 'http://floor.huluxia.com/view/level?viewUserID={userID}&_key={key}'.format(
        userID=userID, key=key)
    response = requests.post(url=url, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')  #解析html页面
    level = soup.select('.lev_li_forth span')  #筛选经验值
    output('[+]当前经验值:' + level[0].string)
    output('[+]距离下一等级:' + level[1].string + '还需:' + level[2].string + '经验')


def sign(key):
    url = 'https://floor.huluxia.com/category/list/ANDROID/2.0'
    response = requests.get(url=url, verify=False)
    categories = json.loads(response.text)['categories']
    count = 0  #签到次数
    for list in categories:
        categoryID = list['categoryID']
        title = list['title']
        url = 'https://floor.huluxia.com/user/signin/ANDROID/4.0?_key={key}&cat_id={categoryID}'.format(
            key=key, categoryID=categoryID)
        response = requests.get(url=url, verify=False)
        msg = json.loads(response.text)['msg']
        status = json.loads(response.text)['status']
        if status == 0:
            output('[+]' + msg)
        if status == 1:
            count += 1
            output('[+]板块' + str(count) + '：' + title + ' 签到成功')
    output('[+]共计签到' + str(count) + '个板块')


#server酱推送
def server():
    global contents
    message = {"text": "葫芦侠3楼签到通知！", "desp": contents}
    r = requests.post("https://sc.ftqq.com/" + SCKEY + ".send", data=message)
    if r.status_code == 200:
        print('[+]server酱已推送，请查收')
        
def ppsend(PPKEY, message):

    pp_url = 'http://pushplus.hxtrip.com/send?token={}&title=葫芦侠三楼签到通知！&content={}&template=html'.format(PPKEY, message)

    if pp_enable:

        r.get(url=pp_url)

#钉钉消息推送
def dingtalk():
    webhook_url = webhook
    dd_header = {"Content-Type": "application/json", "Charset": "UTF-8"}
    global contents
    dd_message = {
        "msgtype": "text",
        "text": {
            "content": f'葫芦侠3楼签到通知！\n{contents}'
        }
    }
    r = requests.post(url=webhook_url,
                      headers=dd_header,
                      data=json.dumps(dd_message))
    if r.status_code == 200:
        output('[+]钉钉消息已推送，请查收  ')


def main():
    output('---开始【登录，查询用户信息】---')
    try:
        value = login()
    except Exception:
        print('[+]登录失败，请检测账号密码')
        sys.exit()
    get_level(value[0], value[1])
    output('---结束【登录，查询用户信息】---\n')

    output('---开始【签到】---')
    sign(value[1])
    output('---结束【签到】---')
    if notice == '0':
        try:
            dingtalk()
        except Exception:
            print('[+]请检查钉钉配置是否正确')
    elif notice == '1':
        try:
            server()
        except Exception:
            print('[+]请检查server酱配置是否正确')
    else:
        print('[+]选择不推送信息')


def main_handler(event, context):
    return main()


if __name__ == '__main__':
    main()
