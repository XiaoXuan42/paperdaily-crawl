import urllib.request
from lxml import etree
from typing import List


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
    def from_oai_xml(cls, xml) -> List[ArxivRecord]:
        if isinstance(xml, (str, bytes)):
            xml = etree.fromstring(xml)
        list_records = xml.find(f"{{{cls.OAI_xmlns}}}ListRecords")
        results = []
        for record_node in list_records:
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
        return results

    @classmethod
    def get_records_by_oai(cls, from_time=None, until_time=None, set=None) -> List[ArxivRecord]:
        basic_url = "http://export.arxiv.org/oai2?verb=ListRecords"
        url = basic_url
        if from_time:
            url += f"&from={from_time}"
        if until_time:
            url += f"&until={until_time}"
        url += "&metadataPrefix=arXiv"
        if set:
            url += f"&set={set}"
        with urllib.request.urlopen(url) as res:
            xml = res.read()
            return cls.from_oai_xml(xml)
