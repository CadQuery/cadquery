from mypy.plugin import Plugin, FunctionContext
from mypy.types import Type, UnionType


class CadqueryPlugin(Plugin):
    def get_function_hook(self, fullname: str):

        if fullname == "cadquery.occ_impl.shapes._get":

            return hook__get

        elif fullname == "cadquery.occ_impl.shapes._get_one":

            return hook__get_one

        return None


def hook__get(ctx: FunctionContext) -> Type:
    """
    Hook for cq.occ_impl.shapes._get

    Based on the second argument values it adjusts return type to an Iterator of specific subclasses of Shape.
    """

    return_type_names = [el.value for el in ctx.args[1][0].items]
    return_types =  UnionType([ctx.api.named_type(n) for n in return_type_names]
    )

    return ctx.api.named_generic_type("typing.Iterable", [return_types])

def hook__get_one(ctx: FunctionContext) -> Type:
    """
    Hook for cq.occ_impl.shapes._get_one

    Based on the second argument values it adjusts return type to a Union of specific subclasses of Shape.
    """

    return_type_names = [el.value for el in ctx.args[1][0].items]

    return  UnionType([ctx.api.named_type(n) for n in return_type_names])


def plugin(version: str):

    return CadqueryPlugin
