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

rich_logger = RichLogger()


class MongoConfig:
    def __init__(self):
        # MongoDB 连接地址
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
        """
        更新作者信息
        :param author_list: 作者信息列表
        :param collection: 集合名称
        :param batch_size: 批量写入的数量
        :return: None
        """
        bulk_ops = []
        mongo_col = self.mongo_db[collection]

        # 确保 author_list 不为空
        if not author_list:
            rich_logger.warning("没有获取到任何作者信息，跳过更新")
            return

        for author in author_list:
            try:
                author_id = author.get('author_id')
                author_name = author.get('author_name')
                author_avatar = author.get('author_avatar')
                author_url = author.get('author_url')

                # 确保必要字段存在
                if not author_name or not author_avatar or not author_url:
                    rich_logger.warning(f"缺少必要的作者信息：{author}")
                    continue  # 跳过当前作者，继续处理下一个

                # 添加到bulk_ops列表中
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
                        upsert=True  # 如果没有找到该作者，插入新文档
                    )
                )
                rich_logger.info(f"成功添加/更新作者信息：{author_name}")

            except Exception as e:
                rich_logger.error(f"处理{author.get('author_name')}信息失败：{e}")

        if bulk_ops:
            try:
                for i in range(0, len(bulk_ops), batch_size):
                    # 分批执行写入操作，避免一次性写入太多导致内存问题
                    batch = bulk_ops[i:i + batch_size]
                    mongo_col.bulk_write(batch)
                    rich_logger.info(f"已成功初始化 {min(i + batch_size, len(bulk_ops))} 个作者信息")

            except Exception as e:
                rich_logger.error(f"批量写入操作失败: {e}")

        else:
            rich_logger.warning("没有有效的操作，跳过写入。")

    def get_author_urls(self, collection="pornhub"):
        """
        获取所有作者名称和主页链接
        :param collection: 集合名称
        :return: author_url_list - 作者信息字典列表
        """
        author_url_list = []
        mongo_col = self.mongo_db[collection]

        try:
            # 查询所有包含"作者名称"和"作者主页"字段的文档
            cursor = mongo_col.find({"作者名称": {"$exists": True}, "作者主页": {"$exists": True}})

            for doc in cursor:
                author_name = doc.get("作者名称")
                author_url = doc.get("作者主页")
                author_id = doc.get("作者ID")

                # 检查作者名称和主页链接是否有效
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

    def update_author_info(self, author_name, author_info, collection="pornhub", batch_size=200):
        """
        更新作者信息（作者视频信息）
        :param author_name: 作者名称
        :param author_info: 作者的详细信息字典，包括视频数量、视频列表等
        :param collection: 集合名称
        :param batch_size: 批量写入的数量
        :return: None
        """
        bulk_ops = []
        mongo_col = self.mongo_db[collection]

        # 构建更新操作
        try:
            # 确保视频数量被正确更新（不累加）
            if "作者视频数量" in author_info:
                author_info["作者视频数量"] = author_info["作者视频数量"]  # 保证使用最新的值

            bulk_ops.append(
                UpdateOne(
                    {"作者名称": author_name},  # 使用作者名称作为查询条件
                    {
                        "$set": author_info  # 设置更新内容，包括主页、头像、视频信息等
                    },
                    upsert=True  # 如果没有该作者，则插入新文档
                )
            )
            rich_logger.info(f"成功更新：{author_name}视频列表")

        except Exception as e:
            rich_logger.error(f"更新{author_name}视频列表失败: {e}")

        # 执行批量写入
        if bulk_ops:
            try:
                for i in range(0, len(bulk_ops), batch_size):
                    # 分批执行写入操作，避免一次性写入太多导致内存问题
                    batch = bulk_ops[i:i + batch_size]
                    mongo_col.bulk_write(batch)
                    rich_logger.info(f"已成功批量更新{author_name}作者信息")
            except Exception as e:
                rich_logger.error(f"批量写入数据库失败: {e}")

    def update_download_status(self, video_infos, download_status, collection="pornhub"):
        """
        更新视频下载状态
        :param video_infos: 视频信息列表
        :param download_status: 下载状态
        :param collection: 集合名称
        :return: None
        """
        mongo_col = self.mongo_db[collection]
        author_name = video_infos.get("作者名称")
        video_url = video_infos.get("视频链接")
        video_title = video_infos.get("视频标题")
        try:
            mongo_col.update_one(
                {"作者视频列表.视频链接": video_url},  # 查询条件：视频链接匹配
                {
                    "$set": {
                        "作者视频列表.$[elem].下载状态": download_status  # 更新满足条件的数组元素的下载状态
                    }
                },
                array_filters=[{"elem.视频链接": video_url}]  # 使用 arrayFilters 过滤匹配到的视频链接
            )
            rich_logger.info(f"成功更新视频下载状态：[{download_status}]丨{author_name}丨{video_title}")
        except Exception as e:
            rich_logger.error(f"更新视频下载状态失败：{e}")
