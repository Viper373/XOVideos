# -*- coding: utf-8 -*-
# @Project   :td_gsc_scraper
# @FileName  :file_utils.py
# @Time      :2024/10/11 11:00
# @Author    :Zhangjinzhao
# @Software  :PyCharm

import os
import io
import json
import requests
import pandas as pd
from datetime import datetime
from tool_utils.log_utils import RichLogger

rich_logger = RichLogger()


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super(CustomJSONEncoder, self).default(obj)


class ExcelManager:
    def __init__(self, base_dir='excel'):
        """
        初始化 FileManager 类。

        :param base_dir: 基础目录，用于存储 Excel 文件。
        """
        self.base_dir = base_dir
        self.today = datetime.today().strftime('%Y-%m-%d')
        self.project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.excel_path = os.path.join(self.project_path, self.base_dir, self.today)
        # os.makedirs(self.excel_path, exist_ok=True)

    @rich_logger
    def write_indexing_excel(self, response: requests.Response, domain_str: str, index: str):
        """
        将响应中的二进制数据写入文件，按照指定的目录结构保存。

        :param response: 请求返回的 Response 对象。
        :param domain_str: 域名字符串。
        :param index: 索引字符串，作为文件名。
        """
        domain_dir = os.path.join(self.excel_path, domain_str.split(':')[-1])
        os.makedirs(domain_dir, exist_ok=True)
        file_path = os.path.join(self.excel_path, domain_str.split(':')[-1], f"{index}.xlsx")
        # 检查响应状态码并写入文件
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
                rich_logger.info(f"{file_path} 写入成功")
        else:
            rich_logger.error(f"{file_path} 写入失败：{response.status_code}")

    @rich_logger
    def write_performance_excel(self, response: requests.Response, domain_str: str, excel_name: str | bool):
        """
        将响应中的二进制数据写入文件，按照指定的目录结构保存。
        :param response: 请求返回的 Response 对象。
        :param domain_str: 域名字符串。
        :param excel_name: excel文件名。
        """
        if not excel_name:
            return
        domain_dir = os.path.join(self.excel_path, domain_str.split(':')[-1])
        os.makedirs(domain_dir, exist_ok=True)
        file_path = os.path.join(self.excel_path, domain_dir, excel_name)
        # 检查响应状态码并写入文件
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
                rich_logger.info(f"{file_path} 写入成功")
        else:
            rich_logger.error(f"{file_path} 写入失败：{response.status_code}")

    @staticmethod
    @rich_logger
    def sheet_content_to_json(response: requests.Response, sheet_name: str = None) -> dict | list:
        """
        从 response.content 中读取 Excel 文件，并将其转换为 JSON。
        :param response: 请求返回的 Response 对象。
        :param sheet_name: 工作表名称。
        :return: 包含所有工作表数据的 JSON 字符串。
        """
        if response.status_code != 200:
            rich_logger.error(f"无法读取 Excel 文件: {response.status_code}")
            return {}

        # 使用 BytesIO 将响应内容转换为文件流
        excel_file = io.BytesIO(response.content)

        # 使用 pandas 读取 Excel 文件
        if sheet_name:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            json_data = df.to_dict(orient='records')
            rich_logger.info(f"成功将工作表 '{sheet_name}' 转换为 JSON")
            return json_data
        else:
            # 读取所有工作表
            xls = pd.ExcelFile(excel_file)
            json_data = {}
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet)
                json_data[sheet] = df.to_dict(orient='records')
                rich_logger.info(f"成功将工作表 '{sheet}' 转换为 JSON")
            return json_data
