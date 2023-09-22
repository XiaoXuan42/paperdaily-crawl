from arxiv import ArxivFilter, ArxivSet


class CategoryFilterConfig:
    def __init__(self, d: dict) -> None:
        self.categories = d["categories"]
        self.authors = d.get("authors", [])
        self.keypoints_in_title = d.get("keypoints_in_title", [])
        self.keypoints_in_abstract = d.get("keypoints_in_abstract", [])

        self.category_filter = ArxivFilter(categories=self.categories)
        self.authors_filter = ArxivFilter(authors=self.authors)
        self.title_filter = ArxivFilter(keypoints_in_title=self.keypoints_in_title)
        self.abstract_filter = ArxivFilter(
            keypoints_in_abstract=self.keypoints_in_abstract
        )

    def filt(self, data: ArxivSet):
        tmp = self.category_filter(data)
        filters = [self.authors_filter, self.title_filter, self.abstract_filter]
        tmps = [f(tmp) for f in filters]
        res = ArxivSet([])
        for t in tmps:
            res = res.union(t)
        return res
