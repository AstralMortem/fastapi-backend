from fastapi_backend.db import Model, Mapped, mapped_column, ForeignKey


class Post(Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("auth.User"))
