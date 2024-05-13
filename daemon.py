from arxiv import ArxivAPI
import time
from datetime import timedelta
from datetime import datetime as ddt
import datetime
import logging
import asyncio
import db

logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
logger.setLevel(logging.INFO)
sh.setLevel(logging.INFO)
sh.setFormatter(logging.Formatter("%(asctime)s-%(name)s-%(levelname)s %(message)s"))
logger.addHandler(sh)
logger.propagate = False


def get_psets(pset=None):
    psets = []
    if pset is None:
        psets = list(ArxivAPI.primary_set)
    else:
        if not isinstance(pset, (tuple, list)):
            pset = [pset]
        for st in pset:
            if st not in ArxivAPI.primary_set:
                logger.error(f"Invalid primary category: {st}")
            else:
                psets.append(st)
    return psets


class PaperCrawlDaemon:
    def __init__(self, psets, db_ip, db_user, db_passwd):
        self.psets = psets
        self.dbint = db.DBInterface(db_user, db_passwd, db_ip)

    def check_psets(self):
        if isinstance(self.psets, str):
            self.psets = self.psets.split(",")
            self.psets = [st.strip() for st in self.psets]
        self.psets = get_psets(self.psets)
        if len(self.psets) == 0:
            logger.error("No valid primary categories")
            return False
        return True

    async def _request(self, pset, date: str, sleep_time=5):
        while True:
            try:
                logging.info(f"Request ({pset}, {date})")
                d_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                d_yesterday = d_date - timedelta(days=1)
                s_yesterday = d_yesterday.strftime("%Y-%m-%d")
                records = await ArxivAPI.async_get_records_by_oai(
                    from_time=s_yesterday, until_time=date, pset=pset
                )
                return records
            except Exception as e:
                logger.error(f"Request ({pset}, {date}) receives an exception: {e}, waiting for {sleep_time} seconds")
                await asyncio.sleep(sleep_time)

    async def _request_all(self, date: str):
        results = []
        for pset in self.psets:
            results.extend(await self._request(pset, date))
        return results

    async def crawl_loop(self):
        last_date = None
        awake_interval_seconds = 60 * 60 * 0.5
        while True:
            now = ddt.utcnow()
            if last_date is None or last_date.day != now.day:
                logger.info("Fetch")
                last_date = now
                results = await self._request_all(now.strftime("%Y-%m-%d"))
                self.dbint.update_records(results)

            logger.info(f"Sleep for {awake_interval_seconds / 3600} hours...")
            await asyncio.sleep(awake_interval_seconds)

    async def command(self):
        pass

    async def run(self):
        if not self.check_psets():
            return

        tasks = []
        tasks.append(self.crawl_loop())
        tasks.append(self.command())

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    import getpass
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pset")
    args = parser.parse_args()
    pset = args.pset
    db_ip = input("Database address(default 127.0.0.1): ")
    if len(db_ip) == 0:
        db_ip = "127.0.0.1"
    db_user = input("Database user: ")
    db_passwd = getpass.getpass("Database passwd: ")

    pc_daemon = PaperCrawlDaemon(pset, db_ip, db_user, db_passwd)
    asyncio.run(pc_daemon.run())
