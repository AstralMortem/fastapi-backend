from fastapi_backend.db import Model, Mapped, mapped_column


class User(Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
