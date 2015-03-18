#!/usr/bin/python

import urllib2
from bs4 import BeautifulSoup
import datetime
import pymongo
import traceback
import logging

def get_shops_by_category_search(section,query,shop_collection):

    search_text = "https://www.etsy.com/search/%s?q=%s" % (section,query)
    logging.info(search_text)

    try:

        shop_names = []

        page = opener.open(search_text)
        soup = BeautifulSoup(page)

        pagers = soup.find('ol')

        for i, link in enumerate(pagers):
            if i == len(pagers) -2:
                num_pages = int(link.find('a').text)

        logging.info("%i pages to scan for bags for %s query %s" %  (num_pages,section,query))

        for i in range(num_pages):
            search_page_text = search_text + '&page=%i' % (i+1)

            page = opener.open(search_page_text)

            soup = BeautifulSoup(page)

            productLinks = [div.a for div in soup.findAll('div', attrs={'class' : 'listing-maker'})]

            for link in productLinks:
                shop_name = link['href'].split('?')[0].split('/')[2]
                shop_names.append(shop_name)


        shop_names = list(set(shop_names))
        date_added = str(datetime.datetime.now())

        print shop_names
        for shop in shop_names:

            shop_dict = {
                        '_id' : shop,
                        'date_added' : date_added
                        }

            try:
                shop_collection.insert(shop_dict)
            except:
                logging.warning('%s is already in the collection' % (shop))

    except:
        logging.error(traceback.format_exc())


def get_section_types(section):
    try:
        url_text = "https://www.etsy.com/search/%s" % (section)

        page = opener.open(url_text)
        soup = BeautifulSoup(page)

        types = {}

        for href in soup.find(class_='second-level').find_all('a'):
            bag_type_text = href.text.strip()
            bag_type = ''.join(e for e in bag_type_text if e.isalnum())
            types[bag_type] = '/'+href['href'].split('/')[5]

        types['entire_section'] = ''

        return types

    except:
        logging.error(traceback.format_exc())
        return None


def main():

    # just for bags and purses right now...
    for section in sections:

        section_types = get_section_types(section)
        logging.info('section types:')
        logging.info(section_types)


        for section_type in section_types.values():
            section_subsection = section + section_type


            #if we are searching the whole section
            # if section_subsection == section:
            shop_collection = db['etsy_shops']
            # else:
            #     shop_collection = db[section_subsection.replace('/','_') + "_etsy_shops"]


            # if section_type in ['backpacks','totes','luggage-and-travel','market','messenger-bags','']:
            query = ['weekender','duffel','tote','sack','bucket','travel','carry+on','bag']
            # else:
            #     query = ['bag']

            # for bag_type in bags:
            for query in query:
                print section_subsection + "  " + query
                get_shops_by_category_search(section_subsection,query,shop_collection)





date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
mongo_log_dir = '/var/log/etsy/'
LOG_FILENAME = '%sget_shops_by_category_search/%s.out' % (mongo_log_dir,date)
logging.basicConfig(filename=LOG_FILENAME, # log to this file
                    format='%(asctime)s %(message)s') # include timestamp


client = pymongo.MongoClient(host = "104.236.210.32")
db = client['etsy_db']


opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

sections = ['bags-and-purses']

main()