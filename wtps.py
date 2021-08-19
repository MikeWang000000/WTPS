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

ENABLE_LOGGING = True                               # �Ƿ�������־
ENABLE_WARNING = True                               # �Ƿ����þ��棨����Windows����ϵͳ��
REFRESH_INTERVAL = 5                                # ˢ�¼������λ��s��
REQUEST_TIMEOUT = 10                                # ����ʱ����λ��s��
OUTPUT_ENCODING = "auto"                            # ����̨������루����������������Ϊ��GBK����UTF-8����
COOKIE_PATH = ".cookie"                             # cookie�ļ�·��
NAME_JSON_PATH = "name.json"                        # �û���-�������ձ�·��
PLACE_JSON_PATH = "place.json"                      # ap-�ص���ձ�·��
TARGET_JSON_PATH = "target.json"                    # ����Ŀ���б�·��
LOG_DIR_NAME = "logs"                               # ��־�ļ�����
LOG_NAME_FORMAT = "%Y_%m_%d.log"                    # ��־�ļ���ʽ
LOGIN_USERNAME = "guest"                            # ac�û���
LOGIN_PASSWORD = "guest"                            # ac����
CONF_COMMAND = "show ac-config debug client"        # acִ������
LOGIN_URL = "http://rj-ac.local/login.do"           # ac��¼��ַ
CONF_URL = "http://rj-ac.local/web_config.do"       # acִ�е�ַ

# ������Ŀ¼�л���python�ű������ļ���
py_dir = os.path.split(os.path.realpath(sys.argv[0]))[0]
os.chdir(py_dir)

# ���봦��
if OUTPUT_ENCODING == "auto":
    if platform.system() == "Windows":
        OUTPUT_ENCODING = "GBK"
        os.system("mode con cols=64")
        # ���ݷ�����Windows
        os.system("CHCP 936 >NUL")
    else:
        OUTPUT_ENCODING = "UTF-8"

# ����cookie
cookie = cookielib.MozillaCookieJar(COOKIE_PATH)
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))

# ȫ�ֱ�����ʼ��
last_online_macs = set()
last_mac_place = {}
mac_to_name = {}
names = {}
places = {}
targets = []


# ��־���֣�stdout�ض���
class LogPrint:
    # ����stdout
    reload(sys)
    stdout = sys.stdout

    def __init__(self, dir_name, name_format):
        self.dir_name = dir_name
        self.format = name_format
        self.fo = None

    # ��ʱ�������־�ļ�·��
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

# ���þ�����ҪWindows����ϵͳ���ɵ���cmdow.exe
if ENABLE_WARNING and not platform.system() == "Windows" or not os.path.exists("cmdow.exe"):
    print "Warning: Warning mode is not supported, turned off automatically."
    ENABLE_WARNING = False


# ����ģʽ��ǰ�ò�����ڣ�������ɫ����
def warn_mode():
    if ENABLE_WARNING:
        os.system("cmdow.exe @ /res /act /top")
        os.system("color 1F")


# ����ģʽ��ȡ��ǰ�ã���ɫ����
def norm_mode():
    if ENABLE_WARNING:
        os.system("cmdow.exe @ /not")
        os.system("color 0F")


# ��¼����
def ac_login():
    global opener, cookie
    # �ԡ��û���:���롱����base64����
    login_hash = base64.b64encode("%s:%s" % (LOGIN_USERNAME, LOGIN_PASSWORD))
    # POST����
    auth_req = "auth=%s" % login_hash
    opener.open(LOGIN_URL, auth_req, timeout=REQUEST_TIMEOUT)
    cookie.save(ignore_discard=True, ignore_expires=True)


# ��ȡac������Ϣ������ʧ��Ĭ������3��
def get_ac_res(ntry=3):
    global opener
    ntry -= 1
    if ntry < 0:
        raise Exception
    # POST����
    ip_req = urllib.urlencode({"command": CONF_COMMAND, "mode_url": "exec"})
    response = opener.open(CONF_URL, ip_req, timeout=REQUEST_TIMEOUT)
    # ������������Ϣ
    res = response.read()
    # δ�ܻ�ȡ����Ϣ
    lines = res.splitlines()[4:-4]
    if len(lines) == 0:
        # ���µ�¼
        ac_login()
        return get_ac_res(ntry)
    else:
        return res


