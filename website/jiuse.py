# -*- coding:utf-8 -*-
# @Project        :XOVideos
# @FileName       :jiuse.py
# @Time           :2025/1/15 20:47
# @Author         :Viper373
# @Index          :https://viper3.top
# @Blog           :https://blog.viper3.top
# @Software       :PyCharm

import os
import time
import subprocess
import configparser
import requests
from lxml import html
from urllib.parse import urljoin
from pathvalidate import sanitize_filename
from urllib.parse import unquote
from tool_utils.log_utils import RichLogger
from tool_utils.string_utils import StringUtils
from tool_utils.api_utils import APIUtils
from tool_utils.mongo_utils import MongoUtils
from tool_utils.proxy_utils import ProxyUtils
from tool_utils.file_utils import S3Utils

rich_logger = RichLogger()
string_utils = StringUtils()
api_utils = APIUtils()
mongo_utils = MongoUtils()
proxy_utils = ProxyUtils()
s3_utils = S3Utils()


class Jiuse:
    def __init__(self):
        # 获取根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 读取配置文件
        jiuse_config = configparser.ConfigParser()
        jiuse_config.read(os.path.join(root_dir, 'config', 'jiuse.cfg'), encoding='utf-8')
        download_config = configparser.ConfigParser()
        download_config.read(os.path.join(root_dir, 'config', 'download.cfg'), encoding='utf-8')

        # 其他配置项
        self.video_dir = os.path.join(root_dir, jiuse_config.get('Video', 'VIDEO_DIR'))  # S3下载目录
        self.local_dir = jiuse_config.get('Video', 'LOCAL_DIR')  # 直接使用配置的绝对路径
        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.local_dir, exist_ok=True)

        self.index_url = jiuse_config.get('URL', 'INDEX_URL')
        self.m3u8_base_url = jiuse_config.get('URL', 'M3U8_BASE_URL')
        self.author_params = jiuse_config.get('Author', 'AUTHORS_NAME')

        author_url = jiuse_config.get('Author', 'AUTHOR_URL')
        self.author_base_url = f"{urljoin(self.index_url, author_url)}/"

        self.command = [
            download_config.get('N_m3u8DL-RE', 'TOOL'),
            download_config.get('N_m3u8DL-RE', 'URL'),
            download_config.get('N_m3u8DL-RE', 'SAVE_DIR'),
            download_config.get('N_m3u8DL-RE', 'SAVE_NAME_VALUE'),
            download_config.get('N_m3u8DL-RE', 'SAVE_NAME'),
            download_config.get('N_m3u8DL-RE', 'SAVE_NAME_VALUE'),
        ]
        self.pre_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5,ko;q=0.4,fr;q=0.3',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'referer': 'https://jiuse.ai/video/view/27f09ce959b3bdf2ca26',
            'sec-ch-ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
        }
        self.detail_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5,ko;q=0.4,fr;q=0.3',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'referer': 'https://jiuse.ai/author/%E7%8E%A9%E7%89%A9%E4%B8%8A%E5%BF%97',
            'sec-ch-ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
        }
        self.proxies = proxy_utils.get_proxy()

    @rich_logger
    def run_jiuse(self):
        self.get_author_info()
        self.get_video_info()
        self.get_download_videos(download_to_s3=False)

    @rich_logger
    def get_author_info(self):
        """
        获取作者信息并更新到数据库
        :return: None
        """
        author_list = []
        cfg_author_list = [author.strip() for author in self.author_params.split(',')]
        for author_name in cfg_author_list:
            author_info = {
                "author_name": author_name,
                "author_url": urljoin(self.author_base_url, author_name),
            }
            author_list.append(author_info)

            rich_logger.info(f"{author_name}信息获取成功")

        if author_list:
            mongo_utils.init_author_info(author_list, collection='jiuse')
        else:
            rich_logger.warning("没有获取到任何作者信息，跳过更新")

    @rich_logger
    def get_video_info(self):
        author_urls = mongo_utils.get_author_urls(collection='jiuse')
        for author in author_urls:
            author_name = author.get('作者名称')
            author_url = author.get('作者主页')
            author_videos_count = author.get('作者视频数量')
            try:
                author_document = mongo_utils.mongo_db['jiuse'].find_one({"作者名称": author_name})
                if not author_document or '作者视频列表' not in author_document:
                    mongo_videos = []
                else:
                    mongo_videos = author_document['作者视频列表']
                current_video_list_length = len(mongo_videos)

                if author_videos_count and current_video_list_length >= author_videos_count:
                    rich_logger.info(f"{author_name} 的视频列表已完整，跳过更新")
                    continue

                new_videos = []
                response = api_utils.requests_retry(url=author_url, headers=self.pre_headers, proxies=self.proxies, timeout=10)
                if response.status_code != 200:
                    rich_logger.error(f"获取 {author_name} 视频列表失败: {response.status_code}")
                    continue

                tree = html.fromstring(response.text)
                total_pages = self.get_total_pages(tree)

                for page in range(1, total_pages + 1):
                    page_url = f"{author_url}/{page}"
                    response = api_utils.requests_retry(url=page_url, headers=self.pre_headers, proxies=self.proxies, timeout=10)
                    if response.status_code != 200:
                        rich_logger.error(f"获取 {author_name} 第 {page} 页视频列表失败: {response.status_code}")
                        break

                    tree = html.fromstring(response.text)
                    videos = tree.xpath('//main/div[last()]//div[@id="rd4"]/div[1]/div')

                    if not videos:
                        rich_logger.info(f"{author_name} 第 {page} 页没有更多视频，结束抓取")
                        break

                    for video in videos:
                        video_info = self.extract_video_info(video)
                        if video_info:
                            video_url = video_info["视频链接"]

                            if any(v["视频链接"] == video_url for v in mongo_videos):
                                rich_logger.info(f"视频已存在，跳过: {video_info['视频标题']}")
                                continue

                            new_videos.append(video_info)
                            rich_logger.info(f"新增视频: {video_info['视频标题']}")

                    time.sleep(1)

                if new_videos:
                    mongo_utils.update_author_info(author_name, new_videos, current_video_list_length, collection='jiuse')
                else:
                    rich_logger.info(f"{author_name} 没有新视频，跳过更新")

            except Exception as e:
                rich_logger.exception(f"获取 {author_name} 视频信息失败: {e}")

    @rich_logger
    def get_download_videos(self, download_to_s3=True):
        author_urls = mongo_utils.get_author_urls(collection='jiuse')
        if download_to_s3:
            rich_logger.info(f"下载模式: S3，目录: {self.video_dir}")
        else:
            rich_logger.info(f"下载模式: 本地，目录: {self.local_dir}")

        for author in author_urls:
            author_name = author.get('作者名称')
            try:
                author_document = mongo_utils.mongo_db['jiuse'].find_one({"作者名称": author_name})
                if not author_document or '作者视频列表' not in author_document:
                    rich_logger.warning(f"{author_name} 没有视频列表，跳过下载")
                    continue

                videos = author_document['作者视频列表']
                for video in videos:
                    video_title = video['视频标题']

                    # 统一的文件存在性检查
                    if download_to_s3:
                        download_path = os.path.join(self.video_dir, author_name, f"{video_title}.mp4")
                        file_exists = s3_utils.check_s3_file_exists(download_path)
                        location = "S3"
                    else:
                        download_path = os.path.join(self.local_dir, author_name, f"{video_title}.mp4")
                        file_exists = os.path.exists(download_path)
                        location = "本地"

                    # 检查文件是否存在
                    if file_exists:
                        rich_logger.info(f"文件已存在于{location}，跳过: {author_name} - {video_title}")
                        # 如果文件存在但数据库状态不是1，更新状态
                        if video.get('下载状态') != 1:
                            mongo_utils.update_download_status(video, 1, collection='jiuse')
                        continue

                    # 如果文件不存在但数据库状态是1，记录警告
                    if video.get('下载状态') == 1:
                        rich_logger.warning(f"数据库显示已下载但文件不存在于{location}，重新下载: {author_name} - {video_title}")

                    video_url = video.get('视频链接')
                    download_url = self.get_m3u8_url(video_url)
                    if not download_url:
                        mongo_utils.update_download_status(video, 2, collection='jiuse')
                        continue

                    video_infos = {
                        "作者名称": author_name,
                        "视频标题": video_title,
                        "视频链接": video_url
                    }

                    # 统一的下载方法
                    self.download_video(video_infos, download_url, download_to_s3)

            except Exception as e:
                rich_logger.exception(f"{author_name} 下载视频失败: {e}")

    @rich_logger
    def download_video(self, video_infos, download_url, download_to_s3=True):
        """
        统一的视频下载方法，支持本地和S3两种模式
        :param video_infos: 视频信息字典
        :param download_url: 下载链接
        :param download_to_s3: True为S3模式，False为本地模式
        """
        author_name = sanitize_filename(video_infos.get('作者名称'))
        video_title = sanitize_filename(video_infos.get('视频标题'))

        # 根据下载模式设置路径
        if download_to_s3:
            download_path = os.path.join(self.video_dir, author_name, f"{video_title}.mp4")
            download_dir = os.path.join(self.video_dir, author_name)
        else:
            download_path = os.path.join(self.local_dir, author_name, f"{video_title}.mp4")
            download_dir = os.path.join(self.local_dir, author_name)

        # 确保目录存在
        os.makedirs(download_dir, exist_ok=True)

        try:
            # 构建 N_m3u8DL-RE 命令
            self.command[1] = download_url  # 更新下载链接
            self.command[3] = download_dir  # 更新保存目录
            self.command[5] = video_title  # 更新保存文件名

            result = subprocess.run(self.command, check=False)

            # 检查返回码
            if result.returncode != 0:
                rich_logger.error(f"下载失败: {author_name} - {video_title}，返回码：{result.returncode}")
                mongo_utils.update_download_status(video_infos, 2, collection='jiuse')
                return

            # S3模式需要额外的转码和上传步骤
            if download_to_s3:
                h264_video_path = s3_utils.ffmpeg_video_streaming(input_file=download_path)
                if h264_video_path:
                    upload_success = s3_utils.s4_upload_file(file_path=h264_video_path)
                    if upload_success:
                        rich_logger.info(f"下载并上传成功：{author_name} - {video_title}")
                        mongo_utils.update_download_status(video_infos, 1, collection='jiuse')
                    else:
                        rich_logger.error(f"上传失败: {author_name} - {video_title}")
                        mongo_utils.update_download_status(video_infos, 2, collection='jiuse')
                else:
                    rich_logger.error(f"文件转换失败: {author_name} - {video_title}")
                    mongo_utils.update_download_status(video_infos, 2, collection='jiuse')
            else:
                # 本地模式直接标记为成功
                rich_logger.info(f"下载成功: {author_name} - {video_title}")
                mongo_utils.update_download_status(video_infos, 1, collection='jiuse')

        except Exception as e:
            rich_logger.exception(f"{video_infos.get('视频标题')} 下载失败: {download_url}，错误信息：{e}")
            mongo_utils.update_download_status(video_infos, 2, collection='jiuse')

    @staticmethod
    def get_total_pages(tree):
        """
        获取视频页面的总页数
        :param tree: 页面解析树
        :return: int - 总页数
        """
        try:
            total_pages = tree.xpath('//ul[contains(@class, "pagination-list")]/li[last()-2]/a/text()')
            if total_pages:
                return int(total_pages[-1])  # 获取最后一页的页码
            return 1  # 如果没有分页，默认只有1页
        except Exception as e:
            rich_logger.warning(f"获取页数时发生错误: {e}")
            return 1  # 默认只有1页

    def get_m3u8_url(self, video_url, retries=3, delay=2):
        """
        获取视频的下载链接
        :param video_url: 视频链接
        :param retries: 最大重试次数
        :param delay: 每次重试之间的延迟（秒）
        :return: 下载链接或 None
        """
        attempt = 0
        while attempt < retries:
            try:
                response = api_utils.requests_retry(url=video_url, headers=self.detail_headers, proxies=self.proxies, timeout=10)
                if response.status_code == 200:
                    # 下载链接解析
                    download_url = urljoin(self.m3u8_base_url, unquote(string_utils.extract_jiuse_download_url(response.text).replace('\\/', '/')))
                    rich_logger.info(f"获取下载链接成功: {download_url}")
                    return download_url
                else:
                    rich_logger.error(f"获取下载链接失败: {response.status_code}丨{response.text}")
            except requests.RequestException as e:
                rich_logger.error(f"请求下载链接错误（尝试 {attempt + 1}/{retries}）: {e}")

            attempt += 1
            if attempt < retries:
                rich_logger.info(f"重试获取下载链接，等待 {delay} 秒...")
                time.sleep(delay)

        rich_logger.error(f"获取下载链接失败，已达到最大重试次数: {video_url}")
        return None

    def extract_video_info(self, video):
        """
        提取单个视频的信息
        :param video: 视频元素
        :return: dict - 视频信息
        """
        try:
            video_url = urljoin(self.index_url, video.xpath('.//a/@href')[0])
            video_title = sanitize_filename(video.xpath('.//h4/a/text()')[0])
            video_cover = video.xpath('.//img/@src')[0]
            video_duration = string_utils.format_duration(video.xpath('.//span[contains(@class, "duration")]/text()')[0])
            video_time = video.xpath('.//time/text()')[0]
            video_views = string_utils.format_views(video.xpath('.//time/parent::p/text()')[-1].strip().replace('|', ''))
            # 生成每个视频的字典信息
            return {
                "视频标题": video_title,
                "视频封面": video_cover,
                "视频链接": video_url,
                "视频时长": video_duration,
                "视频发布时间": video_time,
                "视频观看次数": video_views,
                "下载状态": 0  # 状态：0代表未下载
            }
        except Exception as e:
            rich_logger.warning(f"提取视频信息失败: {e}")
            return None


def main():
    jiuse = Jiuse()
    jiuse.run_jiuse()
