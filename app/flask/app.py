from flask import Flask, render_template
from arxiv import ArxivAPI
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

@app.route("/paper/today")
def today():
    d_today = datetime.now(timezone.utc)
    d_yesterday = d_today - timedelta(days=1)
    s_today = d_today.strftime("%Y-%m-%d")
    s_yesterday = d_yesterday.strftime("%Y-%m-%d")

    papers = ArxivAPI.get_records_by_oai(from_time=s_yesterday, until_time=s_today, set="econ")
    print(s_today, s_yesterday, len(papers))

    return render_template("paperlist.html", today=s_today, papers=papers)
    

if __name__ == "__main__":
    app.run()
