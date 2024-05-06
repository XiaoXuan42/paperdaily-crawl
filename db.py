from arxiv import ArxivAPI, ArxivRecord
from typing import List
import logging
from sqlalchemy import create_engine, text


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(logging.Formatter("%(asctime)s-%(name)s-%(levelname)s %(message)s"))
logger.addHandler(sh)


class DBInterface:
    def __init__(self, user, passwd, ip='127.0.0.1', port=3306):
        self.engine = create_engine(f"mysql+pymysql://{user}:{passwd}@{ip}/papers?charset=utf8mb4")

    def record_to_dict(self, record: ArxivRecord):
        return {
            'id': record.id,
            'title': record.title,
            'abstract': record.abstract,
            'categories': ";;".join(record.categories),
            'authors': ';;'.join(record.authors),
            'published': record.published if record.published else None,
            'updated': record.updated if record.updated else None
        }

    def update_records(self, records: List[ArxivRecord]):
        if len(records) == 0:
            return
        rc_dicts = [self.record_to_dict(record) for record in records]

        insert_sql = f"REPLACE INTO paper_crawl VALUES (:id, :title, :abstract, :categories, :authors, :published, :updated);"
        with self.engine.begin() as conn:
            conn.execute(text(insert_sql), rc_dicts)
        logger.info(f"DB: upate {len(records)} record(s)")
