from flask import Flask, render_template
from arxiv import ArxivAPI, ArxivAsset, ArxivDaily
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


@app.route("/cs/yesterday")
def yesterday():
    global arxiv_asset, config

    papers = []
    d_yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    s_yesterday = d_yesterday.strftime("%Y-%m-%d")
    st = arxiv_asset.get_by_date(s_yesterday, primary_set="cs")
    if st:
        st = config.filt(st)
        papers = st.get_records()
    return render_template("paperlist.html", date=s_yesterday, papers=papers)


if __name__ == "__main__":
    app.run()
