# -*- coding: utf-8 -*-
# @Project   :td_gsc_scraper
# @FileName  :file_utils.py
# @Time      :2024/10/11 11:00
# @Author    :Zhangjinzhao
# @Software  :PyCharm

import os
import time
import boto3
from botocore.exceptions import ClientError
from tool_utils.log_utils import RichLogger

rich_logger = RichLogger()


class S3Utils:
    def __init__(self):
        s3endpoint = os.getenv('S3_ENDPOINT')  # 请填入控制台 “Bucket 设置” 页面底部的 “Endpoint” 标签中的信息
        s3region = os.getenv('S3_REGION')
        s3accessKeyId = os.getenv('S3_ACCESS_KEY')  # 请到控制台创建子账户，并为子账户创建相应 accessKey
        s3SecretKeyId = os.getenv('S3_SECRET_KEY')  # ！！切记，创建子账户时，需要手动为其分配具体权限！！
        self.bucket = 'viper3'
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=s3accessKeyId,
            aws_secret_access_key=s3SecretKeyId,
            endpoint_url=s3endpoint,
            region_name=s3region
        )

    def upload_file(self, file_path):
        """
        自动跳过已存在的文件
        本地文件可读性校验
        路径合规性检查
        网络重试机制
        :param file_path: 本地文件路径
        :return: None
        """
        start_time = time.time()

        try:
            # 统一替换所有路径分隔符为 S3 适用的正斜杠
            unified_path = file_path.replace("\\", "/")

            # 强制校验路径中必须包含 '/XOVideos/videos/' 目录
            if "/XOVideos/videos/" not in unified_path:
                raise ValueError("文件路径必须包含 '/XOVideos/videos/' 目录作为根节点")

            # 分割路径并定位第二个 XOVideos 的位置
            parts = unified_path.split("/")

            # 查找所有 XOVideos 的索引位置
            xov_indices = [i for i, part in enumerate(parts) if part == "XOVideos"]

            # 检查是否有至少两个 XOVideos
            if len(xov_indices) < 2:
                raise ValueError("路径中需要包含至少两个 'XOVideos' 目录")

            # 取第二个 XOVideos 的索引
            videos_index = xov_indices  # 索引从 0 开始，xov_indices 是第二个出现的位置

            # 组合 S3 对象键（XOVideos 之后的路径部分）
            s3_key = "/".join(parts[videos_index:])
            try:
                # HEAD 请求检查对象元数据（低开销）
                self.s3_client.head_object(Bucket=self.bucket, Key=s3_key)
                end_time = time.time()
                rich_logger.info(f"缤纷云文件已存在，跳过上传://{self.bucket}/{s3_key}丨耗时：{end_time - start_time:.2f} 秒")
                os.remove(file_path)
                return True
            except ClientError as e:
                error_code = e.response['Error'].get('Code', 'Unknown')
                if error_code != '404':
                    # 非"文件不存在"错误（如权限问题），直接抛出异常
                    raise
            # 获取文件大小并记录日志
            file_size = os.path.getsize(file_path)

            # 智能转换文件大小单位
            size_units = ['B', 'KB', 'MB', 'GB', 'TB']
            size_index = 0
            while file_size >= 1024 and size_index < len(size_units) - 1:
                file_size /= 1024.0
                size_index += 1

            # 根据单位类型调整显示精度
            if size_index == 0:  # 字节
                size_str = f"{int(file_size)} {size_units[size_index]}"
            else:
                size_str = f"{file_size:.2f} {size_units[size_index]}".replace(".00", "")  # 优化整数显示

            rich_logger.info(f"开始上传缤纷云: {s3_key}，文件大小: {size_str}")

            # 执行上传
            self.s3_client.upload_file(file_path, self.bucket, s3_key)
            end_time = time.time()
            rich_logger.info(f"缤纷云上传成功://{self.bucket}/{s3_key}丨耗时：{end_time - start_time:.2f} 秒")
            os.remove(file_path)
            return True

        except ClientError as e:
            error_code = e.response['Error'].get('Code', 'Unknown')
            end_time = time.time()
            rich_logger.error(f"缤纷云操作失败 ({error_code}): {str(e)}丨耗时：{end_time - start_time:.2f} 秒")
            os.remove(file_path)
            return False

        except Exception as e:
            end_time = time.time()
            rich_logger.exception(f"未知错误: {str(e)}丨耗时：{end_time - start_time:.2f} 秒")
            os.remove(file_path)
            return False

