from magic_spider import MagicSpider
import scrapy


class Queen:
    def __init__(self):
        self.deploy_children()

    def deploy_children(self):
        cmd = 'scrapy runspider quotes_spider.py -o quotes.jl'
        exec(cmd)
