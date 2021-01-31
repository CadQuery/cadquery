import pytest

from glob import glob
from itertools import chain

from docutils.parsers.rst import directives, Directive
from docutils.core import publish_doctree


import cadquery as cq
from cadquery import cqgi
from cadquery.cq_directive import cq_directive


def find_examples(pattern="examples/*.py"):

    for p in glob(pattern):
        with open(p) as f:
            code = f.read()

        yield code


def find_examples_in_docs(pattern="doc/*.rst"):

    # dummy CQ directive for code
    class dummy_cq_directive(cq_directive):

        codes = []

        def run(self):

            self.codes.append("\n".join(self.content))

            return []

    directives.register_directive("cadquery", dummy_cq_directive)

    # read and parse all rst files
    for p in glob(pattern):
        with open(p) as f:
            doc = f.read()

        publish_doctree(doc)

    # yield all code snippets
    for c in dummy_cq_directive.codes:

        yield c


@pytest.mark.parametrize("code", chain(find_examples(), find_examples_in_docs()))
def test_example(code):

    # build
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
