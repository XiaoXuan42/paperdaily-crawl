from arxiv import ArxivFilter, ArxivSet


class CategoryFilterConfig:
    def __init__(self, d: dict) -> None:
        self.categories = d.get("categories", [])
        self.authors = d.get("authors", [])
        self.keywd_in_title = d.get("keywd_in_title", [])
        self.keywd_in_abstract = d.get("keywd_in_abstract", [])

        self.category_filter = ArxivFilter(categories=self.categories)
        self.authors_filter = ArxivFilter(authors=self.authors)
        self.title_filter = ArxivFilter(keypoints_in_title=self.keywd_in_title)
        self.abstract_filter = ArxivFilter(
            keypoints_in_abstract=self.keywd_in_abstract
        )

    def filt(self, data: ArxivSet):
        tmp = self.category_filter(data)
        filters = [self.authors_filter, self.title_filter, self.abstract_filter]
        tmps = [f(tmp) for f in filters]
        res = ArxivSet([])
        for t in tmps:
            res = res.union(t)
        return res

    def get_str_attr(self, attr):
        val = getattr(self, attr)
        if val is None:
            return ""
        else:
            if isinstance(val, list):
                return ','.join([str(v) for v in val])
            return str(val)
