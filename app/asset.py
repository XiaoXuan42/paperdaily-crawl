import os
from arxiv import ArxivRecord, ArxivAPI
from typing import List
from app.utils import NLP
from datetime import datetime, timedelta
import zipfile
import pickle

_default_asset_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "arxiv")


class ArxivSet:
    def __init__(self, records: List[ArxivRecord]) -> None:
        self.records = records
        self.id2records = {r.id: r for r in self.records}

    def add(self, record: ArxivRecord):
        if record.id in self.id2records:
            old_record = self.id2records[record.id]
            self.records.remove(old_record)
        self.id2records[record.id] = record
        self.records.append(record)

    def get_records(self):
        return [record for record in self.records]

    def union(self, other: "ArxivSet"):
        res = self.get_records()
        for r in other.records:
            if r.id not in self.id2records:
                res.append(r)
        return ArxivSet(res)

    def intersect(self, other: "ArxivSet"):
        res = []
        for id, r in self.id2records.items():
            if id in other.id2records:
                res.append(r)
        return ArxivSet(res)

    def __len__(self):
        return len(self.records)



class ArxivDaily(ArxivSet):
    def __init__(self, date, pset, records: List[ArxivRecord]) -> None:
        super().__init__(records)
        self.date = date
        self.pset = pset


class ArxivFilter:
    def __init__(
        self,
        categories=None,
        keypoints_in_abstract=None,
        keypoints_in_title=None,
        authors=None,
    ) -> None:
        self.categories = self._none_or_set(categories)
        self.keywd_in_abstract = self._none_or_set(keypoints_in_abstract)
        self.keywd_in_title = self._none_or_set(keypoints_in_title)
        self.authors = self._none_or_set(authors)

    def _none_or_set(self, val):
        if val is None:
            return None
        else:
            if not isinstance(val, (list, tuple)):
                val = [val]
        return set([v.lower() for v in val])

    def _filt_by_category(self, record: ArxivRecord):
        if self.categories is None:
            return True
        else:
            lower_record_categories = set([c.lower() for c in record.categories])
            st = self.categories.intersection(lower_record_categories)
            return len(st) > 0

    def _filt_by_authors(self, record: ArxivRecord):
        if self.authors is None:
            return True
        else:
            lower_record_authors = set([a.lower() for a in record.authors])
            st = self.authors.intersection(lower_record_authors)
            return len(st) > 0

    def _filt_by_keyword(self, keywords, s: str):
        if keywords is None:
            return True
        else:
            for kwd in keywords:
                if NLP.contain_phrase(s, kwd):
                    return True
            return False

    def _filt_by_keypoint_in_title(self, record: ArxivRecord):
        return self._filt_by_keyword(self.keywd_in_title, record.title)

    def _filt_by_keypoint_in_abstract(self, record: ArxivRecord):
        return self._filt_by_keyword(self.keywd_in_abstract, record.abstract)

    def _filt(self, records: List[ArxivRecord]):
        res = []
        for record in records:
            if (
                self._filt_by_category(record)
                and self._filt_by_authors(record)
                and self._filt_by_keypoint_in_abstract(record)
                and self._filt_by_keypoint_in_title(record)
            ):
                res.append(record)
        return res

    def __call__(self, data: ArxivSet):
        return ArxivSet(self._filt(data.get_records()))


class ArxivAsset:
    def __init__(self, root=_default_asset_root):
        self.root = root
        if not os.path.exists(self.root):
            os.mkdir(self.root)
        self._cached_daily = {}

    @classmethod
    def is_valid_pset(cls, pset):
        return pset in list(ArxivAPI.categories_set.keys())

    @classmethod
    def get_all_categories(cls, pset):
        if pset in ArxivAPI.categories_set:
            return list(ArxivAPI.categories_set[pset])
        else:
            return []

    @classmethod
    def find_pset(cls, category):
        for pset, cts in ArxivAPI.categories_set.items():
            if category in cts:
                return pset
        return None

    def _get_cache_path(self, pset, date):
        return os.path.join(self.root, pset, date)

    def cache(self, data: ArxivDaily, pset, date: str):
        path = self._get_cache_path(pset, date) + ".zip"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        d_bytes = pickle.dumps(data)
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr(date, d_bytes)

    def request_and_cache(self, pset, date: str):
        try:
            d_date = datetime.strptime(date, "%Y-%m-%d")
            d_yesterday = d_date - timedelta(days=1)
            s_yesterday = d_yesterday.strftime("%Y-%m-%d")
            records = ArxivAPI.get_records_by_oai(
                from_time=s_yesterday, until_time=date, set=pset
            )
            arxiv_daily = ArxivDaily(date, pset, records)
            self.cache(arxiv_daily, pset, date)
            return arxiv_daily

        except FileNotFoundError:
            return None

    def load_cache(self, pset, date: str):
        if pset in self._cached_daily:
            if date in self._cached_daily[pset]:
                return self._cached_daily[pset][date]

        path = self._get_cache_path(pset, date)
        zippath = path + ".zip"
        try:
            if os.path.exists(zippath):
                with zipfile.ZipFile(zippath, "r") as zf:
                    d_bytes = zf.read(date)
                    res = pickle.loads(d_bytes)
            else:
                with open(path, "rb") as f:
                    res = pickle.load(f)
            self._cached_daily.setdefault(pset, {})
            self._cached_daily[pset][date] = res

            return res
        except FileNotFoundError:
            return None

    def get_by_date(self, date, categories=None, primary_set=None):
        """
        If primary_set is None, then get primary_set by categories.

        Args:
            date: date
            categories: List[str] | None
            primary_set: str | None
        """
        psets = None
        if categories is not None:
            psets = set()
            for category in categories:
                psets.add(self.find_pset(category))
        else:
            psets = set(primary_set)
        if psets is None:
            return None

        d_date = datetime.strptime(date, "%Y-%m-%d")
        now = datetime.utcnow()
        if d_date + timedelta(days=1) > now:
            return None

        result = ArxivSet([])
        filter = ArxivFilter(categories=categories) if categories else None
        for pset in psets:
            cur_res = self.load_cache(pset, date)
            if cur_res is None:
                cur_res = self.request_and_cache(pset, date)
            if filter:
                cur_res = filter(cur_res)
            result = result.union(cur_res)

        return result
