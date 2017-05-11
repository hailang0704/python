# -*- encoding:utf-8 -*-
import redis
import copy
from multiprocessing import Process
import sys, os
import time
from copy import deepcopy
from redis import Redis
from pymongo import MongoClient
import datetime
from redisstore import RedisStore
queues = ['tmp_seed_queue_%d' % i for i in range(11)]
class QueueCheck:

    def __init__(self):
        self.redis = Redis()
        self.redisStore =  RedisStore()
        self.mongoCall = MongoClient('localhost')['icraw']['company']
    def maincheck(self):
        while True:
            for i in range(11):
                queue = ["tmp_seed_queue_%d" %i]
                print 'queue'
                print queue
                premin = self.redisStore.getlimittime(20)
                print premin
                seeds = self.redis.zrangebyscore("queue",0,premin)
                for seed in seeds:
                    print "xxxxxxxxxxx"
                    x = self.redis.hget(queue,seed.get("uid", None)[0])
                    self.add_job('save_testseed1', deepcopy(x))
                    # 将缓冲队列中的种子移入下一队列并从当前缓冲队列中删除
                    # print self.redis.zrange("tmp_seed_queue_0", 0, -1)
                    self.redis.zadd("tmp_seed_queue_%d" %(i+1), seed.get("uid", None)[0], self.onlyint(datetime.datetime.now()))
                    # print  seed.get("uid", None)[0]
                    self.redis.zrem(queue, seed.get("uid", None)[0])

if __name__ == '__main__':
    check = QueueCheck()
    print check.redisStore.getlimittime(30)
    check.maincheck()