import urllib
from lxml import etree
from typing import List, Optional
import time
import logging
import requests
from requests.adapters import HTTPAdapter, Retry
import aiohttp
import asyncio


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(logging.Formatter("%(asctime)s-%(name)s-%(levelname)s %(message)s"))
logger.addHandler(sh)


class ArxivRecord:
    def __init__(
        self,
        id="",
        title="",
        abstract="",
        categories=None,
        authors=None,
        published="",
        updated="",
    ) -> None:
        self.id = id
        self.title = title
        self.abstract = abstract
        self.categories = [] if categories is None else categories
        self.authors = [] if authors is None else authors
        self.published: Optional[str] = published
        self.updated: Optional[str] = updated


class ArxivAPI:
    OAI_xmlns = r"http://www.openarchives.org/OAI/2.0/"
    arxiv_xmlns = r"http://arxiv.org/OAI/arXiv/"

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
        if list_records is None:
            return ""
        for record_node in list_records:
            if f"{{{cls.OAI_xmlns}}}resumptionToken" == record_node.tag:
                resumption_token = record_node.text if record_node.text else ""
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
    def generate_url(self, resumption_token, from_time, until_time, pset):
        basic_url = "http://export.arxiv.org/oai2?verb=ListRecords"
        if resumption_token != "":
            true_url = f"{basic_url}&resumptionToken={urllib.parse.quote(resumption_token)}"
        else:
            true_url = basic_url
            if from_time:
                true_url += f"&from={from_time}"
            if until_time:
                true_url += f"&until={until_time}"
            if pset:
                true_url += f"&set={pset}"
            true_url += "&metadataPrefix=arXiv"
        return true_url

    @classmethod
    def get_records_by_oai(
        cls, from_time=None, until_time=None, pset=None
    ) -> List[ArxivRecord]:
        results = []
        resumption_token = ""
        sess = requests.Session()
        retries = Retry(total=5, status_forcelist=[429, 503], respect_retry_after_header=True)
        sess.mount("http://", HTTPAdapter(max_retries=retries))

        while True:
            true_url = cls.generate_url(resumption_token, from_time, until_time, pset)
            logger.info(f"Get from {true_url}")

            response = sess.get(true_url)
            response.raise_for_status()
            xml = response.content
            resumption_token = cls.from_oai_xml(xml, results)
            if resumption_token == "":
                break

            time.sleep(0.1)
        return results

    @classmethod
    async def async_get_records_by_oai(cls, from_time=None, until_time=None, pset=None) -> List[ArxivRecord]:
        results = []
        resumption_token = ""

        async with aiohttp.ClientSession() as sess:
            while True:
                true_url = cls.generate_url(resumption_token, from_time, until_time, pset)
                logger.info(f"Get from {true_url}")
                
                async with sess.get(true_url) as response:
                    if response.status == 503:
                        logger.info("Meet 503 status code")
                        if "Retry-After" in response.headers:
                            logger.info(f"retry-after: {response.headers['Retry-After']}")
                    xml = await response.read()
                    resumption_token = cls.from_oai_xml(xml, results)

                if resumption_token == "":
                    break

                await asyncio.sleep(0.1)

        return results
