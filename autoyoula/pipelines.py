# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo


class AutoyoulaPipeline:
    def process_item(self, item, spider):
        db_client = pymongo.MongoClient("mongodb://localhost:27017")
        db_client["auto2"][spider.name].insert_one(item)
