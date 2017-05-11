# encoding:utf-8
'''
redisstore.py核心处理代码的文件
queue_seed_check.py队列种子超时检测并维护
'''
import redis
import hashlib
import datetime
from redis import Redis
import settings
from pymongo import MongoClient
import helper
from copy import deepcopy
import urllib2
import os
import json
import requests
from urllib import quote
import logging
import cookielib
buildJob = lambda r, i, n, m: {'RequestJob': r, 'Order': i, 'Type': '%s_%s'%(n, m)}
fakeJob = lambda i, t: {"ID": "active","Data": i, "Queue": t, "Nacks": 0, "AdditionalDeliveries": 0}
buildResult = lambda data, queue:{"ID":"active","Result":"ResultData","Data":data,"Queue":queue}
class RedisStore:
    def __init__(self):
        self.redis = Redis()
        self.mongoCall = MongoClient('localhost')['icraw']['company']
        self.initialize()
        self.relatedinfo={}
    def initialize(self):
        #self.logger = self.get_logger('logs/common.log')
        print 'init'


    def getlimittime(self, minutes=10):
        pre = datetime.timedelta(minutes=minutes)
        #print pre
        now = datetime.datetime.now()
        #print now
        thetime = now - pre
        thetime = self.onlyint(thetime)
        return thetime
    #找出字符串中的数字并且拼接
    def onlyint(self, string):
        new = ''
       # print string
        for i in str(string):
            new = new + (i if i.isdigit() else '')
        return new

    def get_uid(self, url):
        try:
            url = url.encode('utf8')
        except:
            pass
        md5 = hashlib.new("md5", url).hexdigest()
        first_half_bytes = md5[:16]
        last_half_bytes = md5[16:]
        first_half_int = int(first_half_bytes, 16)
        last_half_int = int(last_half_bytes, 16)
        xor_int = first_half_int ^ last_half_int
        uid = "%x" % xor_int
        return uid

    def saveHtml(self, file_name, file_content):
        #    注意windows文件命名的禁用符，比如 /
        with open(file_name.replace('/', '_') + ".html", "wb") as f:
            #   写文件用bytes而不是str，所以要转码
            f.write(file_content)

    # 按规则拼装
    def packresult(self, request, html,queue):

        _ = {
            'data': html,
            'request': request,
            'queue':queue
        }
        return _

    # 下载html，并将结果存放在resultqueue集合队列中
    def get_html(self, pack_seed):

        #print quote(uidinfo[1].encode('utf-8'))
        url = pack_seed.get('url', None)
        request =  urllib2.Request(url)

        cookie = cookielib.CookieJar()
        openner = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))

        user_agent = pack_seed.get('proxy', None)
        request.add_header("User-Agent",user_agent)

        cookie_qcc= pack_seed.get('headers', None)
        request.add_header("Cookie",cookie_qcc)

        html = openner.open(request).read()

        packresult = self.packresult(pack_seed, html,"save_testseed1")
        build=buildResult(packresult,"result_queue")
        print "build"
        print build
        print "result_queue"
        self.redis.hset("result_queue",pack_seed.get("query",None).get("uid",None)[0],build)
        print self.redis.hlen("result_queue")
        print self.redis.hkeys ("result_queue")
        #print html
        #self.saveHtml('text1',html)

    # 从任务队列中拿到种子并解析
    def get_job(self,queue):
        while True:
            seed = {}
            # 从任务队列中获取任务
            seed = self.redis.spop(queue)
            print 'get_job seed'
            print seed
            if(seed == None):
                break
            seed = eval(seed)
            requestjob = seed.get('RequestJob',None)
            data = requestjob.get('Data', None)
            self.get_html(data)
        #print self.redis.smembers('result_testseed')


    def add_job(self, queue, data):
        self.redis.sadd(queue, data)
        #print data
        #print self.redis.scard(queue)
        #print self.redis.smembers(queue)
        self.get_job(queue)


    # 按规则拼装
    def packrequest(self,seed,type = 'qcc'):
        url = ''
        if (type == 'qcc'):
            url = 'http://www.qichacha.com/search?key={name}'
        else:
            url = "http://www.tianyancha.com/search?key={name}&checkFrom=searchBox"

        user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
        cookie_qcc = "acw_tc=AQAAABRgySDfNAwA+ClHZZpC/wlxiVgh; PHPSESSID=c9gk69p3jsqngs44ljas082gb3; UM_distinctid=15b8a41973192-08d6548e783886-414a0229-1fa400-15b8a4197325f; gr_user_id=1b0b2938-c170-4309-946c-3ffbceeaa237; _uab_collina=149267329361333337295407; _umdata=6AF5B463492A874D68440E29201A27EB153FE35B87CDC5D38AC99570BF58F96AA147D8399A8FE866CD43AD3E795C914C8C1E13EA888C33C7EA763DE0991B015C; gr_session_id_9c1eb7420511f8b2=0361498c-3a83-40ae-be5d-a059ee0e4b35; CNZZDATA1254842228=1838556974-1492669086-https%253A%252F%252Fwww.baidu.com%252F%7C1493710621"
        uid = seed.get('uid',None)
        url = url.format(**{'name': quote(uid[1].encode('utf-8'))})
        _ = {
            'ack': True,
            'url': url,
            'params': {
            },
            'query': {
                'key_queue_name': 111,
                'uid': uid,
            },
            'headers': cookie_qcc,
            'method': 'GET',
            'proxy': user_agent,
        }
        return _

    # 将种子推送到任务队列，然后将种子从当前移动到下一队列
    def pushseed(self, seeds, tmp_queue):
        _name_ = 'test_seed'
        #print(seeds)
        # 将种子存入save队列中，测试用
        for seed in seeds:
            pack_seed = self.packrequest(seed)
            x = buildJob(fakeJob(pack_seed, _name_), 0, _name_, 0)
            #print 'x'
            #print x
            #更新hashmapvalue
            self.redis.hset("common_seed_queue", seed.get("uid", None)[0], x)
            # 将任务添加到任务队列
            self.add_job('save_testseed1', deepcopy(x))
            # 将缓冲队列中的种子移入下一队列并从当前缓冲队列中删除
            #print self.redis.zrange("tmp_seed_queue_0", 0, -1)
            self.redis.zadd("tmp_seed_queue_1",seed.get("uid",None)[0],self.onlyint(datetime.datetime.now()))
            #print  seed.get("uid", None)[0]
            self.redis.zrem("tmp_seed_queue_0", seed.get("uid", None)[0])
            #print '----queue0'
            print self.redis.zrange("tmp_seed_queue_0",0,-1)
            #print '----queue1'
            print self.redis.zrange("tmp_seed_queue_1", 0, -1)
            #self.logger.info('add a save test seed.')

    def getseed(self):
        seeds = []
        datas = self.mongoCall.find()
        for doc in datas:
            #print doc.get('name')
            uid = self.get_uid(doc.get('name'))
            relatedinfo = doc.get('qccid')
            data = {'uid':[uid,doc.get('name'),relatedinfo]}
            seeds.append(data)

            # print datetime.datetime.now()
            self.redis.zadd('tmp_seed_queue_0', uid,  self.onlyint(datetime.datetime.now()))
            # 与缓冲队列配合使用，uid的vlue保存在common队列中，起到字典的作用
            self.redis.hset('common_seed_queue',uid, relatedinfo)

            self.mongoCall.update({'name': doc.get('name')}, {'$set': {'uid': uid, 'qccid':2}}, upsert=True)
            self.relatedinfo.update({uid: relatedinfo})
        self.pushseed(seeds, "tmp_seed_queue_0")
        print 'commonqueue'
        print self.redis.hgetall("common_seed_queue")
        #print self.redis.zrange('tmp_seed_queue_0', 0, 2, False, True)



if __name__ == '__main__':
    redisstore = RedisStore()
    print redisstore.getlimittime(10)
    redisstore.getseed()