# -*- coding: utf-8 -*-
# @Project   :td_gsc_sc_scraper
# @FileName  :string_utils.py
# @Time      :2024/10/11 10:45
# @Author    :Zhangjinzhao
# @Software  :PyCharm

import re
import hashlib
from tool_utils.log_utils import RichLogger

rich_logger = RichLogger()


class StringUtils:

    def __init__(self):
        pass

    def md5_encode(self, str_data: str) -> str:
        """
        对字符串进行MD5加密。
        :param str_data: 需要加密的字符串
        :return: 加密后的字符串
        """
        md5_value = hashlib.md5()
        md5_value.update(str_data.encode('utf-8'))
        return md5_value.hexdigest()

    def extract_pornhub_download_url(self, response_text):
        """
        使用正则表达式从响应文本中提取视频下载链接。
        :param response_text: 包含视频信息的JSON格式文本
        :return: 第一个videoUrl的值或None
        """
        response_text_cleaned = re.sub(r'\\/', '/', response_text)
        try:
            video_url = re.findall(r'"videoUrl":"(.*?)"', response_text_cleaned)
            if len(video_url) >= 2:
                return video_url[-2]
            elif video_url:
                return video_url[0]
            else:
                rich_logger.warning("未找到视频下载链接")
                return None
        except Exception as e:
            rich_logger.exception(f"提取视频链接时发生错误: {e}")
            return None

    def extract_jiuse_download_url(self, response_text):
        """
        使用正则表达式从响应文本中提取视频下载链接。
        :param response_text: 包含视频信息的JSON格式文本
        :return: 第一个videoUrl的值或None
        """
        try:
            video_url = re.findall(r'"hls":"([^"]+)"', response_text)
            if video_url:
                hls_path = video_url[0].replace('\\/', '/')
                return hls_path
            else:
                rich_logger.warning("未找到视频下载链接")
                return None
        except Exception as e:
            rich_logger.exception(f"提取视频链接时发生错误: {e}")
            return None

    def format_duration(self, time_str: str) -> str:
        """
        如果时间字符串的小时部分为 '00'，去除小时部分及其冒号。
        :param time_str: 输入时间字符串，格式为 'xx:xx:xx'
        :return: 处理后的时间字符串
        """
        if time_str.startswith("00:"):
            return time_str[3:]  # 去除前三个字符（'00:'），返回 'xx:xx'
        return time_str  # 原样返回

    def format_views(self, play_str: str) -> str:
        """
        从播放次数字符串中提取数字并格式化为指定格式。
        :param play_str: 输入字符串，例如 ' 2.7万次播放', '1606次播放', '941次播放'
        :return: 格式化后的字符串，例如 '27k', '1.6k', '941'
        """
        play_str = play_str.strip()
        match = re.search(r'(\d*\.?\d*)\s*万?次播放', play_str)
        if not match:
            return play_str
        number_str = match.group(1)

        if '万' in play_str:
            number = float(number_str) * 10  # 万 = 10k
            # 如果是整数，去掉 .0，例如 27.0k -> 27k
            if number.is_integer():
                return f"{int(number)}k"
            return f"{number:.1f}k"
        else:
            number = int(number_str)
            if number >= 1000:
                result = number / 1000
                # 如果是整数，去掉 .0，例如 1.0k -> 1k
                if result.is_integer():
                    return f"{int(result)}k"
                return f"{result:.1f}k"
            return str(number)
