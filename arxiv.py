import urllib.request
from lxml import etree
from typing import List
from datetime import datetime, timedelta
import pickle
import os
import copy


class ArxivRecord:
    def __init__(self) -> None:
        self.id = ""
        self.title = ""
        self.abstract = ""
        self.categories = []
        self.authors = []
        self.published = ""
        self.updated = ""


class ArxivAPI:
    OAI_xmlns = r"http://www.openarchives.org/OAI/2.0/"
    arxiv_xmlns = r"http://arxiv.org/OAI/arXiv/"

    @classmethod
    def _oai_xml_attr_text(cls, metadata_node, attr):
        try:
            text = metadata_node.find(f"{{{cls.arxiv_xmlns}}}{attr}").text
            return text
        except AttributeError:
            return ""

    @classmethod
    def _oai_xml_authors(cls, metadata_node):
        try:
            results = []
            authors_node = metadata_node.find(f"{{{cls.arxiv_xmlns}}}authors")
            for author_node in authors_node:
                keyname = author_node.find(f"{{{cls.arxiv_xmlns}}}keyname").text
                forenames = author_node.find(f"{{{cls.arxiv_xmlns}}}forenames").text
                results.append(f"{forenames} {keyname}")
            return results
        except (AttributeError, TypeError):
            return []

    @classmethod
    def from_oai_xml(cls, xml, results):
        if isinstance(xml, (str, bytes)):
            xml = etree.fromstring(xml)
        list_records = xml.find(f"{{{cls.OAI_xmlns}}}ListRecords")
        resumption_token = ""
        for record_node in list_records:
            if f"{{{cls.OAI_xmlns}}}resumptionToken" == record_node.tag:
                resumption_token = record_node.text
                break
            metadata_node = record_node.find(f"{{{cls.OAI_xmlns}}}metadata")[0]
            record = ArxivRecord()
            record.id = cls._oai_xml_attr_text(metadata_node, "id")
            record.title = cls._oai_xml_attr_text(metadata_node, "title")
            record.abstract = cls._oai_xml_attr_text(metadata_node, "abstract")
            record.published = cls._oai_xml_attr_text(metadata_node, "created")
            record.updated = cls._oai_xml_attr_text(metadata_node, "updated")

            categories = cls._oai_xml_attr_text(metadata_node, "categories")
            if categories:
                record.categories = categories.split(" ")

            record.authors = cls._oai_xml_authors(metadata_node)

            results.append(record)
        return resumption_token

    @classmethod
    def get_records_by_oai(
        cls, from_time=None, until_time=None, set=None
    ) -> List[ArxivRecord]:
        basic_url = "http://export.arxiv.org/oai2?verb=ListRecords"
        url = basic_url
        if from_time:
            url += f"&from={from_time}"
        if until_time:
            url += f"&until={until_time}"
        url += "&metadataPrefix=arXiv"
        if set:
            url += f"&set={set}"
        results = []
        resumption_token = ""
        while True:
            true_url = url
            if resumption_token != "":
                true_url += f"&resumptionToken={resumption_token}"
            with urllib.request.urlopen(true_url) as res:
                xml = res.read()
                resumption_token = cls.from_oai_xml(xml, results)
                if resumption_token == "":
                    break
        return results


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


class ArxivDaily(ArxivSet):
    def __init__(self, date, pset, records: List[ArxivRecord]) -> None:
        super().__init__(records)
        self.date = date
        self.pset = pset


class ArxivFilter:
    def __init__(self, categories=None) -> None:
        if categories is None:
            self.categories = None
        else:
            if isinstance(categories, (list, tuple)):
                categories = [categories]
            self.categories = set(categories)

    def _filter_by_category(self, record: ArxivRecord):
        if self.categories is None:
            return True
        else:
            st = self.categories.intersection(set(record.categories))
            if len(st) > 0:
                return True
        return False

    def filter(self, records: List[ArxivRecord]):
        res = []
        for record in records:
            if self._filter_by_category(record):
                res.append(res)
        return res


_default_asset_root = os.path.join(os.path.dirname(__file__), "arxiv")


