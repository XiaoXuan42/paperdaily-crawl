from flask import Flask, render_template, request
from arxiv import ArxivAPI, ArxivAsset, ArxivSet
from config import CategoryFilterConfig
from datetime import datetime, timezone, timedelta
from typing import Callable
import os
import json

app = Flask(__name__)

arxiv_asset = ArxivAsset()

if os.path.exists("config.json"):
    with open("config.json", "r") as f:
        d = json.load(f)
        config = CategoryFilterConfig(d)
else:
    config = CategoryFilterConfig({})


def _validate_date(date):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _query(date, f: Callable[[ArxivSet], ArxivSet], category=None, primary_set=None):
    st = arxiv_asset.get_by_date(date, category=category, primary_set=primary_set)
    papers = []
    if st:
        st = f(st)
        papers = st.get_records()
    return render_template("paperlist.html", date=date, papers=papers)


def _query_from_dict(d: dict):
    pset = d.get("primary_set", None)
    date = d.get("date", "")

    if pset is None or not _validate_date(date):
        return render_template("paperlist.html", date="", papers=[])

    def check_and_split(d, attr):
        if attr in d:
            if not isinstance(d[attr], list):
                d[attr] = d[attr].split(",")

    check_and_split(d, "categories")
    check_and_split(d, "authors")
    check_and_split(d, "keywd_in_title")
    check_and_split(d, "keywd_in_abstract")

    cur_config = CategoryFilterConfig(d)
    return _query(date, f=cur_config.filt, primary_set=pset)


@app.route("/query/<pset>")
def query(pset):
    d = request.args.to_dict()
    d["primary_set"] = pset
    return _query_from_dict(d)


@app.route("/cs/")
def cs_query():
    d = request.args.to_dict()
    d["primary_set"] = "cs"
    return _query_from_dict(d)


@app.route("/cs/yesterday")
def cs_yesterday():
    d_yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    s_yesterday = d_yesterday.strftime("%Y-%m-%d")
    return _query(s_yesterday, f=config.filt, primary_set="cs")


if __name__ == "__main__":
    app.run()
