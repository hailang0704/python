import scrapy
import os
import sys
# 引入容器
from course_spider.course_item import CourseItem


class CourseSpider(scrapy.Spider):
    #设置name
    name = "course_spider"
    #设定域名
    allowed_domains = ["imooc.com"]
    #填写爬取地址
    start_urls = ["http://www.imooc.com/course/list"]
    #编写爬取方法
    def parse(self, response):

        #实例一个容器保存爬取的信息
        item = CourseItem()
        #这部分是爬取部分，使用xpath的方式选择信息，具体方法根据网页结构而定
        #先获取每个课程的div,此div是可迭代的
        divs = response.xpath('//div[@class="moco-course-list"]//div[@class="index-card-container course-card-container container "]')
        print("#################response",type(divs),divs)
        for box in divs:
            try:
                #获取每个div中的课程路径
                item['url'] =  'http://www.imooc.com'+box.xpath('.//a[@target="_blank"]/@href').extract()[0]
                print('item', item)
                # print('box',box.xpath('.//@href').extract()[0])
                #获取div中的课程标题
                item['title'] = box.xpath('.//h3/text()').extract()[0].strip()
                #获取div中的标题图片地址
                item['image_url'] = box.xpath('.//div[@class="course-card-bk"]//img/@src').extract()[0]
                #获取div中的学生人数
                item['student'] = box.xpath('.//div[@class="course-card-info"]/text()').extract()[1].strip()[:-3]
                #获取div中的课程简介
                item['introduction'] = box.xpath('.//p/text()').extract()[0].strip()
                print('item',item)
            except:
                print('匹配信息失败，手动修改匹配样式。。。。。。。。。。。。')
            #返回信息
            yield item # 有此句pipline才会被调用
        try:
            next_page_url = response.xpath('.//a[contains(text(),"下一页")]/@href').extract()[0]
            print('next_page_url',next_page_url)
            if next_page_url:
                next_page_url = 'http://www.imooc.com'+ next_page_url
                yield scrapy.Request(next_page_url,callback=self.parse)
        except:
            print('获取下一页url时出错。。。。。。。。。。。')