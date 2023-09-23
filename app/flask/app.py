from flask import Flask, render_template, request
from arxiv import ArxivAsset
from config import CategoryFilterConfig
from datetime import datetime, timezone, timedelta
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


def render_papers404(date, config: CategoryFilterConfig):
    return render_template(
        "papers404.html",
        date=date,
        categories=config.get_str_attr("categories"),
        authors=config.get_str_attr("authors"),
        keywd_in_title=config.get_str_attr("keywd_in_title"),
        keywd_in_abstract=config.get_str_attr("keywd_in_abstract")
    )

def _query(date, config: CategoryFilterConfig, category=None, primary_set=None):
    st = arxiv_asset.get_by_date(date, category=category, primary_set=primary_set)
    papers = []
    if st:
        st = config.filt(st)
        papers = st.get_records()
        return render_template("paperlist.html", date=date, papers=papers)
    else:
        return render_papers404(date=date, config=config)


def _query_from_dict(d: dict):
    pset = d.get("primary_set", None)
    date = d.get("date", "")

    def check_and_split(d, attr):
        if attr in d:
            if not isinstance(d[attr], list):
                d[attr] = d[attr].split(",")

    check_and_split(d, "categories")
    check_and_split(d, "authors")
    check_and_split(d, "keywd_in_title")
    check_and_split(d, "keywd_in_abstract")

    cur_config = CategoryFilterConfig(d)
    if pset is None or not _validate_date(date):
        return render_papers404(date, cur_config)

    return _query(date, config=cur_config, primary_set=pset)


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
    global config
    d_yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    s_yesterday = d_yesterday.strftime("%Y-%m-%d")
    return _query(s_yesterday, config=config, primary_set="cs")


if __name__ == "__main__":
    app.run()
