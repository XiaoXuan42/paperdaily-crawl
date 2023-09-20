import urllib.request
import time
import feedparser
import os
import pickle
import pandas as pd
from datetime import datetime, timedelta
from easydict import EasyDict as edict
import logging


logging.basicConfig(format="%(asctime)s %(message)s")

def get_today_date():
    return datetime.utcnow().strftime("%Y-%m-%d")


def get_yesterday_date():
    yesterday = datetime.utcnow() - timedelta(1)
    return yesterday.strftime("%Y-%m-%d")


def parse_date(date):
    year = int(date[:4])
    month = int(date[5:7])
    day = int(date[8:10])
    return year, month, day


def arxiv_daily(date, wait_time=3.1):
    # Base api query url
    parsed_date = parse_date(date)

    # Search parameters
    search_query = urllib.parse.quote("cat:cs.CV")

    logging.warning(f"arxiv daily: {parsed_date}")

    i = 0
    results_per_iteration = 1000
    collections = []
    stop = False
    while not stop:
        query = "http://export.arxiv.org/api/query?"
        query += (
            f"search_query={search_query}&start={i}&max_results={results_per_iteration}"
        )
        query += f"&sortBy=submittedDate&sortOrder=descending"
        response = urllib.request.urlopen(query).read()
        feed = feedparser.parse(response)

        for entry in feed.entries:
            cur_entry = edict(entry)
            d = parse_date(cur_entry.updated)
            if d > parsed_date:
                continue
            elif d < parsed_date:
                stop = True
                continue
            else:
                collections.append(cur_entry)

        i += len(feed.entries)
        time.sleep(wait_time)
    fpath = os.path.join("arxiv", date)
    print(len(collections))
    with open(fpath, "wb") as f:
        pickle.dump(collections, f)


if __name__ == "__main__":
    arxiv_daily(get_yesterday_date())
