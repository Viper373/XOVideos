# -*- coding: utf-8 -*-
# @Project   :td_gsc_scraper
# @FileName  :file_utils.py
# @Time      :2024/10/11 11:00
# @Author    :Zhangjinzhao
# @Software  :PyCharm

import os
import time
import boto3
import mimetypes
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
    def s4_upload_file(self, file_path, delete_on_success=True, delete_on_failure=False):
        start_time = time.time()

        try:
            # 路径合规性检查
            if not os.path.isfile(file_path):
                rich_logger.error(f"文件不存在或不可读: {file_path}")
                return False

            # 分割路径
            parts = file_path.split("/")
            xovideos_indices = [i for i, part in enumerate(parts) if part == "XOVideos"]

            # 防御性检查
            if len(xovideos_indices) < 2:
                rich_logger.error(f"路径中未找到足够的 'XOVideos' 目录: {file_path}")
                return False
            videos_index = xovideos_indices[1]
            s3_key = "/".join(parts[videos_index:])

            # 检查文件是否存在
            try:
                self.s3_client.head_object(Bucket=self.bucket, Key=s3_key)
                rich_logger.info(f"文件已存在，跳过上传: {s3_key}")

                if delete_on_success:
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        rich_logger.error(f"删除本地文件失败: {e}")
                return True
            except ClientError as e:
                error_code = e.response['Error'].get('Code', 'Unknown')
                if error_code != '404':
                    raise

            # 动态检测 MIME 类型
            content_type, _ = mimetypes.guess_type(file_path)
            extra_args = {
                "ContentType": content_type or "application/octet-stream",
                "ContentDisposition": "inline"
            }

            # 记录文件大小
            file_size = os.path.getsize(file_path)
            size_units = ['B', 'KB', 'MB', 'GB', 'TB']
            size_index = 0
            while file_size >= 1024 and size_index < len(size_units) - 1:
                file_size /= 1024.0
                size_index += 1
            size_str = f"{int(file_size)} {size_units[size_index]}" if size_index == 0 else f"{file_size:.2f} {size_units[size_index]}".rstrip('0').rstrip('.')
            rich_logger.info(f"开始上传: {s3_key}，大小: {size_str}")

            # 执行上传
            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=self.bucket,
                Key=s3_key,
                ExtraArgs=extra_args
            )
            rich_logger.info(f"上传成功: {s3_key}")

            # 上传成功后删除本地文件
            if delete_on_success:
                try:
                    os.remove(file_path)
                except OSError as e:
                    rich_logger.error(f"删除本地文件失败: {e}")
            return True

        except ClientError as e:
            error_code = e.response['Error'].get('Code', 'Unknown')
            rich_logger.error(f"上传失败 ({error_code}): {e}")
            if delete_on_failure:
                try:
                    os.remove(file_path)
                except OSError as err:
                    rich_logger.error(f"删除本地文件失败: {err}")
            return False
        except Exception as e:
            rich_logger.exception(f"未知错误: {e}")
            if delete_on_failure:
                try:
                    os.remove(file_path)
                except OSError as err:
                    rich_logger.error(f"删除本地文件失败: {err}")
            return False

    @staticmethod
    @rich_logger
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