def get_ac_info():
    global names, places, targets, last_mac_place, last_online_macs, mac_to_name
    info = []  # �����û����ݱ����Ϣ
    online_macs = set()  # �������ߵ�mac��ַ
    targets_not_found = copy.copy(targets)  # ������δ�ҵ���Ŀ��
    # ������������Ϣ���Ĳ��֣����зָ�
    lines = get_ac_res().splitlines()[4:-4]
    # ����ÿ�����ӵ���Ϣ
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

        # �������û�������mac��ַ��Ϊ�û���
        if c_user == "":
            c_user = c_mac.replace(".", "")

        # ����δ֪��Ϣ�򲻽��н���
        if c_user not in names:
            names[c_user] = c_user
        if c_ap not in places:
            places[c_ap] = c_ap

        # �����ݽ������������͵ص�
        c_name = names[c_user]
        c_place = places[c_ap]

        # ����Ŀ���û���Ϣ
        if c_name in targets or targets == []:
            if c_name in targets_not_found and not targets == []:
                targets_not_found.remove(c_name)
            online_macs.add(c_mac)
            mac_to_name[c_mac] = c_name
            # ��������û���Ϣ
            print "%s  %s  %s" % (c_name.rjust(12), ("%s (%sdB)" % (c_place, c_rssi)).ljust(31), c_mac)
            # ���λ�ñ䶯
            if c_mac in last_mac_place and not last_mac_place[c_mac] == c_place:
                warn_mode()
                info.append("<< [ %s ] changed from [ %s ] to [ %s ] >>" % (c_name, last_mac_place[c_mac], c_place))
            # ���汾��λ�����´ζԱ�
            last_mac_place[c_mac] = c_place

    # ���û�����ݵ�Ŀ���û�
    for c_name in targets_not_found:
        print "%s  %s" % (c_name.rjust(12), "No Data".ljust(31))

    # ������û�
    for c_mac in (online_macs - last_online_macs):
        warn_mode()
        info.append("<< [ %s ] found at [ %s ] >>" % (mac_to_name[c_mac], last_mac_place[c_mac]))

    # ���ԭ���û���ʧ
    for c_mac in (last_online_macs - online_macs):
        warn_mode()
        info.append("<< [ %s ] lost at [ %s ] >>" % (mac_to_name[c_mac], last_mac_place[c_mac]))
        del last_mac_place[c_mac]

    print "================================="

    # �����ǰʱ��
    print time.ctime()

    # ����û����ݱ����Ϣ
    for n in info:
        print n
    last_online_macs = online_macs


def loop():
    global names, places, targets
    # ��ȡ������Ϣ
    # �û���-�������ձ�
    try:
        names = eval(open(NAME_JSON_PATH).read())
    except Exception:
        print "Warning: Name json file read failed, use default instead."
        names = {}
    # ap-�ص���ձ�
    try:
        places = eval(open(PLACE_JSON_PATH).read())
    except Exception:
        print "Warning: Place json file read failed, use default instead."
        places = {}
    # ����Ŀ���б�
    try:
        targets = eval(open(TARGET_JSON_PATH).read())
    except Exception:
        print "Warning: Target json file read failed, use default instead."
        targets = []
    # �ָ�����ģʽ
    norm_mode()
    # ��ӡ���ֿ�ʼ
    print "Wireless Teacher Positioning System (WTPS) Radar v%s" % __VERSION__
    print "------ Scaning ------"
    get_ac_info()
    print "------ Complete ------"


print "\nInfo: Program started at %s.\n" % time.ctime()
# ��ʼѭ��
while True:
    try:
        loop()
        # �ȴ��´�ѭ��
        time.sleep(REFRESH_INTERVAL)
        print "\n\n"
    except KeyboardInterrupt:
        # ��ֹ�� Ctrl+C ���³����˳�
        if raw_input("Exit? (y/n)") == "y":
            exit()
        else:
            print "\n\n"
            continue
