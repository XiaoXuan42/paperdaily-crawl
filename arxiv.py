import urllib.request
import time
import feedparser
import os
from easydict import EasyDict as edict
import pickle


def get_today_date():
    return time.strftime("%Y-%m-%d", time.localtime(time.time()))

def parse_date(date):
    year = int(date[:4])
    month = int(date[5:7])
    day = int(date[8:10])
    return year, month, day

def arxiv_daily(date, wait_time=3.1):
    # Base api query url
    parsed_date = parse_date(date)
    base_url = 'http://export.arxiv.org/api/query?'

    # Search parameters
    search_query = urllib.parse.quote("cat:cs.CV")

    i = 0
    results_per_iteration = 1000
    collections = []
    stop = False
    while not stop:
        query = 'search_query=%s&start=%i&max_results=%i&sortBy=submittedDate&sortOrder=descending' % (search_query,
                                                            i,
                                                            results_per_iteration)
        response = urllib.request.urlopen(base_url+query).read()
        feed = feedparser.parse(response)

        for entry in feed.entries:
            cur_entry = edict(entry)
            d = parse_date(cur_entry.updated)
            if d < parsed_date:
                stop = True
                continue
            collections.append(cur_entry)
        time.sleep(wait_time)
    fpath = os.path.join("arxiv", date)
    with open(fpath, 'wb') as f:
        pickle.dump(collections, f)


if __name__ == "__main__":
    arxiv_daily(get_today_date())
