from cadquery.utils import cqmultimethod as multimethod

from pytest import raises


def test_multimethod():
    class A:
        @multimethod
        def f(self, a: int, c: str = "s"):
            return 1

        @f.register
        def f(self, a: int, b: int, c: str = "b"):
            return 2

    assert A().f(0, "s") == 1
    assert A().f(0, c="s") == 1
    assert A().f(0) == 1

    assert A().f(0, 1, c="s") == 2
    assert A().f(0, 1, "s") == 2
    assert A().f(0, 1) == 2

    assert A().f(a=0, c="s") == 1

    with raises(TypeError):
        A().f(a=0, b=1, c="s")
