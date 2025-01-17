from website.pornhub import Pornhub
from tool_utils.log_utils import RichLogger

rich_logger = RichLogger()


class Run:
    def __init__(self):
        self.pornhub = Pornhub()

    @rich_logger
    def run(self):
        self.pornhub.run_pornhub()
