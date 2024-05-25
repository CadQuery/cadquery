from mypy.plugin import Plugin, FunctionContext
from mypy.types import Type, UnionType


class CadqueryPlugin(Plugin):
    def get_function_hook(self, fullname: str):

        if fullname == "cadquery.occ_impl.shapes._get":

            return hook__get

        elif fullname == "cadquery.occ_impl.shapes._get_one":

            return hook__get_one

        elif fullname == "cadquery.occ_impl.shapes._get_edges":

            return hook__get_edges

        elif fullname == "cadquery.occ_impl.shapes._get_wires":

            return hook__get_wires

        return None


def hook__get(ctx: FunctionContext) -> Type:
    """
    Hook for cq.occ_impl.shapes._get

    Based on the second argument values it adjusts return type to an Iterator of specific subclasses of Shape.
    """

    if hasattr(ctx.args[1][0], "items"):
        return_type_names = [el.value for el in ctx.args[1][0].items]
    else:
        return_type_names = [ctx.args[1][0].value]

    return_types = UnionType([ctx.api.named_type(n) for n in return_type_names])

    return ctx.api.named_generic_type("typing.Iterable", [return_types])


def hook__get_one(ctx: FunctionContext) -> Type:
    """
    Hook for cq.occ_impl.shapes._get_one

    Based on the second argument values it adjusts return type to a Union of specific subclasses of Shape.
    """

    if hasattr(ctx.args[1][0], "items"):
        return_type_names = [el.value for el in ctx.args[1][0].items]
    else:
        return_type_names = [ctx.args[1][0].value]

    return UnionType([ctx.api.named_type(n) for n in return_type_names])


def hook__get_wires(ctx: FunctionContext) -> Type:
    """
    Hook for cq.occ_impl.shapes._get_wires
   """

    return_type = ctx.api.named_type("Wire")

    return ctx.api.named_generic_type("typing.Iterable", [return_type])


def hook__get_edges(ctx: FunctionContext) -> Type:
    """
    Hook for cq.occ_impl.shapes._get_edges
   """

    return_type = ctx.api.named_type("Edge")

    return ctx.api.named_generic_type("typing.Iterable", [return_type])


def plugin(version: str):

    return CadqueryPlugin
