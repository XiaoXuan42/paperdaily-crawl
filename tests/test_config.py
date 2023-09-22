from config import CategoryFilterConfig
from arxiv import ArxivRecord, ArxivSet


def test_Config():
    config = CategoryFilterConfig(
        {
            "categories": ["cs.AI", "cs.CG"],
            "authors": ["luka judy"],
            "keypoints_in_title": ["transformer", "token"],
            "keypoints_in_abstract": ["novel"],
        }
    )
    records = [
        ArxivRecord(
            title="tranformer for object detection",
            authors=["luka judy", "ken"],
            categories=["cs.AI"],
        ),
        ArxivRecord(title="nnmm", categories=["cs.CG"]),
        ArxivRecord(title="hello world", abstract="A novel idea"),
        ArxivRecord(authors=["ken tompson", "luka judy"], categories=["cs.AI"]),
        ArxivRecord(
            title="functional analysis", authors=["Henry"], published="2023-10-01"
        ),
    ]
    st = config.filt(ArxivSet(records))
    assert len(st) == 2
