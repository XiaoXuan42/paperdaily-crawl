from flask import Flask, render_template, request
from arxiv import ArxivAsset
from config import CategoryFilterConfig
from datetime import datetime, timezone, timedelta
import os
import json

app = Flask(__name__)

arxiv_asset = ArxivAsset()


def _get_config(name):
    config_path = os.path.join("configs", name + ".json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            d = json.load(f)
            return CategoryFilterConfig(d)
    return None


def _validate_date(date):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def render_papers404(date):
    return render_template("papers404.html", date=date)


def _query(date, config: CategoryFilterConfig):
    if not _validate_date(date):
        return render_papers404("invalid")

    st = arxiv_asset.get_by_date(date, categories=config.categories)
    if st:
        st = config.filt(st)
        papers = st.get_records()
        return render_template("paperlist.html", date=date, papers=papers)
    else:
        return render_papers404(date)


@app.route("/<pset>/")
def query(pset):
    """
    Set arguments through url
    """
    if not ArxivAsset.is_valid_pset(pset):
        return render_papers404("invalid")

    d = request.args.to_dict()

    def check_and_split(d, attr):
        if attr in d:
            if not isinstance(d[attr], list):
                d[attr] = d[attr].split(",")

    check_and_split(d, "categories")
    if "categories" not in d:
        d["categories"] = ArxivAsset.get_all_categories(pset)
    else:
        d["categories"] = list(
            set(d["categories"]).intersection(set(ArxivAsset.get_all_categories(pset)))
        )

    check_and_split(d, "authors")
    check_and_split(d, "keywd_in_title")
    check_and_split(d, "keywd_in_abstract")

    date = d.get("date", "")
    config = CategoryFilterConfig(d)

    return _query(date, config)


def query_config(config_name, offset):
    d_today = datetime.now(timezone.utc)
    try:
        offset = int(offset)
    except ValueError:
        return render_papers404(d_today)
    date = d_today - timedelta(days=offset)
    s_date = date.strftime("%Y-%m-%d")
    config = _get_config(config_name)

    if config is None:
        return render_papers404(s_date)
    return _query(s_date, config=config)


@app.route("/config/<config_name>/yesterday")
def query_yesterday(config_name):
    return query_config(config_name, 1)


@app.route("/config/<config_name>/<offset>")
def query_config_with_offset(config_name, offset):
    return query_config(config_name, offset)


if __name__ == "__main__":
    app.run()
