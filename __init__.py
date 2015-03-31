from flask import Flask, request, render_template, jsonify
import pymongo

import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!
import matplotlib.pyplot as plt


import plotly.plotly as py
from plotly.graph_objs import *
import numpy as np

from operator import itemgetter

app = Flask(__name__)
@app.route("/dash")
def main():

    query = "Weekender"
    
    c = pymongo.MongoClient("104.236.210.32")
    db = c['etsy_db']
    
    comment_query_clusters_coll = db['comment_query_clusters']
    
    comments = comment_query_clusters_coll.find_one({'query':'weekender'})
    
    bag_comments = db['transaction_bags']
    bag_transactions = db['transaction_listing_bags']
    bag_inventory = db['current_bag_market']

    bag_comments_count = bag_comments.count()
    bag_transactions_count = bag_transactions.count()
    bag_inventory_count = bag_inventory.count()
    
    plot_num = 245

    weekender_sales = db['temp_weekender_sales']
    temp_weekender_top_stores_by_sales = db['temp_weekender_top_stores_by_sales']
    temp_weekender_top_listings_by_sales = db['temp_weekender_top_listings_by_sales']

    #top_stores = list(temp_weekender_top_stores_by_sales.find().limit(10))
    
    stores = list(temp_weekender_top_stores_by_sales.find())
    top_stores = sorted(stores, key=itemgetter('sales_count'), reverse=True)

    items = list(temp_weekender_top_listings_by_sales.find())
    top_items  = sorted(items, key=itemgetter('sales_count'), reverse=True)
    
    return render_template("test_bootstrap.html",
                           bag_inventory_count=bag_inventory_count,
                           bag_transactions_count=bag_transactions_count,
                           bag_comments_count=bag_comments_count,
                           int1=1,
                           int2=4,
                           int3=3,
                           plot_num=plot_num,
                           comments=comments,
                           query = query,
                           top_stores = top_stores[:10],
                           top_items=top_items[:10])

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=8888)
    #app.run()

