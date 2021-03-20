import scrapy
import re

from ..loaders import AutoYoulaLoader


class AutoYoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['https://auto.youla.ru/']
    mydict = {
        "start": "//div[contains(@class,'TransportMainFilters')]//a[@class='blackLink']/@href",
        "brand": "//div[contains(@class,'Paginator_block')]//a[contains(@class,'Paginator_button')]/@href",
        "car": "//div[@id='serp']//a[@data-target='serp-snippet-title']/@href"
    }
    my_data = {
        "title": {"xpath": "//div[contains(@class,'AdvertCard_topAdvertHeader')]"
                           "//div[@data-target='advert-title']/text()"},
        "price": {"xpath": "//div[contains(@class, 'app_gridContentChildren')]//div[@data-target='advert-price']/text()"},
        "characteristics": {"xpath": "//h3[contains(text(), 'Характеристики')]"
                                     "/..//div[contains(@class, 'AdvertSpecs_row')]"},
        "description": {"xpath": "//div[@data-target='advert-info-descriptionFull']/text()"}

    }

    def get_response(self, response, xpath, callback):
        for link in response.xpath(self.mydict[xpath]):
            yield response.follow(link, callback=callback)

    def parse(self, response, *args, **kwargs):
        yield from self.get_response(response, "start", self.brand_parse)

    def brand_parse(self, response, *args, **kwargs):
        yield from self.get_response(response, "brand", self.brand_parse)
        yield from self.get_response(response, "car", self.car_parse)

    @staticmethod
    def get_author(response):
        marker = 'window.transitState = decodeURIComponent'
        for script in response.css("script"):
            try:
                if marker in script.css("::text").extract_first():
                    re_pattern = re.compile(r"youlaId%22%2C%22([a-zA-Z|\d]+)%22%2C%22avatar")
                    result = re.findall(re_pattern, script.css("::text").extract_first())
                    return response.urljoin(f"/user/{result[0]}").replace("auto.", "") if result else None
            except TypeError:
                return None

    def car_parse(self, response, *args, **kwargs):
        loader = AutoYoulaLoader(response=response)
        loader.add_value("url", response.url)
        loader.add_value("author", self.get_author(response))
        for key, xpath in self.my_data.items():
            loader.add_xpath(key, **xpath)
        yield loader.load_item()
