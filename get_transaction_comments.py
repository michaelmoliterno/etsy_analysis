__author__ = 'michaelmoliterno'

import urllib2
from bs4 import BeautifulSoup
import pymongo
from dateutil.parser import parse
import datetime
import logging
import workerpool
import urllib3

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

NUM_SOCKETS = 4
NUM_WORKERS = 10

http = urllib3.PoolManager(maxsize=NUM_SOCKETS)
workers = workerpool.WorkerPool(size=NUM_WORKERS)

date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
mongo_log_dir = '/var/log/etsy/'
LOG_FILENAME = '%sget_transaction_comments/%s.out' % (mongo_log_dir,date)
logging.basicConfig(filename=LOG_FILENAME, # log to this file
                    format='%(asctime)s %(message)s') # include timestamp

# Set up the db connections
try:
    c = pymongo.MongoClient("104.236.210.32")
    db = c['etsy_db']
    etsy_shops = db['etsy_shops']
    etsy_transaction_comments = db['etsy_transaction_comments']
    etsy_transaction_comments_titles = db['etsy_transaction_comments_title_search']
    shops_inventory_db = db['etsy_shops_inventories_master']
except:
    print 'cannot connect to db'
    logging.exception('')


shops = etsy_transaction_comments.distinct('shop')
shops.sort(reverse=True)

num_shops = len(shops)

URL_LIST = ["https://www.etsy.com/shop/%s/reviews"%(shop) for shop in shops]

print num_shops, 'shops to crawl for comments. STARTING NOW!'

for shop_num, shop in enumerate(shops):

    shop_url = "https://www.etsy.com/shop/" + shop + "/reviews"
    print "processing shop #%s of %i (%s)" % (shop_num,num_shops,shop_url)

    try:

        try:
            page = opener.open(shop_url)
            soup = BeautifulSoup(page)
        except:
            continue

        print 'processing: %s ' % (shop_url)

        pages = soup.find(class_='pages')

        if pages is not None:
            # this gets the total number of pages of reviews for a seller
            for i, link in enumerate(pages):
                if i == len(pages) -2:
                    num_review_pages = int(link.find('a').text)

            print "%i review pages for shop %s" % (num_review_pages,shop)
        else:
            num_review_pages = -1
            print "no review pages for shop %s" % (shop)

        if num_review_pages > 0:

            shop_review_base_url = shop_url + "?page="

            # for each review page (a seller can have many)
            for review_page in range(num_review_pages):

                shop_review_page = shop_review_base_url + "%s" % (review_page+1)
                print shop_review_page

                page = opener.open(shop_review_page)
                soup = BeautifulSoup(page)

                reviews = soup.findAll(class_ = 'receipt-review')

                for review in reviews:

                    try:
                        reviewer = review.find(class_='reviewer-info').find('a')['href'].split('/')[2]
                    except:
                        reviewer = 'anonymous'

                    try:
                        date = review.find(class_='reviewer-info').findAll('span')[1].text[3:]
                        date_time = parse(date)
                    except:
                        date_time = None

                    review_infos = review.findAll('li')

                    for review_items, review_info in enumerate(review_infos):

                        if review_items>0:

                            try:
                                image = review_info.find(class_='image')

                                item_id = int(image['href'].split('?')[0].split('/')[2])
                                image_url = image.findChild()['src']
                            except:
                                item_id = -1
                                image_url = ''

                            try:
                                title = review_info.find(class_='transaction-title').text.strip()
                            except:
                                title = 'no_item_title'


                            try:
                                stars =  int(review_info.find(class_='stars ').findChild()['value'])
                            except:
                                stars = 0

                            try:
                                review_text = review.find(class_='review').text.strip()
                            except:
                                review_text = ''

                            if item_id > 0:

                                review_dict = {
                                                "_id":item_id,
                                                "item_title":title,
                                                "date": date_time,
                                                "stars":stars,
                                                "image_url":image_url,
                                                "review_text":review_text,
                                                "reviewer":reviewer,
                                                "shop":shop
                                                }
                                try:
                                    etsy_transaction_comments.insert(review_dict)
                                except:
                                    print 'listing %s already in etsy_transaction_comments' % (item_id)
                                    continue

        else:
            review_dict = {
                    "item_title":'NO EXISTING BUYER COMMENTS',
                    "date": date_time,
                    "stars":-1,
                    "shop":shop
                    }
            etsy_transaction_comments.insert(review_dict)

    except:
        logging.exception('')