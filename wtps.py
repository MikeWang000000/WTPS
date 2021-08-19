#!/usr/bin/env python2.7
# -*- coding: GBK -*-

__VERSION__ = "2.0.10-gh"

import cookielib
import platform
import urllib2
import urllib
import base64
import time
import copy
import sys
import os

ENABLE_LOGGING = True                               # 是否启用日志
ENABLE_WARNING = True                               # 是否启用警告（仅限Windows操作系统）
REFRESH_INTERVAL = 5                                # 刷新间隔（单位：s）
REQUEST_TIMEOUT = 10                                # 请求超时（单位：s）
OUTPUT_ENCODING = "auto"                            # 控制台输出编码（如果出现乱码可设置为“GBK”或“UTF-8”）
COOKIE_PATH = ".cookie"                             # cookie文件路径
NAME_JSON_PATH = "name.json"                        # 用户名-姓名对照表路径
PLACE_JSON_PATH = "place.json"                      # ap-地点对照表路径
TARGET_JSON_PATH = "target.json"                    # 监视目标列表路径
LOG_DIR_NAME = "logs"                               # 日志文件夹名
LOG_NAME_FORMAT = "%Y_%m_%d.log"                    # 日志文件格式
LOGIN_USERNAME = "guest"                            # ac用户名
LOGIN_PASSWORD = "guest"                            # ac密码
CONF_COMMAND = "show ac-config debug client"        # ac执行命令
LOGIN_URL = "http://rj-ac.local/login.do"           # ac登录地址
CONF_URL = "http://rj-ac.local/web_config.do"       # ac执行地址

# 将工作目录切换至python脚本所在文件夹
py_dir = os.path.split(os.path.realpath(sys.argv[0]))[0]
os.chdir(py_dir)

# 编码处理
if OUTPUT_ENCODING == "auto":
    if platform.system() == "Windows":
        OUTPUT_ENCODING = "GBK"
        os.system("mode con cols=64")
        # 兼容非中文Windows
        os.system("CHCP 936 >NUL")
    else:
        OUTPUT_ENCODING = "UTF-8"

# 处理cookie
cookie = cookielib.MozillaCookieJar(COOKIE_PATH)
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))

# 全局变量初始化
last_online_macs = set()
last_mac_place = {}
mac_to_name = {}
names = {}
places = {}
targets = []


# 日志部分，stdout重定向
class LogPrint:
    # 备份stdout
    reload(sys)
    stdout = sys.stdout

    def __init__(self, dir_name, name_format):
        self.dir_name = dir_name
        self.format = name_format
        self.fo = None

    # 按时间更新日志文件路径
    def update(self):
        if not os.path.exists(self.dir_name):
            os.mkdir(self.dir_name)
        log_name = time.strftime(self.format, time.localtime())
        log_path = os.path.join(self.dir_name, log_name)
        if self.fo is None or self.fo.name != log_path:
            self.fo = open(log_path, "a")

    def write(self, s):
        if ENABLE_LOGGING:
            self.update()
            self.fo.write(s)
            self.fo.flush()
        if not OUTPUT_ENCODING == "GBK":
            s = s.decode("GBK").encode(OUTPUT_ENCODING, "ignore")
        self.stdout.write(s)


sys.stdout = LogPrint(LOG_DIR_NAME, LOG_NAME_FORMAT)

# 启用警告需要Windows操作系统并可调用cmdow.exe
if ENABLE_WARNING and not platform.system() == "Windows" or not os.path.exists("cmdow.exe"):
    print "Warning: Warning mode is not supported, turned off automatically."
    ENABLE_WARNING = False


# 警告模式，前置并激活窗口，设置蓝色背景
def warn_mode():
    if ENABLE_WARNING:
        os.system("cmdow.exe @ /res /act /top")
        os.system("color 1F")


# 正常模式，取消前置，黑色背景
def norm_mode():
    if ENABLE_WARNING:
        os.system("cmdow.exe @ /not")
        os.system("color 0F")


# 登录函数
def ac_login():
    global opener, cookie
    # 对“用户名:密码”进行base64编码
    login_hash = base64.b64encode("%s:%s" % (LOGIN_USERNAME, LOGIN_PASSWORD))
    # POST数据
    auth_req = "auth=%s" % login_hash
    opener.open(LOGIN_URL, auth_req, timeout=REQUEST_TIMEOUT)
    cookie.save(ignore_discard=True, ignore_expires=True)


# 获取ac返回信息函数，失败默认重试3次
def get_ac_res(ntry=3):
    global opener
    ntry -= 1
    if ntry < 0:
        raise Exception
    # POST数据
    ip_req = urllib.urlencode({"command": CONF_COMMAND, "mode_url": "exec"})
    response = opener.open(CONF_URL, ip_req, timeout=REQUEST_TIMEOUT)
    # 服务器返回信息
    res = response.read()
    # 未能获取到信息
    lines = res.splitlines()[4:-4]
    if len(lines) == 0:
        # 重新登录
        ac_login()
        return get_ac_res(ntry)
    else:
        return res