class ArxivAsset:
    primary_set = {
        "cs",
        "econ",
        "eess",
        "math",
        "physics",
        "physics:astro-ph",
        "physics:cond-mat",
        "physics:gr-qc",
        "physics:hep-ex",
        "physics:hep-lat",
        "physics:hep-ph",
        "physics:hep-th",
        "physics:math-ph",
        "physics:nlin",
        "physics:nucl-ex",
        "physics:nucl-th",
        "physics:physics",
        "physics:quant-ph",
        "q-bio",
        "q-fin",
        "stat",
    }
    categories_set = {
        "cs": {
            "cs.AI",  # artificial intelligence
            "cs.AR",  # hardware architecture
            "cs.CC",  # computational complexity
            "cs.CE",  # computational engineering, finance and science
            "cs.CG",  # computational geometry
            "cs.CL",  # computation and language
            "cs.CR",  # cryptography and security
            "cs.CV",  # computer vision and pattern recognition
            "cs.CY",  # computers and society
            "cs.DB",  # databases
            "cs.DC",  # distributed, parallel and cluster computing
            "cs.DL",  # digital libraries
            "cs.DM",  # discrete mathematics
            "cs.DS",  # data structure and algorithms
            "cs.ET",  # emerging technologies
            "cs.FL",  # formal languages
            "cs.GL",  # general literature
            "cs.GR",  # graphics
            "cs.GT",  # computer science and game theory
            "cs.HC",  # human-computer interaction
            "cs.IR",  # information retrieval
            "cs.IT",  # information theory
            "cs.LG",  # machine learning
            "cs.LO",  # logic
            "cs.MA",  # multiagent systems
            "cs.MM",  # multimedia
            "cs.MS",  # mathematical software
            "cs.NA",  # numerical analysis
            "cs.NE",  # neural and evolutionary computing
            "cs.NI",  # networking and Internet architecture
            "cs.OH",  # other computer science
            "cs.OS",  # operating system
            "cs.PF",  # performance
            "cs.PL",  # programming language
            "cs.RO",  # robotics
            "cs.SC",  # symbolic computation
            "cs.SD",  # sound
            "cs.SE",  # software engineering
            "cs.SI",  # social and information networks
            "cs.SY",  # systems and control
        }
    }

    def __init__(self, root=_default_asset_root):
        self.root = root
        self._cached_daily = {}

    def find_pset(self, category):
        for pset, cts in self.categories_set.items():
            if category in cts:
                return pset
        return None

    def _get_cache_path(self, pset, date):
        return os.path.join(self.root, pset, date)

    def cache(self, data: ArxivDaily, pset, date):
        path = self._get_cache_path(pset, date)
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def request_and_cache(self, pset, date):
        try:
            d_date = datetime.strptime(date, "%Y-%m-%d")
            d_yesterday = d_date - timedelta(days=1)
            s_yesterday = d_yesterday.strftime("%Y-%m-%d")
            records = ArxivAPI.get_records_by_oai(
                from_time=s_yesterday, until_time=date, set=pset
            )
            arxiv_daily = ArxivDaily(records)
            self.cache(arxiv_daily, pset, date)
            return arxiv_daily

        except FileNotFoundError:
            return None

    def load_cache(self, pset, date):
        if pset in self._cached_daily:
            if date in self._cached_daily[pset]:
                return self._cached_daily[pset][date]

        path = self._get_cache_path(pset, date)
        try:
            with open(path, "wb") as f:
                res = pickle.load(f)
                self._cached_daily.setdefault(pset, {})
                self._cached_daily[pset][date] = res
                return res
        except FileNotFoundError:
            return None

    def get_by_date(self, category, date):
        pset = self.find_pset(category)
        if pset is None:
            return None
        d_date = datetime.strptime(date, "%Y-%m-%d")
        now = datetime.utcnow()
        if d_date + timedelta(days=1) > now:
            return None

        res = self.load_cache(pset, date)
        if res is None:
            res = self.request_and_cache(pset, date)
        return res


if __name__ == "__main__":
    arxiv = ArxivAsset()
    print(arxiv.get_by_date("cs.AI", "2023-09-20"))
