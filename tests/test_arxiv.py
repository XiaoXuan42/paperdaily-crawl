from app.asset import ArxivAsset
from datetime import datetime, timedelta


def sample_arxiv():
    arxiv = ArxivAsset()
    yesterday = datetime.strftime((datetime.now(datetime.UTC) - timedelta(days=1)), "%Y-%m-%d")
    print(f"{yesterday}: {len(arxiv.get_by_date('cs.AI', yesterday))}")
