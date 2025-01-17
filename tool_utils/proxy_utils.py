# -*- coding: utf-8 -*-
# @Project   :td_gsc_bot
# @FileName  :proxy_utils.py
# @Time      :2024/10/14 11:15
# @Author    :Zhangjinzhao
# @Software  :PyCharm
import random


class ProxyUtils:
    def __init__(self):
        pass

    @staticmethod
    def get_proxy():
        proxy_host = '103.214.44.131'
        proxy_port = 12321
        proxy_user = 'testdaily'
        proxy_pwd = f'proxy1024_country-us_session-{int(random.random() * 10000000)}_lifetime-3m'
        return f'http://{proxy_user}:{proxy_pwd}@{proxy_host}:{proxy_port}'
