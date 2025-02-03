# -*- coding: utf-8 -*-
# @Project   :td_gsc_scraper
# @FileName  :api_utils.py
# @Time      :2024/10/12 10:34
# @Author    :Zhangjinzhao
# @Software  :PyCharm

import time
import requests
from requests.exceptions import RequestException
from tool_utils.log_utils import RichLogger
from tool_utils.proxy_utils import ProxyUtils

rich_logger = RichLogger()
proxy_utils = ProxyUtils()


class APIUtils:

    def __init__(self):
        self.proxies = proxy_utils.get_proxy()

    def requests_retry(self, url, headers=None, cookies=None, params=None, retries=5, delay=2, timeout=30):
        """
        发起请求并加入重试机制。
        :param url: 请求的URL
        :param headers: 请求头
        :param cookies: 请求Cookies
        :param params: URL参数
        :param retries: 最大重试次数
        :param delay: 每次重试的间隔时间（秒）
        :param timeout: 请求超时时间（秒）
        :return: requests.Response对象 或 None
        """
        attempt = 0
        while attempt < retries:
            try:
                response = requests.get(url, headers=headers, cookies=cookies, params=params, proxies=self.proxies, timeout=timeout)
                if response.status_code == 200:
                    return response
                else:
                    rich_logger.error(f"请求失败: {response.status_code} | URL: {url}")
            except RequestException as e:
                rich_logger.error(f"请求出错: {e} | 尝试 {attempt + 1}/{retries} 次，URL: {url}")

            attempt += 1
            if attempt < retries:
                rich_logger.info(f"重试请求，等待 {delay} 秒... (尝试 {attempt + 1}/{retries})")
                time.sleep(delay)

        rich_logger.error(f"请求失败，已达到最大重试次数: {url}")
        return None


if __name__ == '__main__':
    api_utils = APIUtils()
    # gscType = 'Not found (404)'
    # projectSource = 'aicoloringpages.net'
    # date = api_utils.get_recent_time(gscType=gscType, projectSource=projectSource)
    # print(type(date))
