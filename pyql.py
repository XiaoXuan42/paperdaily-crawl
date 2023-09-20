"""
pyql: Python Query Language

Introduction:
A language to get a list of content from json/dict/object.

Syntax:
Stmt := Selector > Stmt
Selector := KeySelector | &ValueSelector
KeySelector := "key" | Predicate
ValueSelector := Predicate | \epsilon
Predicate := expr("python expressions") | func("function name") | all
"""


class PyQlASTNode:
    def eat_whitespace(self, s: str, p: int):
        while p < len(s) and s[p] == " ":
            p += 1
        return p

    def parse_str(self, s: str, p: int):
        p = self.eat_whitespace(s, p)
        if p >= len(s) - 1 or s[p] != '"':
            return None, p
        p += 1
        init_p = p
        trans = False
        while s[p] != '"' or trans:
            if trans:
                trans = False
            elif s[p] == "\\":
                trans = True
            p += 1
            if p >= len(s):
                return None, p
        res = s[init_p:p]
        p += 1
        return res, p


class PyQlPredicate(PyQlASTNode):
    def __init__(self) -> None:
        super().__init__()
        self.type = "expr"
        self.predicate = None

    def parse(self, s: str, p: int):
        p = self.eat_whitespace(s, p)
        if p >= len(s):
            raise ValueError(f"Stmt start at {p} is not a valid predicate.")
        if s[p:].startswith("expr"):
            self.type = "expr"
            p += len("expr") + 1
            st, new_p = self.parse_str(s, p)
            if st is None:
                raise ValueError(f"Stmt start at {p} is not a valid expression.")
            self.predicate = st
            if new_p >= len(s) or s[new_p] != ")":
                raise ValueError(f"Expect ')' at {new_p}.")
            return new_p + 1
        elif s[p:].startswith("func"):
            self.type = "func"
            p += len("func") + 1
            st, new_p = self.parse_str(s, p)
            if st is None:
                raise ValueError(f"Stmt at {p} is not a valid function.")
            self.predicate = st
            if new_p >= len(s) or s[new_p] != ")":
                raise ValueError(f"Expect ')' at {new_p}")
            return new_p + 1
        elif s[p:].startswith("all"):
            self.type = "all"
            return p + 3
        else:
            raise ValueError(f"Stmt start at {p} is not a valid predicate.")


class PyQlKeySelector(PyQlASTNode):
    def __init__(self) -> None:
        self.selector = None

    def parse(self, s: str, p: int):
        p = self.eat_whitespace(s, p)
        if p >= len(s):
            raise ValueError(f"Stmt start at {p} is not a valid key selector.")
        if s[p] == '"':
            st, new_p = self.parse_str(s, p)
            if st is None:
                raise ValueError(f"Stmt at {p} is not a valid key selector.")
            self.selector = st
            return new_p
        else:
            self.selector = PyQlPredicate()
            return self.selector.parse(s, p)


class PyQlValueSelector(PyQlASTNode):
    def __init__(self) -> None:
        self.predicate = None

    def parse(self, s: str, p: int):
        p = self.eat_whitespace(s, p)
        if p >= len(s):
            self.predicate = None
            return p
        else:
            self.predicate = PyQlPredicate()
            return self.predicate.parse(s, p)


class PyQlStmt(PyQlASTNode):
    def __init__(self) -> None:
        super().__init__()
        self.selectors = []

    def parse(self, s: str, p: int):
        p = self.eat_whitespace(s, p)
        if p >= len(s):
            raise ValueError(f"Stmt at {p} is not a statement.")
        new_selectors = []
        while p < len(s):
            if s[p] == "&":
                p += 1
                valsel = PyQlValueSelector()
                p = valsel.parse(s, p)
                new_selectors.append(valsel)
            else:
                keysel = PyQlKeySelector()
                p = keysel.parse(s, p)
                new_selectors.append(keysel)
            p = self.eat_whitespace(s, p)

        self.selectors = new_selectors


class PyQlAST:
    def __init__(self) -> None:
        self.stmt = PyQlStmt()

    def parse(self, s: str):
        self.stmt.parse(s, 0)


class PyQl:
    def __init__(self, env) -> None:
        self.env = env

    def all_keys(self, obj):
        return list(obj.keys())

    def all_values(self, obj):
        return obj

    def _predicate(self, p: PyQlPredicate, v, *args):
        if p.predicate is None or p.type == "all":
            return True
        elif p.type == "expr":
            return eval(p.predicate, globals=self.env, locals={"v": v})
        elif p.type == "func":
            func = self.env(p.predicate)
            return func(v, *args)
        else:
            raise ValueError(f"Invalid predicate {p}")

    def _select(self, selector, v, *args):
        if isinstance(selector, PyQlKeySelector):
            if isinstance(selector.selector, str):
                return v == selector.selector
            elif isinstance(selector.selector, PyQlPredicate):
                return self._predicate(selector.selector, v, *args)
            else:
                raise ValueError(f"Invalid KeySelector")
        elif isinstance(selector, PyQlValueSelector):
            if selector.predicate is None:
                return True
            elif isinstance(selector.predicate, PyQlValueSelector):
                return self._predicate(selector.predicate, v, *args)
            else:
                raise ValueError(f"Invalid ValueSelector")
        else:
            raise ValueError(f"Invalid selector {selector}")

    def select_keys(self, selector, obj, keys):
        return [k for k in keys if self._select(selector, k, obj[k])]

    def select_values(self, selector, values):
        return [v for v in values if self._select(selector, v)]

    def _execute_selectors(self, obj, selectors: list):
        if len(selectors) == 0:
            raise ValueError(f"Incompatible query")
        else:
            cur_selector = selectors[0]
            if isinstance(cur_selector, PyQlKeySelector):
                chosen_keys = self.select_keys(cur_selector, obj, self.all_keys(obj))
                result = {}
                for k in chosen_keys:
                    if len(selectors) > 1:
                        result[k] = self._execute_selectors(obj[k], selectors[1:])
                    else:
                        result[k] = obj[k]
                return result
            elif isinstance(cur_selector, PyQlValueSelector):
                chosen_values = self.select_values(cur_selector, self.all_values(obj))
                if len(selectors) > 1:
                    result = [
                        self._execute_selectors(val, selectors[1:])
                        for val in chosen_values
                    ]
                else:
                    result = chosen_values
                return result

    def _execute(self, obj, stmt: PyQlStmt):
        return self._execute_selectors(obj, stmt.selectors)

    def execute(self, obj, s):
        if isinstance(s, str):
            stmt = PyQlStmt()
            stmt.parse(s, 0)
            return self._execute(obj, stmt)
        elif isinstance(s, PyQlAST):
            return self._execute(obj, s.stmt)
        elif isinstance(s, PyQlStmt):
            return self._execute(obj, s)
        else:
            raise ValueError(f"Invalid argument: {s}")
