#!/usr/bin/python


__author__ = 'michaelmoliterno'

import json
import time
import pymongo
import datetime
import requests
import logging
import traceback

api_key = 'dlyt2hbnt15lynvvr5lvtv9q'


c = pymongo.MongoClient("104.236.210.32")
db = c['etsy_db']



date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
mongo_log_dir = '/var/log/etsy/'
LOG_FILENAME = '%sget_shop_inventory/%s.out' % (mongo_log_dir,date)
logging.basicConfig(filename=LOG_FILENAME, # log to this file
                    format='%(asctime)s %(message)s') # include timestamp





def get_shop_inventories():


    shops_inventory_db = db['etsy_shops_inventories_master']
    shops_inventories_titles = db['etsy_shops_inventories_master_title_search']

    #shops = shops_inventory_db.distinct('shop_name_text')

    transaction_bags = db['transaction_bags']
    shops = list(transaction_bags.find({},{'shop':1}).distinct('shop'))

    # for shop in section_shops_db.find():
    #     shops.append(shop['_id'])

    for i, shop in enumerate(shops):

        print 'attempting to get inventory from %s.' % (shop)


        try:

            time.sleep(.1)

            if (i+1)%50 == 0:
                print 'total shops processed: ', i+1

            api_url = 'https://openapi.etsy.com/v2/shops/%s/listings/active?api_key=%s&limit=9999' % (shop, api_key)

            response = requests.get(api_url)

            print 'attempting API %i in this job' % (i)
            api_response = response.text


            data = json.loads(api_response)
            date_added = str(datetime.datetime.now())

            for x in data["results"]:
                # x['_id'] = x['listing_id']
                x['shop_name_text'] = shop
                x['inserted_date'] = date_added
                shops_inventory_db.insert(x)

        except:
            logging.error(traceback.format_exc())



get_shop_inventories()


#db_collections = sorted(db.collection_names(),reverse=False)

#for collection in db_collections:
    #if collection.endswith('shops'):

    #shops_collection = db["etsy_shops"]

    #db.etsy_shops_inventories_master.distinct('shop_name_text')


    # shops = []
    #
    # for shop in section_shops_db.find():
    #     shops.append(shop['_id'])



    # else:
    #     pass
