# -*- coding: utf-8 -*-
# @Project   :td_gsc_scraper
# @FileName  :file_utils.py
# @Time      :2024/10/11 11:00
# @Author    :Zhangjinzhao
# @Software  :PyCharm

import os
import time
import boto3
import subprocess
from botocore.exceptions import ClientError
from tool_utils.log_utils import RichLogger

rich_logger = RichLogger()


class S3Utils:
    def __init__(self):
        s3endpoint = os.getenv('S3_ENDPOINT')  # 请填入控制台 “Bucket 设置” 页面底部的 “Endpoint” 标签中的信息
        s3region = os.getenv('S3_REGION')
        s3accessKeyId = os.getenv('S3_ACCESS_KEY')  # 请到控制台创建子账户，并为子账户创建相应 accessKey
        s3SecretKeyId = os.getenv('S3_SECRET_KEY')  # ！！切记，创建子账户时，需要手动为其分配具体权限！！
        self.bucket = os.getenv('S3_BUCKET')  # 请填入控制台 “Bucket 列表” 页面的 “Bucket 名称”
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=s3accessKeyId,
            aws_secret_access_key=s3SecretKeyId,
            endpoint_url=s3endpoint,
            region_name=s3region
        )

    @rich_logger
    def s4_upload_file(self, file_path):
        """
        上传文件至缤纷云S4
        自动跳过已存在的文件
        本地文件可读性校验
        路径合规性检查
        网络重试机制
        :param file_path: 本地文件路径
        :return: None
        """
        start_time = time.time()

        try:
            # 分割路径
            parts = file_path.split("/")

            # 查找所有 "XOVideos" 的位置
            xovideos_indices = [i for i, part in enumerate(parts) if part == "XOVideos"]

            # 取第二个出现的 XOVideos 位置
            videos_index = xovideos_indices[1]

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
            self.s3_client.upload_file(
                filename=file_path,
                bucket=self.bucket,
                key=s3_key,
                ExtraArgs={
                    "ContentType": "video/mp4",
                    "ContentDisposition": "inline"  # 允许浏览器预览
                }
            )
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

    @staticmethod
    def ffmpeg_video_streaming(input_file):
        """
        使用FFmpeg将视频转换为H.264格式，并进行流优化处理，使其能够流式传输。

        参数:
        - input_file: 输入的视频文件路径
        - output_file: 输出的优化后的视频文件路径

        返回:
        - 成功: 返回输出文件的路径
        - 失败: 返回 None
        """
        output_file = input_file.replace('.mp4', 'h264.mp4')
        command = [
            'ffmpeg',
            '-i', input_file,
            '-c:v', 'libx264',  # 使用H.264编解码器
            'crf', '0',  # 最低 CRF 值（0-51，0 为无损，通常 18-28 是合理范围）
            '-c:a', 'copy',  # 保留原始音频
            '-movflags', 'faststart',  # 使视频文件头放在文件开始处，优化流媒体播放
        ]

        try:
            # 使用 subprocess.run 执行 FFmpeg 命令，并捕获 stdout 和 stderr 以便调试
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            rich_logger.info(f"视频优化和H.264转换完成: {output_file}")
            os.remove(input_file)  # 删除原视频，保留流式优化视频
            os.rename(output_file, input_file)  #
            return output_file
        except subprocess.CalledProcessError as e:
            # 捕获 FFmpeg 命令的返回码和输出
            rich_logger.exception(f"视频优化失败: {output_file}\n错误信息: {e.stderr.decode('utf-8')}")
            return None
        except Exception as e:
            # 捕获其他意外错误
            rich_logger.error(f"未知错误: {e}")
            return None
