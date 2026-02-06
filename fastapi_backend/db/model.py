from typing import ClassVar, Self, TypeVar, Tuple, TYPE_CHECKING
from sqlalchemy.orm import declared_attr, registry, DeclarativeBase
from sqlalchemy import MetaData, inspect as sa_inspect
from fastapi_backend.modules.registry import modules, ModulesRegistry
from .session import async_session_context, sync_session_context
from .manager import Manager
from fastapi_backend.utils.string import normalize_modelname

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

mapper_registry = registry(metadata=metadata)
M = TypeVar("M", bound="Model")


class Model(DeclarativeBase):

    metadata = mapper_registry.metadata
    registry = mapper_registry

    # __abstract__ = True
    __module_label__: str
    __module_reg__: ModulesRegistry
    repr_fields: ClassVar[Tuple[str]] = ()


    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        label = getattr(cls, "__module_label__", None)
        modelname = normalize_modelname(cls.__name__)
        if not label:
            return modelname
        return f"{label}_{modelname}"
    
    if TYPE_CHECKING:
        objects: Manager[Self]

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)

        # Don't register/attach Manager for abstract classes
        if getattr(cls, "__abstract__", False):
            return

        py_module = getattr(cls, "__module__", None)

        module_config = modules.get_containing_module_config(py_module)

        module_label = getattr(cls, "__module_label__", None)
        if module_label is None:
            if module_config is None:
                raise RuntimeError(
                    f"Model class {py_module}.{cls.__name__} doesn't declare an explicit "
                    f"model_label and isn't in an application in INSTALLED_MODULES."
                )
            module_label = module_config.label

        cls.__module_label__ = module_label
        cls.__module_reg__ = modules
        cls.__module_reg__.register_model(cls.__module_label__, cls)
        cls.objects = Manager(cls)

    def save(self):
        with sync_session_context() as session:
            session.add(self)
            session.commit()
            session.flush()
            return self

    async def asave(self):
        async with async_session_context() as session:
            session.add(self)
            await session.commit()
            await session.flush()
            return self

    def delete(self):
        with sync_session_context() as session:
            session.delete(self)
            session.commit()
            session.flush()
            return None

    async def adelete(self):
        async with async_session_context() as session:
            await session.delete(self)
            await session.commit()
            await session.flush()
            return None


    def __repr__(self):
        fields = {}
        if not self.repr_fields:
            res = sa_inspect(self.__class__)
            for col in list(res.mapper.columns):
                if col.primary_key and col.key:
                    fields[col.key] = getattr(self, col.key)
                
                if len(fields) < 3:
                    fields[col.key] = getattr(self, col.key)
                else:
                    break
        else:
            for field_name in self.repr_fields:
                fields[field_name] = getattr(self, field_name)

        data = ", ".join([f"{k}={v}" for k, v in fields.items()])

        return f"<{self.__class__.__name__} {data}>"
    
    def __str__(self):
        return self.__repr__()

        
