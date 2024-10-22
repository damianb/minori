''' database setup and modules '''

from __future__ import annotations

from datetime import datetime
from typing import Optional

import shortuuid
from sqlalchemy import MetaData
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs

import minori.api_models as models

class Base(AsyncAttrs, DeclarativeBase):
    ''' base class for tables '''

    __table_args__ =  {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_bin'
    }

    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

album_tag_xref_table = Table(
    'album_tag_xref',
    Base.metadata,
    Column('album_id', ForeignKey('album.id'), primary_key=True),
    Column('tag_id', ForeignKey('tag.id'), primary_key=True),
)

class Author(Base):
    ''' DB model for Author elements '''

    __tablename__ = 'author'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(32), default=lambda : shortuuid.uuid(), unique=True) # pylint: disable=unnecessary-lambda
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    author_aliases: Mapped[list['AuthorAlias']] = relationship(back_populates='author', foreign_keys='AuthorAlias.author_id')

    def to_model(self) -> models.AuthorModel:
        ''' Convert DB object to API model '''

        return models.AuthorModel(
            id=self.uuid,
            name=self.name
        )

    def to_full_model(self) -> models.FullAuthorModel:
        ''' Convert DB object to API model '''

        return models.FullAuthorModel(
            id=self.uuid,
            name=self.name,
            author_aliases=[author_alias.to_model() for author_alias in self.author_aliases]
        )

class AuthorAlias(Base):
    ''' DB model for Author Alias elements '''

    __tablename__ = 'authoralias'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(32), default=lambda : shortuuid.uuid(), unique=True) # pylint: disable=unnecessary-lambda
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('author.id'), nullable=False)

    author: Mapped['Author'] = relationship(foreign_keys=[author_id])
    albums: Mapped[list['Album']] = relationship(back_populates='author_alias', foreign_keys='Album.author_alias_id')

    def to_model(self) -> models.AuthorAliasModel:
        ''' Convert DB object to API model '''

        return models.AuthorAliasModel(
            id=self.uuid,
            name=self.name
        )

    def to_full_model(self) -> models.FullAuthorAliasModel:
        ''' Convert DB object to API model '''

        return models.FullAuthorAliasModel(
            id=self.uuid,
            name=self.name,
            author=self.author.to_model() if self.author is not None else None
        )

class Album(Base):
    ''' DB model for Album elements '''

    __tablename__ = 'album'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(32), default=lambda : shortuuid.uuid(), unique=True) # pylint: disable=unnecessary-lambda
    disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    title: Mapped[str] = mapped_column(String(256), nullable=False, default='Untitled album')
    author: Mapped[str] = mapped_column(String(128), nullable=False, default='Unknown author')
    author_alias_id: Mapped[int] = mapped_column(ForeignKey('authoralias.id'))
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    album_cover_id: Mapped[Optional[int]] = mapped_column(ForeignKey('image.id'), nullable=True)

    tags: Mapped[list[Tag]] = relationship(
        secondary=album_tag_xref_table,
        back_populates='albums',
        cascade='all, delete'
    )

    images: Mapped[list['Image']] = relationship(back_populates='album', cascade='all, delete-orphan', foreign_keys='Image.album_id')
    album_cover: Mapped[Optional['Image']] = relationship(foreign_keys=[album_cover_id])
    author_alias: Mapped[Optional['AuthorAlias']] = relationship(foreign_keys=[author_alias_id])

    def to_model(self, include_author_alias = False) -> models.AlbumModel:
        ''' Convert DB object to API model '''

        return models.AlbumModel(
            id=self.uuid,
            disabled=self.disabled,
            title=self.title,
            author_alias=self.author_alias.to_full_model() if include_author_alias and self.author_alias is not None else None,
            description=self.description,
            url=self.url,
            created_at=self.created_at
        )

    def to_full_model(self) -> models.FullAlbumModel:
        ''' Convert DB object to API model (including cover entry and tags) '''

        return models.FullAlbumModel(
            id=self.uuid,
            disabled=self.disabled,
            title=self.title,
            author_alias=self.author_alias.to_full_model() if self.author_alias is not None else None,
            description=self.description,
            url=self.url,
            created_at=self.created_at,
            cover=self.album_cover.to_model() if self.album_cover is not None else None,
            tags=[tag.to_model() for tag in self.tags]
        )

class Image(Base):
    ''' DB model for Image elements '''

    __tablename__ = 'image'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(32), default=lambda : shortuuid.uuid(), unique=True) # pylint: disable=unnecessary-lambda
    filename: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    uploaded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    album_id: Mapped[int] = mapped_column(ForeignKey('album.id'))
    album: Mapped['Album'] = relationship(back_populates='images', foreign_keys=[album_id])
    album_order_key: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def to_model(self) -> models.ImageModel:
        ''' Convert object to dict representation (for API serialization) '''

        return models.ImageModel(
            id=self.uuid,
            filename=self.filename,
            original_filename=self.original_filename,
            uploaded=self.uploaded,

            created_at=self.created_at,
            uploaded_at=self.uploaded_at,

            album_order_key=self.album_order_key
        )

class Tag(Base):
    ''' DB model for Tag elements '''

    __tablename__ = 'tag'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(32), default=lambda : shortuuid.uuid(), unique=True) # pylint: disable=unnecessary-lambda

    namespace: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    albums: Mapped[list[Album]] = relationship(
        secondary=album_tag_xref_table,
        back_populates='tags'
    )

    def to_model(self) -> models.TagModel:
        ''' Convert DB object to API model '''

        return models.TagModel(
            id=self.uuid,
            namespace=self.namespace,
            name=self.name
        )

    def to_string(self) -> str:
        ''' Converts tag to string form '''

        return f'{self.namespace}:{self.name}' if self.namespace else self.name
