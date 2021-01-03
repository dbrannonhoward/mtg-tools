from scrapy.crawler import CrawlerProcess
import scrapy


class MagicSpider(scrapy.Spider):
    name = 'magicspider'
    start_urls = [
        'https://quotes.toscrape.com/'
    ]

    def parse(self, response):
        for quote in response.css('div.quote'):
            yield {
                'author': quote.xpath('span[has-class("author")]/text()').get(),
                'text': quote.xpath('span[has-class("text")]/text()').get()
            }

        next_page = response.css('li.next a::attr("href")').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)


process = CrawlerProcess(settings={
    "FEEDS": {
        "items.json": {"format": "json"},
    },
})


if __name__ == '__main__':
    process.crawl(MagicSpider)
    process.start()  # holds here until crawling is finished
else:
    print('importing ' + __name__)
