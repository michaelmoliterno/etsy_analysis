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
import time


NUM_SOCKETS = 3
NUM_WORKERS = 6
http = urllib3.PoolManager(maxsize=NUM_SOCKETS)
workers = workerpool.WorkerPool(size=NUM_WORKERS)
http.headers['User-agent'] = 'Mozilla/5.0'
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]


date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
mongo_log_dir = '/var/log/etsy/'
LOG_FILENAME = '%sget_transaction_details/%s.out' % (mongo_log_dir,date)
logging.basicConfig(filename=LOG_FILENAME, # log to this file
                    format='%(asctime)s %(message)s', # include timestamp
                    level=logging.DEBUG)

class GetTransDetailsJob(workerpool.Job):

    idCounter = 0

    def __init__(self, url):
        self.url = url

        GetTransDetailsJob.idCounter += 1
        self.process_count = GetTransDetailsJob.idCounter

    def run(self):

        logging.info("processing store %s of %s"%(self.process_count,num_shops))

        shop_url = self.url

        logging.info('processing %s ' % (shop_url))

        try:

            try:
                #page = opener.open(shop_url)
                page = http.request('GET',shop_url)
                soup = BeautifulSoup(page)
                pages = soup.find(class_ = 'pages')
            except:
                logging.info('could not open %s' % shop_url)
                logging.exception('')
                return None

            num_sold_pages = 0

            if pages is not None:
                for i, link in enumerate(pages):
                    if i == len(pages) -2:
                        num_sold_pages = int(link.find('a').text)
            else:
                num_sold_pages = -1

            if num_sold_pages > 0:

                logging.info("%i pages of sold items to process for %s" % (num_sold_pages,shop_url))

                for sold_page in range(1,num_sold_pages+1):

                    try:
                        shop_url_page = "%s?page=%i" % (shop_url,sold_page)
                        #page = opener.open(shop_url_page)
                        page = http.request('GET',shop_url_page)
                        soup = BeautifulSoup(page)
                        items = soup.findAll(class_ = 'listing-card')
                    except:
                        logging.error('error opening sold page %s for shop: %s'%(sold_page,shop_url))
                        continue

                    if items is not None:
                        logging.info("%s has %i items to process on %s"%(shop_url,len(items),shop_url_page))

                        for listing in items:

                            try:
                                title = listing.find(class_ = 'listing-thumb')['title']
                            except:
                                title = '__NO__TITLE__'

                            if ("bag" in title) or ("backpack" in title):

                                try:
                                    trans = listing.find(class_ = 'listing-thumb')['href']
                                    trans_id = trans.split("?")[0].split("/")[2]
                                    src = listing.find('img')['src']
                                    listing_num = listing.find(class_ = 'collect-container')['data-listing-id']
                                except:
                                    logging.exception('')
                                    continue

                                trans_listing_dict = {
                                    "_id":trans_id,
                                    "item_title":title,
                                    "src":src,
                                    "listing_id":listing_num,
                                    "shop":shop
                                    }

                                try:
                                    transaction_listing_bags.insert(trans_listing_dict)
                                    logging.info("inserted record %s"%(trans_id))
                                except:
                                    logging.info('listing %s already in DB' % (trans_id))
                                    continue

        except:
            logging.exception('')
            return None



# Set up the db connections
try:
    c = pymongo.MongoClient("104.236.210.32")
    db = c['etsy_db']
    transaction_listing_bags = db['transaction_listing_bags']
    transaction_bags = db['transaction_bags']
    etsy_transaction_comments = db['etsy_transaction_comments']

    transaction_bags_list = transaction_bags.distinct('shop')
    transaction_listing_bags_list = transaction_listing_bags.distinct('shop')
    etsy_transaction_comments_shop_list = etsy_transaction_comments.distinct('shop')

except:
    print 'cannot connect to db'
    logging.exception('')
    raise

top_shops = etsy_transaction_comments_shop_list
URL_LIST = ['https://www.etsy.com/shop/%s/sold' % (shop) for shop in top_shops]

num_shops = len(top_shops)
logging.info(num_shops, "shops to process for transaction details")

for url_count, url in enumerate(URL_LIST):
    workers.put(GetTransDetailsJob(url))
    logging.info(url_count, "shops to be processed by the workers")

# Send shutdown jobs to all threads, and wait until all the jobs have been completed
# (If you don't do this, the script might hang due to a rogue undead thread.)
workers.shutdown()
workers.wait()