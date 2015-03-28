__author__ = 'michaelmoliterno'

import urllib2
from bs4 import BeautifulSoup
import pymongo
from dateutil.parser import parse
import datetime
import logging
import sys


date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
mongo_log_dir = '/var/log/etsy/'
LOG_FILENAME = '%sget_transaction_comments/%s.out' % (mongo_log_dir,date)
logging.basicConfig(filename=LOG_FILENAME, # log to this file
                    format='%(asctime)s %(message)s') # include timestamp


opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]


c = pymongo.MongoClient("104.236.210.32")
db = c['etsy_db']

etsy_shops = db['etsy_shops']
etsy_transaction_comments = db['etsy_transaction_comments']
etsy_transaction_comments_titles = db['etsy_transaction_comments_title_search']
shops_inventory_db = db['etsy_shops_inventories_master']

shops = etsy_transaction_comments.distinct('shop')

# for shop in etsy_shops.find():
#     shops.append(shop['_id'])
#
# shops_in_collection = []
#
#
# for i, shop in enumerate(etsy_transaction_comments.distinct('shop')):
#     shops_in_collection.append(shop)
#
# shops_not_in_collection = list(set(shops) - set(shops_in_collection))


errors = []
no_reviews = []

print len(shops), 'to process. STARTING NOW!'

for shop_num, shop in enumerate(shops):

    shop_url = "https://www.etsy.com/shop/" + shop + "/reviews"
    print 'processing shop #:', shop_num
    print shop_url


    try:
        page = opener.open(shop_url)
        soup = BeautifulSoup(page)

        print 'processing: %s ' % (shop_url)

        pages = soup.find(class_='pages')


        # this gets the total number of pages of reviews for a seller
        for i, link in enumerate(pages):
            if i == len(pages) -2:
                num_review_pages = int(link.find('a').text)

        print num_review_pages

        print "%i review pages for shop %s" % (num_review_pages,shop)

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
                                title = 'no_title'


                            try:
                                stars =  int(review_info.find(class_='stars ').findChild()['value'])
                            except:
                                stars = -1


                            try:
                                review_text = review.find(class_='review').text.strip()
                            except:
                                review_text = ''

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


        else:
              review_dict = {
                    "item_title":'NONE',
                    "date": date_time,
                    "stars":-1,
                    "image_url":'NONE',
                    "review_text":'NONE',
                    "reviewer":'NONE',
                    "shop":shop
                    }


        etsy_transaction_comments.insert(review_dict)

    except:
        e = sys.exc_info()[0]
        print e
        errors.append(shop_url)
