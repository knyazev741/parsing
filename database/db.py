from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import models


class Database:
    def __init__(self, base_url):
        engine = create_engine(base_url)
        models.Base.metadata.create_all(bind=engine)
        self.maker = sessionmaker(bind=engine)

    def _get_or_create_comment(self, session, comment):
        if comment is not None:
            for com in comment:
                self._get_or_create(session, models.Comment, models.Comment.id,
                                            com["id"], **com)

    def _get_or_create(self, session, model, field, value, **kwargs):
        db_data = session.query(model).filter(field == value).first()
        if not db_data:
            db_data = model(**kwargs)
            session.add(db_data)
            try:
                session.commit()
            except Exception as ex:
                session.rollback()
                print(ex)
        return db_data

    def create_post(self, data):
        session = self.maker()
        self._get_or_create_comment(session, data["comments"])
        author = self._get_or_create(session, models.Author, models.Author.author_url, data["author"]["author_url"],
                                     **data["author"])
        tag = map(lambda tags: self._get_or_create(session, models.Tag, models.Tag.url, tags["url"], **tags),
                  data["tags"])
        post = self._get_or_create(session, models.Post, models.Post.url, data["post_data"]["url"], **data["post_data"],
                                   author=author)
        post.tags.extend(tag)
        session.add(post)

        try:
            session.commit()
        except Exception as ex:
            session.rollback()
            print(ex)
        finally:
            session.close()
