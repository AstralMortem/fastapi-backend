from fastapi_backend.modules import modules
from fastapi_backend.conf import settings

modules.populate(settings.INSTALLED_MODULES)

print(modules.all_models)

from fastapi_backend.db import Model
from fastapi_backend.db.session import sync_engine


with sync_engine.begin() as conn:
    Model.metadata.create_all(conn)


from posts.models import Post

# user1 = User(id=1, username="Vlad").save()


# post1 = Post(id=1, title="Post", author_id=user1.id).save()

print(Post.objects.get_or_none(id=1))
