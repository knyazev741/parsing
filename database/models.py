from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Table

Base = declarative_base()

tag_post = Table(
    "tag_post",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_id", Integer, ForeignKey("tag.id"))
)


class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    first_img = Column(String)
    publish_date = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("author.id"))
    author = relationship("Author")
    comments = relationship("Comment")
    tags = relationship("Tag", secondary=tag_post)


class Author(Base):
    __tablename__ = "author"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_name = Column(String, nullable=False)
    author_url = Column(String, unique=True, nullable=False)
    posts = relationship("Post")


class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    url = Column(String, unique=True, nullable=False)
    posts = relationship("Post", secondary=tag_post)


class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)
    author_name = Column(String, nullable=False)
    author_url = Column(Integer, nullable=False)
    text = Column(String)
    parent_id = Column(Integer)
    post = relationship("Post")
    post_id = Column(Integer, ForeignKey("post.id"))




