import re
import inflect


def camel_to_snake(name: str) -> str:
    # Handles CamelCase, camelCase, and acronyms
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def snake_to_camel(name: str, pascal: bool = False) -> str:
    parts = name.split("_")
    if pascal:
        return "".join(word.capitalize() for word in parts)
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


p_engine = inflect.engine()


def plural(name: str):
    return p_engine.plural(name)


def normalize_modelname(modelname: str):
    snk = camel_to_snake(modelname)
    if snk.endswith("_model"):
        snk = snk.removesuffix("_model")
    return plural(snk)
