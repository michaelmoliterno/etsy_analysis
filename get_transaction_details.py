__author__ = 'michaelmoliterno'

import urllib2
from bs4 import BeautifulSoup
import pymongo
from dateutil.parser import parse
import datetime
import logging
import sys
import traceback
import workerpool
import urllib3


NUM_SOCKETS = 4
NUM_WORKERS = 10

http = urllib3.PoolManager(maxsize=NUM_SOCKETS)
workers = workerpool.WorkerPool(size=NUM_WORKERS)

date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
mongo_log_dir = '/var/log/etsy/'
LOG_FILENAME = '%sget_transaction_details/%s.out' % (mongo_log_dir,date)
logging.basicConfig(filename=LOG_FILENAME, # log to this file
                    format='%(asctime)s %(message)s') # include timestamp

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

c = pymongo.MongoClient("104.236.210.32")
db = c['etsy_db']
transaction_listing_bags = db['transaction_listing_bags']
transaction_bags = db['transaction_bags']

top_shops = list(transaction_bags.find({},{'shop':1}).distinct('shop'))
URL_LIST = ['https://www.etsy.com/shop/%s/sold' % (shop) for shop in top_shops]

num_shops = len(top_shops)
print num_shops, "shops to process for transaction details"

#for shop_num, shop in enumerate(top_shops):

class GetTransDetailsJob(workerpool.Job):

    def __init__(self, url):
        self.url = url

    def run(self):

        shop_url = self.url

        logging.info('processing %s ' % (shop_url))

        try:

            try:
                page = opener.open(shop_url)
                soup = BeautifulSoup(page)
            except:
                logging.exception('')
                print 'could not open', shop_url

            pages = soup.find(class_ = 'pages')
            num_sold_pages = 0

            if pages is not None:
                for i, link in enumerate(pages):
                    if i == len(pages) -2:
                        num_sold_pages = int(link.find('a').text)
            else:
                num_sold_pages = -1

            if num_sold_pages > 0:

                print "%i pages of sold items to process for %s" % (num_sold_pages,shop_url)

                for sold_page in range(1,num_sold_pages+1):

                    if sold_page % 10 == 0:
                        print 'processing page %i of %i' % (sold_page,num_sold_pages)

                    shop_url_page = "%s?page=%i" % (shop_url,sold_page)

                    page = opener.open(shop_url_page)
                    soup = BeautifulSoup(page)

                    items = soup.findAll(class_ = 'listing-card')

                    if items is not None:

                        for listing in items:

                            try:
                                title = listing.find(class_ = 'listing-thumb')['title']
                            except:
                                title = '__NO__TITLE__'

                            if ("bag" in title) or ("backpack" in title):

                                trans = listing.find(class_ = 'listing-thumb')['href']
                                trans_id = trans.split("?")[0].split("/")[2]

                                src = listing.find('img')['src']
                                listing_num = listing.find(class_ = 'collect-container')['data-listing-id']

                                trans_listing_dict = {
                                    "_id":trans_id,
                                    "item_title":title,
                                    "src":src,
                                    "listing_id":listing_num,
                                    "shop":shop
                                    }

                                try:
                                    transaction_listing_bags.insert(trans_listing_dict)
                                except:
                                    print 'listing %s already in DB' % (trans_id)
                                    continue


        except:
            logging.exception('')

for url_count, url in enumerate(URL_LIST):
    workers.put(GetTransDetailsJob(url))
    print "worker processing job %s of %s"%(url_count,num_shops)

# Send shutdown jobs to all threads, and wait until all the jobs have been completed
# (If you don't do this, the script might hang due to a rogue undead thread.)
workers.shutdown()
workers.wait()