from tortoise.models import ModelMeta, MetaInfo, Model as TortoiseModel
from tortoise.fields.relational import OneToOneFieldInstance
from fastapi_backend.modules.registry import ModulesRegistry, modules

__all__ = ["Model"]


class ModelMetaInfo(MetaInfo):
    __slots__ = MetaInfo.__slots__ + ("registry",)

    def __init__(self, meta):
        super().__init__(meta)
        self.registry: ModulesRegistry = getattr(meta, "registry", modules)


class ModelMetaclass(ModelMeta):
    def __new__(cls, name, bases, attrs):
        parents = [b for b in bases if isinstance(b, ModelMetaclass)]
        if not parents:
            return super().__new__(cls, name, bases, attrs)

        py_module = attrs.get("__module__", None)
        meta_class: Model.Meta = attrs.get("Meta", type("Meta", (), {}))
        is_abstract = getattr(meta_class, "abstract", False)

        module_label = None
        module_config = modules.get_containing_module_config(py_module)

        if getattr(meta_class, "app", None) is None:
            if module_config is None:
                if not is_abstract:
                    raise RuntimeError(
                        "Model class %s.%s doesn't declare an explicit "
                        "app and isn't in an application in "
                        "INSTALLED_MODULES." % (py_module, name)
                    )
            else:
                module_label = module_config.label

        meta_class.app = module_label
        attrs["Meta"] = meta_class
        new_class = super().__new__(cls, name, bases, attrs)
        new_class._meta.registry.register_model(new_class._meta.app, new_class)
        return new_class

    @staticmethod
    def build_meta(
        meta_class,
        fields_map,
        fields_db_projection,
        filters,
        fk_fields,
        o2o_fields,
        m2m_fields,
        pk_attr,
    ):
        meta = ModelMetaInfo(meta_class)
        meta.fields_map = fields_map
        meta.fields_db_projection = fields_db_projection
        meta._filters = filters
        meta.fk_fields = fk_fields
        meta.o2o_fields = o2o_fields
        meta.m2m_fields = m2m_fields
        meta.pk_attr = pk_attr
        if pk_field := fields_map.get(pk_attr):
            meta.pk = pk_field
            if pk_field.source_field:
                meta.db_pk_column = pk_field.source_field
            elif isinstance(pk_field, OneToOneFieldInstance):
                meta.db_pk_column = f"{pk_attr}_id"
            else:
                meta.db_pk_column = pk_attr
        meta._inited = False
        if not fields_map:
            meta.abstract = True
        return meta


class Model(TortoiseModel, metaclass=ModelMetaclass):
    _meta = ModelMetaInfo(None)
