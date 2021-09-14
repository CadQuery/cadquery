import pytest

from glob import glob
from itertools import chain, count

from path import Path

from docutils.parsers.rst import directives
from docutils.core import publish_doctree
from docutils.utils import Reporter

import cadquery as cq
from cadquery import cqgi
from cadquery.cq_directive import cq_directive


def find_examples(pattern="examples/*.py", path=Path("examples")):

    for p in glob(pattern):
        with open(p, encoding="UTF-8") as f:
            code = f.read()

        yield code, path


def find_examples_in_docs(pattern="doc/*.rst", path=Path("doc")):

    # dummy CQ directive for code
    class dummy_cq_directive(cq_directive):

        codes = []

        def run(self):

            self.codes.append("\n".join(self.content))

            return []

    directives.register_directive("cadquery", dummy_cq_directive)

    # read and parse all rst files
    for p in glob(pattern):
        with open(p, encoding="UTF-8") as f:
            doc = f.read()

        publish_doctree(
            doc, settings_overrides={"report_level": Reporter.SEVERE_LEVEL + 1}
        )

    # yield all code snippets
    for c in dummy_cq_directive.codes:

        yield c, path


@pytest.mark.parametrize(
    "code, path", chain(find_examples(), find_examples_in_docs()), ids=count(0)
)
def test_example(code, path):

    # build
    with path:
        res = cqgi.parse(code).build()

    assert res.exception is None

    # check if the resulting objects are valid
    for r in res.results:
        r = r.shape
        if isinstance(r, cq.Workplane):
            for v in r.vals():
                if isinstance(v, cq.Shape):
                    assert v.isValid()
        elif isinstance(r, cq.Shape):
            assert r.isValid()
