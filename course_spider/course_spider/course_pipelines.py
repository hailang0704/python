#引入文件
from scrapy.exceptions import DropItem
import json

class CoursePipeline(object):
    def __init__(self):
        #打开文件
        # print('---------------------files')
        self.file = open('./data.json', 'a', encoding='utf-8')
    #该方法用于处理数据
    def process_item(self, item, spider):
        print('pipline was be called!！！！！！！！！！！！！')
        #读取item中的数据
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        #写入文件
        self.file.write(line)
        #返回item
        return item
    #该方法在spider被开启时被调用。
    def open_spider(self, spider):
        pass
    #该方法在spider被关闭时被调用。
    def close_spider(self, spider):
        self.file.close()