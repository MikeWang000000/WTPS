#!/usr/bin/env python2.7
# -*- coding: GBK -*-
"""
    此脚本用于模拟无线AC服务端。
"""
import BaseHTTPServer
import SocketServer
import time
import random

LISTENIP = "127.0.0.1"
PORT = 9999


class ConnectionRecord(object):
    def __init__(self):
        self.mac = ""
        self.ip = ""
        self.ip6 = ""
        self.ap = ""
        self.radio = ""
        self.ssid = ""
        self.rssi = ""
        self.wlan = ""
        self.vlan = ""
        self.status = ""
        self.assoauth = ""
        self.netauth = ""
        self.v4up = ""
        self.v4down = ""
        self.v6up = ""
        self.v6down = ""
        self.time = ""
        self.client = ""
        self.user = ""

    def __str__(self):
        return "%-14s %-16s %-40s %-64s %-5s %-40s %-4s %-4s %-4s %-15s %-15s %-15s %-15s %-17s %-15s " \
               "%-17s %-12s %-40s %-40s" % (
                   self.mac, self.ip, self.ip6, self.ap, self.radio, self.ssid, self.rssi, self.wlan,
                   self.vlan, self.status, self.assoauth, self.netauth, self.v4up, self.v4down, self.v6up,
                   self.v6down, self.time, self.client, self.user
               )


class ServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith("/login.do"):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Set-Cookie", "LOGIN=yes; path=/; HttpOnly")
            self.end_headers()
            self.wfile.write("OK.")
        elif self.path.endswith("/web_config.do"):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            # 模拟延迟
            time.sleep(0.25)
            self.wfile.write(console_response())
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("404 Not Found.")

    def do_POST(self):
        self.do_GET()


teacher_a = ConnectionRecord()
teacher_a.mac = "0123.4567.89ab"
teacher_a.ap = "Office-302"
teacher_a.user = "wang"
teacher_a.rssi = -40

teacher_b = ConnectionRecord()
teacher_b.mac = "cdef.0123.4567"
teacher_b.ap = "Office-304"
teacher_b.user = "song"
teacher_b.rssi = -50

teacher_c = ConnectionRecord()
teacher_c.mac = "89ab.cdef.0123"
teacher_c.ap = "Playground"
teacher_c.user = "zhang"
teacher_c.rssi = -80

step = 0
records = [teacher_a, teacher_b]


def console_response():
    """
    此函数用于模拟教师的以下行为：
        王老师：从办公室到教室巡查，然后回到办公室；
        宋老师：一直停留在办公室；
        张老师：在操场跑步，信号不稳定。

    :return: None
    """
    global step
    if step == 0:
        teacher_a.ap = "Office-302"
        teacher_a.rssi = -40
    elif step == 3:
        teacher_a.rssi = -60
    elif step == 6:
        teacher_a.ap = "Hall"
    elif step == 9:
        teacher_a.rssi = -40
    elif step == 10:
        records.append(teacher_c)
    elif step == 12:
        teacher_a.ap = "G3"
        teacher_a.rssi = -60
    elif step == 15:
        teacher_a.ap = "G3-2"
        teacher_a.rssi = -50
    elif step == 18:
        teacher_a.rssi = -30
    elif step == 24:
        teacher_a.rssi = -50
        records.remove(teacher_c)
    elif step == 27:
        teacher_a.ap = "Hall"
    step = (step + 1) % 30

    content = "~\n~\n~\n~\n"
    for rec in records:
        # 模拟RSSI波动
        rec.rssi = int(rec.rssi) // 10 * 10 + random.randint(0, 9)
        content += (str(rec) + "\n")
    content += "~\n~\n~\n~\n"
    return content


if __name__ == '__main__':
    httpd = SocketServer.TCPServer((LISTENIP, PORT), ServerHandler)
    print "Serving HTTP on %s port %d ..." % (LISTENIP, PORT)
    httpd.serve_forever()
