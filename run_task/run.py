from website.pornhub import Pornhub
from website.jiuse import Jiuse
from website.allcover import AllCover
from tool_utils.log_utils import RichLogger

rich_logger = RichLogger()


class Run:
    def __init__(self):
        self.pornhub = Pornhub()
        self.jiuse = Jiuse()

    @rich_logger
    def run(self):
        self.pornhub.run_pornhub()
        self.jiuse.run_jiuse()


class CoverRun:
    def __init__(self):
        self.cover = AllCover()

    @rich_logger
    def run(self):
        self.cover.run_cover()
