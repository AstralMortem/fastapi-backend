from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Optional, Union, Type, Tuple

from sqlalchemy import ForeignKey as SA_ForeignKey
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from fastapi_backend.modules import modules

TargetSpec = Union[
    str,                         # "module.Model" or "module.Model.field"
    type,                        # Model class
    Callable[[], type],          # lazy model class (lambda: Model)
    InstrumentedAttribute,       # Model.field (relationship or column attr; we'll validate column)
]

def _is_lazy_model(obj: Any) -> bool:
    # zero-arg callable returning a class
    return callable(obj) and not isinstance(obj, type)

def _parse_string_target(value: str) -> Tuple[str, str, Optional[str]]:
    """
    "module.Model" -> (module, Model, None)
    "module.Model.field" -> (module, Model, field)
    """
    parts = value.split(".")
    if len(parts) == 2:
        return parts[0], parts[1], None
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    raise ValueError(
        f"Invalid target string {value!r}. Expected 'module.Model' or 'module.Model.field'."
    )

def _resolve_model_from_registry(module_label: str, model_name: str) -> type:
    try:
        return modules.get_model(module_label, model_name)
    except ValueError as e:
        raise LookupError(
            f"Model not found in registry: {module_label}.{model_name}"
            f"Known modules: {list(modules.all_models.keys())}"
        ) from e

def _model_pk_column(model: type):
    mapper = sa_inspect(model)
    pk_cols = list(mapper.primary_key)
    if not pk_cols:
        raise ValueError(f"Model {model.__name__} has no primary key.")
    if len(pk_cols) > 1:
        # If you want composite PK support, force explicit ".field"
        raise ValueError(
            f"Model {model.__name__} has a composite primary key; "
            f"specify an explicit column (e.g. 'module.Model.some_pk_part')."
        )
    return pk_cols[0]

def _resolve_column(target: TargetSpec):
    # 1) string
    if isinstance(target, str):
        module_label, model_name, field = _parse_string_target(target)
        model = _resolve_model_from_registry(module_label, model_name)
        if field is None:
            return _model_pk_column(model)
        try:
            col = sa_inspect(model).columns[field]
        except KeyError as e:
            raise AttributeError(
                f"Column {field!r} not found on model {module_label}.{model_name}."
            ) from e
        return col

    # 2) lazy model callable -> model class -> pk
    if _is_lazy_model(target):
        model = target()
        if not isinstance(model, type):
            raise TypeError(f"Lazy model callable must return a model class, got: {model!r}")
        return _model_pk_column(model)

    # 3) model class -> pk
    if isinstance(target, type):
        return _model_pk_column(target)

    # 4) Model.field (InstrumentedAttribute)
    if isinstance(target, InstrumentedAttribute):
        # For columns: .property.columns exists. For relationships: it won’t.
        prop = getattr(target, "property", None)
        cols = getattr(prop, "columns", None)
        if not cols:
            raise TypeError(
                f"{target} does not look like a column attribute. "
                f"Pass a column attribute (Model.some_column) or a model/string target."
            )
        if len(cols) != 1:
            raise ValueError("Composite / multi-column attributes are not supported here.")
        return cols[0]

    raise TypeError(
        "Unsupported target. Expected 'module.Model[.field]', ModelClass, "
        "lambda: ModelClass, or ModelClass.field"
    )

def ForeignKey(
    target: TargetSpec,
    *,
    ondelete: Optional[str] = None,
    onupdate: Optional[str] = None,
    deferrable: Optional[bool] = None,
    initially: Optional[str] = None,
    match: Optional[str] = None,
    name: Optional[str] = None,
    use_alter: Optional[bool] = None,
) -> SA_ForeignKey:
    """
    Returns a sqlalchemy.ForeignKey object suitable for mapped_column(...).

    Examples:
      mapped_column(ForeignKey("test_app1.User"))              -> user.id
      mapped_column(ForeignKey("test_app1.User.uuid"))         -> user.uuid
      mapped_column(ForeignKey(User))                          -> user.pk
      mapped_column(ForeignKey(lambda: User))                  -> user.pk
      mapped_column(ForeignKey(User.id))                       -> user.id
    """
    col = _resolve_column(target)
    fk_target = f"{col.table.fullname}.{col.key}"  # schema-aware, uses actual column key

    return SA_ForeignKey(
        fk_target,
        ondelete=ondelete,
        onupdate=onupdate,
        deferrable=deferrable,
        initially=initially,
        match=match,
        name=name,
        use_alter=use_alter,
    )
