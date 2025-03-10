# -*- coding:utf-8 -*-
# @Project        :XOVideos
# @FileName       :mongo_utils.py
# @Time           :2025/1/15 20:18
# @Author         :Viper373
# @Index          :https://viper3.top
# @Blog           :https://blog.viper3.top
# @Software       :PyCharm

import os
from pymongo.mongo_client import MongoClient
from pymongo import UpdateOne
from pymongo.server_api import ServerApi
from tool_utils.log_utils import RichLogger
from dotenv import load_dotenv

rich_logger = RichLogger()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(root_dir, '.env'))


class MongoConfig:
    def __init__(self):
        self.mongo_connect_host = os.getenv('MONGODB_URI')


class MongoUtils:
    def __init__(self):
        mongo_config = MongoConfig()
        host = mongo_config.mongo_connect_host
        self.mongo_client = MongoClient(
            host=host,
            server_api=ServerApi('1')
        )
        self.mongo_db_name = 'XOVideos'
        self.mongo_db = self.mongo_client[self.mongo_db_name]

    def init_author_info(self, author_list: list, collection="pornhub", batch_size=200):
        bulk_ops = []
        mongo_col = self.mongo_db[collection]
        if not author_list:
            rich_logger.warning("没有获取到任何作者信息，跳过更新")
            return
        for author in author_list:
            try:
                author_id = author.get('author_id')
                author_name = author.get('author_name')
                author_avatar = author.get('author_avatar')
                author_url = author.get('author_url')
                if not author_name or not author_avatar or not author_url:
                    rich_logger.warning(f"缺少必要的作者信息：{author}")
                    continue
                bulk_ops.append(
                    UpdateOne(
                        {"作者名称": author_name},
                        {
                            "$set": {
                                "作者ID": author_id,
                                "作者主页": author_url,
                                "作者头像": author_avatar,
                            },
                        },
                        upsert=True
                    )
                )
                rich_logger.info(f"成功添加/更新作者信息：{author_name}")
            except Exception as e:
                rich_logger.error(f"处理{author.get('author_name')}信息失败：{e}")
        if bulk_ops:
            try:
                for i in range(0, len(bulk_ops), batch_size):
                    batch = bulk_ops[i:i + batch_size]
                    mongo_col.bulk_write(batch)
                    rich_logger.info(f"已成功初始化 {min(i + batch_size, len(bulk_ops))} 个作者信息")
            except Exception as e:
                rich_logger.error(f"批量写入操作失败: {e}")
        else:
            rich_logger.warning("没有有效的操作，跳过写入。")

    def get_author_urls(self, collection="pornhub"):
        author_url_list = []
        mongo_col = self.mongo_db[collection]
        try:
            cursor = mongo_col.find({"作者名称": {"$exists": True}, "作者主页": {"$exists": True}})
            for doc in cursor:
                author_name = doc.get("作者名称")
                author_url = doc.get("作者主页")
                author_id = doc.get("作者ID")
                if author_name and author_url:
                    author_url_list.append({
                        "作者名称": author_name,
                        "作者主页": author_url,
                        "作者ID": author_id,
                    })
                else:
                    rich_logger.warning(f"作者信息不完整，跳过: {doc}")
            if not author_url_list:
                rich_logger.warning("没有找到任何有效的作者信息。")
        except Exception as e:
            rich_logger.error(f"获取作者信息时发生错误: {e}")
        return author_url_list

    # 在 mongo_utils.py 中
    def update_author_info(self, author_name, new_video_list, video_counts, collection="pornhub"):
        mongo_col = self.mongo_db[collection]
        try:
            mongo_col.update_one(
                {"作者名称": author_name},
                {
                    "$set": {"作者视频数量": video_counts},
                    "$push": {"作者视频列表": {"$each": new_video_list}}
                },
                upsert=True
            )
            rich_logger.info(f"成功更新：{author_name}视频列表，新增 {len(new_video_list)} 个视频")
        except Exception as e:
            rich_logger.error(f"更新{author_name}视频列表失败: {e}")

    def update_download_status(self, video_infos, download_status, collection="pornhub"):
        mongo_col = self.mongo_db[collection]
        author_name = video_infos.get("作者名称")
        video_url = video_infos.get("视频链接")
        video_title = video_infos.get("视频标题")
        try:
            mongo_col.update_one(
                {"作者视频列表.视频链接": video_url},
                {"$set": {"作者视频列表.$[elem].下载状态": download_status}},
                array_filters=[{"elem.视频链接": video_url}]
            )
            rich_logger.info(f"成功更新视频下载状态：[{download_status}]丨{author_name}丨{video_title}")
        except Exception as e:
            rich_logger.error(f"更新视频下载状态失败：{e}")

    def get_all_cover_info(self, collection="pornhub"):
        cover_info_list = []
        try:
            cursor = self.mongo_db[collection].find(
                {"作者视频列表.封面状态": {"$in": [0, 2]}},
                {"作者名称": 1, "作者视频列表": 1}
            )
            for doc in cursor:
                author_name = doc.get("作者名称")
                video_list = doc.get("作者视频列表", [])
                for video in video_list:
                    if video.get("封面状态") in [0, 2]:
                        video_title = video.get("视频标题")
                        cover_url = video.get("视频封面")
                        video_url = video.get("视频链接")
                        if author_name and video_title and cover_url and video_url:
                            cover_info_list.append({
                                "作者名称": author_name,
                                "视频标题": video_title,
                                "视频封面": cover_url,
                                "视频链接": video_url
                            })
            rich_logger.info(f"成功获取 {len(cover_info_list)} 个待处理视频封面信息")
        except Exception as e:
            rich_logger.error(f"获取视频封面信息失败: {e}")
        return cover_info_list

    def update_cover_status(self, author_name, video_url, new_status, collection="pornhub"):
        mongo_col = self.mongo_db[collection]
        try:
            video_doc = mongo_col.find_one(
                {"作者名称": author_name, "作者视频列表.视频链接": video_url},
                {"作者视频列表.$": 1}
            )
            video_title = "未知视频"
            if video_doc and "作者视频列表" in video_doc and len(video_doc["作者视频列表"]) > 0:
                video_title = video_doc["作者视频列表"][0].get("视频标题", "未知视频")
            result = mongo_col.update_one(
                {"作者名称": author_name, "作者视频列表.视频链接": video_url},
                {"$set": {"作者视频列表.$[elem].封面状态": new_status}},
                array_filters=[{"elem.视频链接": video_url}]
            )
            if result.modified_count > 0:
                rich_logger.info(f"成功更新封面状态为[{new_status}]丨{author_name} - {video_title}")
            else:
                rich_logger.warning(f"未找到匹配的视频，更新失败丨{author_name} - {video_title}")
        except Exception as e:
            rich_logger.error(f"更新封面状态失败：{e}")
