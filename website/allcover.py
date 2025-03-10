# -*- coding:utf-8 -*-
# @Project        :XOVideos
# @FileName       :allcover.py
# @Time           :2025/3/9 05:34
# @Software       :PyCharm
# @Author         :Viper373
# @Index          :https://viper3.top
# @Blog           :https://blog.viper3.top

import re
import asyncio
import aiohttp
from tool_utils.mongo_utils import MongoUtils
from tool_utils.api_utils import GitHubUtils
from tool_utils.log_utils import RichLogger

rich_logger = RichLogger()
mongo_utils = MongoUtils()
gh_utils = GitHubUtils()


class AllCover:
    def __init__(self):
        pass

    @rich_logger
    def run_cover(self):
        """启动封面上传流程"""
        self.ph_cover_process()

    @staticmethod
    async def batch_upload_cover_urls(cover_info_list, gh_utils, mongo_utils, max_concurrency=5, retries=3, delay=2):
        """批量异步上传封面"""
        semaphore = asyncio.Semaphore(max_concurrency)

        async def upload_with_semaphore(cover_info):
            async with semaphore:
                author_name = cover_info["作者名称"]
                video_title = cover_info["视频标题"]
                cover_url = cover_info["视频封面"]
                video_url = cover_info["视频链接"]

                # 清理标题中的非法字符
                safe_title = re.sub(r'[\/:*?"<>|]', '_', video_title)

                # 获取文件后缀
                file_extension = cover_url.split('.')[-1]
                if '.' not in file_extension or len(file_extension) > 4:
                    file_extension = 'jpg'

                # 构建目标路径
                target_path = f"{author_name}/{safe_title}.{file_extension}"

                # 尝试上传
                success = await gh_utils.async_upload_from_url(session, cover_url, target_path, retries=retries, delay=delay)

                # 更新MongoDB状态
                new_status = 1 if success else 2
                mongo_utils.update_cover_status(author_name, video_url, new_status)

                return success

        async with aiohttp.ClientSession() as session:
            tasks = [upload_with_semaphore(cover_info) for cover_info in cover_info_list]
            await asyncio.gather(*tasks, return_exceptions=True)

    def ph_cover_process(self):
        """处理封面上传"""
        cover_info_list = mongo_utils.get_all_cover_info()
        if not cover_info_list:
            rich_logger.warning("未找到任何视频封面信息，退出操作")
            return
        asyncio.run(self.batch_upload_cover_urls(cover_info_list, gh_utils, mongo_utils, retries=3, delay=2))
