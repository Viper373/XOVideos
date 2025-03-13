# -*- coding:utf-8 -*-
# @Project        :XOVideos
# @FileName       :pornhub.py
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


class Pornhub:

    def __init__(self):
        # 获取根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 读取配置文件
        ph_config = configparser.ConfigParser()
        ph_config.read(os.path.join(root_dir, 'config', 'pornhub.cfg'), encoding='utf-8')
        download_config = configparser.ConfigParser()
        download_config.read(os.path.join(root_dir, 'config', 'download.cfg'), encoding='utf-8')

        # 其他配置项
        self.video_dir = os.path.join(root_dir, ph_config.get('Video', 'VIDEO_DIR'))
        os.makedirs(self.video_dir, exist_ok=True)

        self.index_url = ph_config.get('URL', 'INDEX_URL')
        user_url = ph_config.get('User', 'USER_URL')
        fav_params = ph_config.get('Favorites', 'FAV_URL')
        sub_params = ph_config.get('Subscriptions', 'SUB_URL')
        self.fav_url = urljoin(urljoin(self.index_url, user_url), fav_params)
        self.sub_url = urljoin(urljoin(self.index_url, user_url), sub_params)
        self.command = [
            download_config.get('STREAMLINK', 'TOOL'),
            download_config.get('STREAMLINK', 'URL'),
            download_config.get('STREAMLINK', 'QUALITY'),
            download_config.get('STREAMLINK', 'OPTIONS'),
            download_config.get('STREAMLINK', 'OUTPUT_FILE')
        ]
        self.pre_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5,ko;q=0.4,fr;q=0.3',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://cn.pornhub.com/users/d409917/videos/favorites',
            'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-full-version': '"131.0.2903.146"',
            'sec-ch-ua-full-version-list': '"Microsoft Edge";v="131.0.2903.146", "Chromium";v="131.0.6778.265", "Not_A Brand";v="24.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        }
        self.detail_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5,ko;q=0.4,fr;q=0.3',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://cn.pornhub.com/model/jiojingzhutv/videos',
            'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-full-version': '"131.0.2903.146"',
            'sec-ch-ua-full-version-list': '"Microsoft Edge";v="131.0.2903.146", "Chromium";v="131.0.6778.265", "Not_A Brand";v="24.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        }
        self.cookies = os.getenv('PH_COOKIES')
        self.proxies = proxy_utils.get_proxy()

    @rich_logger
    def run_pornhub(self):
        self.get_author_info()
        self.get_video_info()
        self.get_download_videos()

    @rich_logger
    def get_author_info(self):
        """
        获取视频作者信息并更新到数据库
        :return: None
        """
        author_list = []  # 用于存储所有作者的信息

        try:
            # 发起请求获取订阅页面内容
            response = api_utils.requests_retry(url=self.sub_url, headers=self.pre_headers, cookies=self.cookies, proxies=self.proxies, timeout=10)
            if response.status_code != 200:
                rich_logger.exception(f"获取订阅作者信息失败: {response.status_code}丨{response.text}")
                return  # 返回空列表，表示未成功获取数据

            tree = html.fromstring(response.content)

            author_elements = tree.xpath('//ul[@id="moreData"]//li')  # 获取所有作者元素
            # 提取每个作者的信息并加入到author_list
            for author in author_elements:
                author_name = None
                try:
                    author_id = author.xpath('.//a[@data-type="user"]//@data-userid')[0]
                    author_url = urljoin(self.index_url, author.xpath('.//a[@data-type="user"]/@href')[0]) + '/videos'
                    author_avatar = author.xpath('.//a[@data-type="user"]//img[@class="avatar avatarTrigger"]/@src')[0]
                    author_name = author.xpath('.//a[@class="usernameLink"]//@title')[0]

                    rich_logger.info(f"作者名：{author_name}, 主页：{author_url}")

                    # 生成每个作者的字典信息，并添加到author_list
                    author_info = {
                        "author_id": author_id,
                        "author_name": author_name,
                        "author_avatar": author_avatar,
                        "author_url": author_url,
                    }
                    author_list.append(author_info)

                    rich_logger.info(f"{author_name}信息获取成功")

                except Exception as e:
                    rich_logger.exception(f"获取{author_name}信息失败: {e}")

            if author_list:
                # 调用Mongo写入方法进行批量写入
                mongo_utils.init_author_info(author_list)
            else:
                rich_logger.warning("没有获取到任何作者信息，跳过更新。")

        except Exception as e:
            rich_logger.error(f"获取视频作者信息错误: {e}")

    @rich_logger
    def get_video_info(self):
        author_urls = mongo_utils.get_author_urls()
        for author in author_urls:
            author_name = author.get('作者名称')
            author_url = author.get('作者主页')

            try:
                author_document = mongo_utils.mongo_db['pornhub'].find_one({"作者名称": author_name})
                if not author_document or '作者视频列表' not in author_document:
                    mongo_video_list = []
                else:
                    mongo_video_list = author_document['作者视频列表']

                # 获取网页视频总数
                response = api_utils.requests_retry(url=author_url, headers=self.pre_headers, cookies=self.cookies, proxies=self.proxies, timeout=10)
                tree = html.fromstring(response.content)
                total_pages = self.get_total_pages(tree)
                video_counts = 0
                for i in range(1, total_pages + 1):
                    page_url = author_url if i == 1 else f"{author_url}?page={i}"
                    response = api_utils.requests_retry(url=page_url, headers=self.pre_headers, cookies=self.cookies, proxies=self.proxies, timeout=10)
                    tree = html.fromstring(response.content)
                    video_counts += int(tree.xpath('count(//ul[@id="mostRecentVideosSection"]//li)'))

                # 判断是否需要爬取
                if len(mongo_video_list) == video_counts:
                    rich_logger.info(f"{author_name} 的视频数量未更新，跳过该作者")
                    continue

                rich_logger.info(f"{author_name}数据库视频数量：[{len(mongo_video_list)}]，源视频数量：[{video_counts}]丨开始爬取")

                # 爬取新视频
                new_videos = []
                existing_urls = set(video['视频链接'] for video in mongo_video_list)
                for page in range(1, total_pages + 1):
                    page_url = author_url if page == 1 else f"{author_url}?page={page}"
                    response = api_utils.requests_retry(url=page_url, headers=self.pre_headers, cookies=self.cookies, proxies=self.proxies, timeout=30)
                    tree = html.fromstring(response.content)
                    video_elements = tree.xpath('//ul[@id="mostRecentVideosSection"]//li')

                    page_new_videos = []
                    for video in video_elements:
                        video_info = self.extract_video_info(video)
                        if video_info and video_info['视频链接'] not in existing_urls:
                            page_new_videos.append(video_info)
                            existing_urls.add(video_info['视频链接'])

                    new_videos.extend(page_new_videos)
                    if not page_new_videos:
                        break  # 没有新视频，停止爬取

                # 更新数据库
                if new_videos:
                    mongo_utils.update_author_info(author_name, new_videos)
                    rich_logger.info(f"{author_name} 的视频信息更新成功，新增 {len(new_videos)} 个视频")

            except Exception as e:
                rich_logger.error(f"获取{author_name}的视频信息错误: {e}")

    @rich_logger
    def get_download_videos(self, collection="pornhub"):
        """
        获取视频下载链接并进行实时下载
        :param collection: 集合名称，默认为 'pornhub'
        :return: None
        """
        try:
            # 查询 MongoDB 中所有包含 "视频链接" 字段且下载状态为 0 或 2 的文档
            cursor = mongo_utils.mongo_db[collection].find({
                "作者视频列表.视频链接": {"$exists": True},  # 确保文档中存在 "视频链接" 字段
                "作者视频列表.下载状态": {"$in": [0, 2]}  # 下载状态为 0（未开始）或 2（下载失败）
            })

            # 遍历每个文档
            for doc in cursor:
                # 提取作者名称，假设在文档根级字段中
                author_name = doc.get('作者名称')  # 获取作者名称

                # 如果作者名称不存在，跳过该文档
                if not author_name:
                    continue

                # 遍历作者视频列表中的每个视频
                for video in doc.get('作者视频列表', []):
                    # 提取视频信息
                    video_title = video.get('视频标题')  # 获取视频标题
                    video_url = video.get('视频链接')  # 获取视频链接
                    download_status = video.get('下载状态')  # 获取视频下载状态
                    video_infos = {
                        "作者名称": author_name,
                        "视频链接": video_url,
                        "视频标题": video_title,
                    }
                    download_url = self.get_m3u8_url(video_url)  # 获取视频下载链接
                    # 确保视频信息完整，并且下载状态为 0 或 2（即未开始或下载失败）
                    if download_status in [0, 2]:
                        rich_logger.info(f"开始下载{author_name} - {video_title}")
                        self.download_video(video_infos, download_url)

        except Exception as e:
            rich_logger.error(f"下载视频时发生错误: {e}")

    @rich_logger
    def download_video(self, video_infos, download_url):
        try:
            author_name = video_infos.get('作者名称')
            video_title = video_infos.get('视频标题')
            download_path = os.path.join(self.video_dir, author_name, f"{video_title}.mp4")
            
            # 确保作者目录存在
            os.makedirs(os.path.dirname(download_path), exist_ok=True)

            # 先检查 S3 上是否已存在该文件
            if s3_utils.check_s3_file_exists(download_path):
                rich_logger.info(f"S3 上已存在文件: {author_name} - {video_title}，跳过下载和转换")
                mongo_utils.update_download_status(video_infos, 1)  # 更新为已下载状态
                return

            # 判断本地文件是否已经存在
            if os.path.exists(download_path):
                rich_logger.info(f"{download_path} 已经存在，进行转换和上传")
                # 进行 ffmpeg 转换
                h264_video_path = s3_utils.ffmpeg_video_streaming(input_file=download_path)
                if h264_video_path:
                    # 上传到 S3
                    upload_success = s3_utils.s4_upload_file(file_path=h264_video_path)
                    if upload_success:
                        mongo_utils.update_download_status(video_infos, 1)
                    else:
                        rich_logger.error(f"文件存在但上传失败: {author_name} - {video_title}")
                        mongo_utils.update_download_status(video_infos, 2)
                else:
                    rich_logger.error(f"文件转换失败: {author_name} - {video_title}")
                    mongo_utils.update_download_status(video_infos, 2)
                return

            # 文件不存在，需要下载
            self.command[1] = download_url
            self.command[-1] = download_path

            # 执行 streamlink 命令，并捕获输出
            result = subprocess.run(self.command)

            if result.returncode != 0:
                rich_logger.error(f"下载失败: {author_name} - {video_title}， 错误信息：{result.stderr}")
                mongo_utils.update_download_status(video_infos, 2)
            else:
                # 下载成功，进行转换
                h264_video_path = s3_utils.ffmpeg_video_streaming(input_file=download_path)
                if h264_video_path:
                    # 上传到 S3
                    upload_success = s3_utils.s4_upload_file(file_path=h264_video_path)
                    if upload_success:
                        rich_logger.info(f"下载并上传成功：{author_name} - {video_title}")
                        mongo_utils.update_download_status(video_infos, 1)
                    else:
                        rich_logger.error(f"上传失败: {author_name} - {video_title}")
                        mongo_utils.update_download_status(video_infos, 2)
                else:
                    rich_logger.error(f"文件转换失败: {author_name} - {video_title}")
                    mongo_utils.update_download_status(video_infos, 2)

        except Exception as e:
            mongo_utils.update_download_status(video_infos, 2)
            rich_logger.exception(f"{video_infos.get('视频标题')} 下载失败: {download_url}， 错误信息：{e}")

    @staticmethod
    def get_total_pages(tree):
        """
        获取视频页面的总页数
        :param tree: 页面解析树
        :return: int - 总页数
        """
        try:
            total_pages = tree.xpath('//div[@class="pagination3 paginationGated"]//ul/li[contains(@class, "page_number")]/a/text()')
            if total_pages:
                return int(total_pages[-1])  # 获取最后一页的页码
            return 1  # 如果没有分页，默认只有1页
        except Exception as e:
            rich_logger.warning(f"获取页数时发生错误: {e}")
            return 1  # 默认只有1页

    def get_m3u8_url(self, video_url, retries=3, delay=2):
        """
        获取视频的下载链接，并立即下载视频。
        :param video_url: 视频链接
        :param retries: 最大重试次数
        :param delay: 每次重试之间的延迟（秒）
        :return: None
        """
        attempt = 0
        while attempt < retries:
            try:
                response = api_utils.requests_retry(url=video_url, headers=self.detail_headers, cookies=self.cookies, proxies=self.proxies, timeout=10)
                if response.status_code == 200:
                    # 下载链接解析
                    download_url = unquote(string_utils.extract_video_download_url(response.text).replace('\\/', '/'))

                    rich_logger.info(f"获取下载链接成功: {download_url}")
                    # 立即下载视频
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
            video_title = sanitize_filename(video.xpath('.//a/@title')[0])
            video_cover = video.xpath('.//img/@src')[0]
            video_duration = video.xpath('.//var[@class="duration"]/text()')[0]
            video_views = video.xpath('.//span[@class="views"]//var/text()')[0]

            # 生成每个视频的字典信息
            return {
                "视频标题": video_title,
                "视频封面": video_cover,
                "视频链接": video_url,
                "视频时长": video_duration,
                "视频观看次数": video_views,
                "下载状态": 0  # 状态：0代表未下载
            }
        except Exception as e:
            rich_logger.warning(f"提取视频信息失败: {e}")
            return None
