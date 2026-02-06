from typing import Sequence, Any
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import aliased


def resolve_attr_with_joins(model, stmt, path: Sequence[str]):
    """
    Resolve a Django-like path into a SQLAlchemy attribute, adding JOINs for relationships.

    Example:
      model=Order, path=["user", "email"]
      -> stmt JOIN user, returns UserAlias.email
    """
    current_entity = model
    current_path: list[str] = []
    aliases: dict[tuple[str, ...], Any] = {}

    for i, part in enumerate(path):
        current_path.append(part)

        # last segment => column/attribute on current entity (model or alias)
        if i == len(path) - 1:
            try:
                attr = getattr(current_entity, part)
            except AttributeError as e:
                raise AttributeError(
                    f"'{getattr(current_entity, '__name__', current_entity)}' "
                    f"has no attribute '{part}' (path: {'__'.join(path)})"
                ) from e
            return attr, stmt

        # relationship step
        mapper = sa_inspect(current_entity)
        rel = mapper.relationships.get(part)
        if rel is None:
            raise AttributeError(
                f"'{mapper.class_.__name__}' has no relationship '{part}' "
                f"(path: {'__'.join(path)})"
            )

        path_key = tuple(current_path)
        if path_key not in aliases:
            target_cls = rel.mapper.class_
            target_alias = aliased(target_cls)
            aliases[path_key] = target_alias

            # Join using relationship attribute on current entity
            stmt = stmt.join(target_alias, getattr(current_entity, part))

        current_entity = aliases[path_key]

    raise RuntimeError("Bad path resolution")
