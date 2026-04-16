import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime,
    Integer, Text, ForeignKey, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class PostCategory(str, enum.Enum):
    soil_crops     = "Soil & Crops"
    livestock      = "Livestock"
    agritech       = "AgriTech"
    sustainability = "Sustainability"
    business       = "Business"
    irrigation     = "Irrigation"
    climate        = "Climate"      # present in placeholder data
    other          = "Other"


class PostSectionType(str, enum.Enum):
    paragraph = "paragraph"
    heading   = "heading"
    quote     = "quote"
    image     = "image"


class Post(Base):
    __tablename__ = "posts"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug            = Column(String, unique=True, nullable=False, index=True)
    author_id       = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Author snapshot — captured at write time
    author_name     = Column(String, nullable=False)
    author_initials = Column(String, nullable=False)
    author_bio      = Column(Text,   nullable=True)
    author_avatar   = Column(String, nullable=True)

    # Content
    title           = Column(String,  nullable=False)
    excerpt         = Column(Text,    nullable=False)
    image           = Column(String,  nullable=True)
    category        = Column(SAEnum(PostCategory), nullable=False)
    tags            = Column(String,  nullable=True)   # comma-separated
    read_time       = Column(String,  nullable=True)

    # Denormalised stats
    likes           = Column(Integer, default=0)
    comments        = Column(Integer, default=0)

    is_published    = Column(Boolean,  default=False)
    published_at    = Column(DateTime, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    sections      = relationship(
        "PostSection", back_populates="post",
        cascade="all, delete-orphan",
        order_by="PostSection.order"
    )
    post_likes    = relationship(
        "PostLike", back_populates="post",
        cascade="all, delete-orphan"
    )
    post_comments = relationship(
        "Comment", back_populates="post",
        cascade="all, delete-orphan"
    )


class PostSection(Base):
    __tablename__ = "post_sections"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id     = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    type        = Column(SAEnum(PostSectionType), nullable=False)
    content     = Column(Text,   nullable=False)
    caption     = Column(String, nullable=True)       # image only
    attribution = Column(String, nullable=True)       # quote only
    order       = Column(Integer, default=0)

    post = relationship("Post", back_populates="sections")


class PostLike(Base):
    __tablename__ = "post_likes"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id    = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    user_id    = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="post_likes")


class Comment(Base):
    __tablename__ = "comments"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id         = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    author_id       = Column(UUID(as_uuid=True), nullable=False)
    author_name     = Column(String, nullable=False)
    author_initials = Column(String, nullable=False)
    body            = Column(Text,   nullable=False)
    likes           = Column(Integer, default=0)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    post          = relationship("Post", back_populates="post_comments")
    comment_likes = relationship(
        "CommentLike", back_populates="comment",
        cascade="all, delete-orphan"
    )


class CommentLike(Base):
    __tablename__ = "comment_likes"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=False)
    user_id    = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    comment = relationship("Comment", back_populates="comment_likes")