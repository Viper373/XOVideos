# -*- coding:utf-8 -*-
# @Project        :XOVideos
# @FileName       :redis_utils.py
# @Time           :2025/1/16 07:41
# @Author         :Viper373
# @Index          :https://viper3.top
# @Blog           :https://blog.viper3.top
# @Software       :PyCharm

import redis
from tool_utils.log_utils import RichLogger

rich_logger = RichLogger()


class RedisConfig:

    def __init__(self):
        # 配置 Redis 连接参数
        self.redis_connect_host = 'redis-10580.crce178.ap-east-1-1.ec2.redns.redis-cloud.com'
        self.redis_connect_port = 10580
        self.redis_connect_user = 'default'
        self.redis_connect_pwd = 'ShadowZed666'


class RedisUtils:

    def __init__(self):
        # 初始化 Redis 配置并创建连接池
        redis_config = RedisConfig()
        self.video_download_urls_key = 'pornhub:download:urls'  # 用于存储视频下载链接的 Redis 键
        # 创建连接池
        redis_pool = redis.ConnectionPool(
            host=redis_config.redis_connect_host,
            port=redis_config.redis_connect_port,
            username=redis_config.redis_connect_user,
            password=redis_config.redis_connect_pwd,
            decode_responses=True  # 设置为True，返回的是str类型，而不是bytes类型
        )
        self.redis_conn = redis.StrictRedis(connection_pool=redis_pool)

    def set_video_urls(self, urls: list):
        """
        将视频下载链接推送到 Redis 列表（队列的左端）。
        :param urls: 视频下载链接列表
        """
        if urls:
            self.redis_conn.lpush(self.video_download_urls_key, *urls)  # 将所有链接推送到队列

    def pop_video_url(self):
        """
        从 Redis 列表中获取并弹出一个视频下载链接。
        :return: 返回一个视频下载链接，若队列为空则返回 None
        """
        try:
            download_url = self.redis_conn.rpop(self.video_download_urls_key)  # 弹出最右边的元素（最早推送的）
            if download_url:
                return download_url
            else:
                return None
        except redis.RedisError as e:
            rich_logger.error(f"Redis 弹出链接错误: {e}")
            return None
        except Exception as e:
            rich_logger.error(f"获取视频下载链接时发生错误: {e}")
            return None

    @rich_logger
    def get_video_urls_count(self):
        """
        获取 Redis 列表中视频下载链接的数量。
        :return: 整数，表示 Redis 列表中存储的视频下载链接数量
        """
        try:
            count = self.redis_conn.llen(self.video_download_urls_key)
            if count > 0:
                rich_logger.info(f"Redis 中有 {count} 个视频下载链接，准备处理。")
                return count
            else:
                rich_logger.warning("Redis 中没有视频下载链接。")
                return 0
        except redis.RedisError as e:
            rich_logger.error(f"获取 Redis 列表长度时出错: {e}")
            return 0
        except Exception as e:
            rich_logger.error(f"获取视频下载链接数量时出错: {e}")
            return 0


if __name__ == '__main__':
    redis_utils = RedisUtils()
    redis_utils.get_video_urls_count()