def get_ac_info():
    global names, places, targets, last_mac_place, last_online_macs, mac_to_name
    info = []  # 储存用户数据变更信息
    online_macs = set()  # 本次在线的mac地址
    targets_not_found = copy.copy(targets)  # 本次尚未找到的目标
    # 服务器返回信息正文部分，按行分割
    lines = get_ac_res().splitlines()[4:-4]
    # 遍历每个链接的信息
    for line in lines:
        c_mac = line[0:14].strip()      #
        c_ip = line[15:31].strip()      #
        c_ip6 = line[32:72].strip()
        c_ap = line[73:137].strip()     #
        c_radio = line[138:143].strip()
        c_ssid = line[144:184].strip()
        c_rssi = line[185:189].strip()  #
        c_wlan = line[190:194].strip()
        c_vlan = line[195:199].strip()
        c_status = line[200:215].strip()
        c_assoauth = line[216:231].strip()
        c_netauth = line[232:247].strip()
        c_v4up = line[248:263].strip()
        c_v4down = line[264:281].strip()
        c_v6up = line[282:297].strip()
        c_v6down = line[298:315].strip()
        c_time = line[316:328].strip()
        c_client = line[329:369].strip()
        c_user = line[370:410].strip()   #

        # 不存在用户名则以mac地址作为用户名
        if c_user == "":
            c_user = c_mac.replace(".", "")

        # 存在未知信息则不进行解析
        if c_user not in names:
            names[c_user] = c_user
        if c_ap not in places:
            places[c_ap] = c_ap

        # 由数据解析到的姓名和地点
        c_name = names[c_user]
        c_place = places[c_ap]

        # 处理目标用户信息
        if c_name in targets or targets == []:
            if c_name in targets_not_found and not targets == []:
                targets_not_found.remove(c_name)
            online_macs.add(c_mac)
            mac_to_name[c_mac] = c_name
            # 输出在线用户信息
            print "%s  %s  %s" % (c_name.rjust(12), ("%s (%sdB)" % (c_place, c_rssi)).ljust(31), c_mac)
            # 检测位置变动
            if c_mac in last_mac_place and not last_mac_place[c_mac] == c_place:
                warn_mode()
                info.append("<< [ %s ] changed from [ %s ] to [ %s ] >>" % (c_name, last_mac_place[c_mac], c_place))
            # 保存本次位置与下次对比
            last_mac_place[c_mac] = c_place

    # 输出没有数据的目标用户
    for c_name in targets_not_found:
        print "%s  %s" % (c_name.rjust(12), "No Data".ljust(31))

    # 检测新用户
    for c_mac in (online_macs - last_online_macs):
        warn_mode()
        info.append("<< [ %s ] found at [ %s ] >>" % (mac_to_name[c_mac], last_mac_place[c_mac]))

    # 检测原有用户丢失
    for c_mac in (last_online_macs - online_macs):
        warn_mode()
        info.append("<< [ %s ] lost at [ %s ] >>" % (mac_to_name[c_mac], last_mac_place[c_mac]))
        del last_mac_place[c_mac]

    print "================================="

    # 输出当前时间
    print time.ctime()

    # 输出用户数据变更信息
    for n in info:
        print n
    last_online_macs = online_macs


def loop():
    global names, places, targets
    # 读取配置信息
    # 用户名-姓名对照表
    try:
        names = eval(open(NAME_JSON_PATH).read())
    except Exception:
        print "Warning: Name json file read failed, use default instead."
        names = {}
    # ap-地点对照表
    try:
        places = eval(open(PLACE_JSON_PATH).read())
    except Exception:
        print "Warning: Place json file read failed, use default instead."
        places = {}
    # 监视目标列表
    try:
        targets = eval(open(TARGET_JSON_PATH).read())
    except Exception:
        print "Warning: Target json file read failed, use default instead."
        targets = []
    # 恢复正常模式
    norm_mode()
    # 打印部分开始
    print "Wireless Teacher Positioning System (WTPS) Radar v%s" % __VERSION__
    print "------ Scaning ------"
    get_ac_info()
    print "------ Complete ------"


print "\nInfo: Program started at %s.\n" % time.ctime()
# 开始循环
while True:
    try:
        loop()
        # 等待下次循环
        time.sleep(REFRESH_INTERVAL)
        print "\n\n"
    except KeyboardInterrupt:
        # 防止误按 Ctrl+C 导致程序退出
        if raw_input("Exit? (y/n)") == "y":
            exit()
        else:
            print "\n\n"
            continue
