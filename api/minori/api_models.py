''' models for use with fastapi (request/response structures) '''

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, PositiveInt # pylint: disable=no-name-in-module

class CreateAlbumRequestModel(BaseModel):
    ''' Request body model for creating or updating a new Album '''

    title: Optional[str] = Field(
        description='The title of the album.',
        min_length=1,
        max_length=255,
        default='Untitled album'
    )
    author: Optional[str] = Field(
        description='The author of the album.',
        max_length=120,
        default=None
    )
    description: Optional[str] = Field(
        description='The description of the album.',
        max_length=1000,
        default=None
    )
    url: Optional[str] = Field(
        description='The source URL of the album.',
        max_length=2000,
        default=None
    )

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'title': 'Some Album',
                    'author': 'Someauthor',
                    'description': 'A brief explanation of the purpose or overall contents of the album.',
                    'url': 'https://example.com/where-the/album/came-from'
                }
            ]
        }
    }

class UpdateAlbumRequestModel(BaseModel):
    ''' Request body model for updating an Album '''

    title: Optional[str] = Field(
        description='The title of the album.',
        min_length=1,
        max_length=255,
        default=None
    )
    author: Optional[str] = Field(
        description='The author of the album.',
        max_length=120,
        default=None
    )
    description: Optional[str] = Field(
        description='The description of the album.',
        max_length=1000,
        default=None
    )
    url: Optional[str] = Field(
        description='The source URL of the album.',
        max_length=2000,
        default=None
    )

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'title': 'Some Album',
                    'author': 'Someauthor',
                    'description': 'A brief explanation of the purpose or overall contents of the album.',
                    'url': 'https://example.com/where-the/album/came-from'
                }
            ]
        }
    }

class UpdateImageOrderRequestModel(BaseModel):
    ''' Request body model for updating an image's order in an album '''

    order: PositiveInt = Field(
        description='The new order value for the image.'
    )

class UpdateAuthorRequestModel(BaseModel):
    ''' Request body model for updating an Author '''

    name: str = Field(
        description='The name of the author.',
        max_length=120,
        default=None
    )

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'name': 'Someauthor'
                }
            ]
        }
    }

class UpdateAuthorAliasRequestModel(BaseModel):
    ''' Request body model for updating an AuthorAlias '''

    name: str = Field(
        description='The alias of the author.',
        max_length=120,
        default=None
    )

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'name': 'Someauthoralias'
                }
            ]
        }
    }

class BaseAlbumModel(BaseModel):
    ''' base api model for Albums '''

    id: str = Field(description='Reference ID for the album.')
    disabled: bool = Field(description='Whether or not the album is available for listing.')
    title: str = Field(
        description='Title for the album.',
        default='Untitled album'
    )
    description: Optional[str] = Field(
        description='Description for the album.',
        default=None
    )
    url: Optional[str] = Field(
        description='Source URL for the album.',
        default=None
    )
    created_at: datetime = Field(description='ISO-8601 timestamp of when the album was created.')

class AlbumModel(BaseAlbumModel):
    ''' api model for Albums, including full author and author alias data '''

    author_alias: Optional[FullAuthorAliasModel] = Field(
        description='Author of the album.',
        default=None
    )

class FullAlbumModel(BaseAlbumModel):
    ''' api model for Albums that includes a cover image reference and tags '''

    author_alias: Optional[FullAuthorAliasModel] = Field(
        description='Author of the album.',
        default=None
    )

    cover: Optional[ImageModel] = Field(
        description='The cover image for the album.',
        default=None
    )

    tags: list[TagModel] = Field(
        description='The tags applied to the album.',
        default=[]
    )

class TagModel(BaseModel):
    ''' api model for Tags '''

    id: str = Field(description='Reference ID for the tag.')
    namespace: Optional[str] = Field(
        description='Namespace of the tag.',
        default=None
    )
    name: str = Field(description='Name of the tag.')
    description: Optional[str] = Field(
        description='Description for the tag.',
        default=None
    )

class ImageModel(BaseModel):
    ''' api model for Images '''

    id: str = Field(description='Reference ID for the image.')
    filename: Optional[str] = Field(
        description='Filename of the image.',
        default=None
    )
    original_filename: Optional[str] = Field(
        description='Original filename of the image.',
        default=None
    )
    uploaded: bool = Field(description='Whether the image has been uploaded.')
    created_at: datetime = Field(description='ISO-8601 timestamp of when the image was created.')
    uploaded_at: Optional[datetime] = Field(
        description='ISO-8601 timestamp of when the image was uploaded.',
        default=None
    )
    album_order_key: int = Field(description='The order in which this image appears within the album.')

class AuthorModel(BaseModel):
    ''' api model for Authors '''

    id: str = Field(description='Reference ID for the author.')
    name: str = Field(description='The author name.')

class FullAuthorModel(AuthorModel):
    ''' api model for authors that includes authors and associated aliases '''

    author_aliases: list[AuthorAliasModel] = Field(description='Associated aliases for the author.')

class AuthorAliasModel(BaseModel):
    ''' api model for Author aliases '''

    id: str = Field(description='Reference ID for the author alias.')
    name: str = Field(description='The author alias.')

class FullAuthorAliasModel(AuthorAliasModel):
    ''' api model for Author aliases + authors backref '''

    author: Optional[AuthorModel] = Field(description='The canonical author reference.')

class PaginationModel(BaseModel):
    ''' api model for pagination information '''

    first_page: int = Field(description='The first page number for the content.')
    previous_page: Literal[False] | int = Field(description='The previous page number for the content.')
    current_page: int = Field(description='The current page number for the content.')
    next_page: Literal[False] | int  = Field(description='The next page number for the content')
    last_page: int = Field(description='The last page number for the content')

    total_records: int = Field(description='The number of records available in total.')

class AlbumResponseModel(BaseModel):
    ''' response model for Album-centric endpoints '''
    album: AlbumModel

class AlbumsResponseModel(BaseModel):
    ''' response model for multi-Album-centric endpoints '''
    albums: list[AlbumModel]

class FullAlbumResponseModel(BaseModel):
    ''' response model for FullAlbum endpoints '''
    album: FullAlbumModel

class FullAlbumsResponseModel(BaseModel):
    ''' response model for multi-FullAlbum endpoints '''
    albums: list[FullAlbumModel]

class PaginatedFullAlbumsResponseModel(FullAlbumsResponseModel):
    ''' response model for multi-FullAlbum endpoints that also provides pagination information '''
    pagination: PaginationModel

class TagResponseModel(BaseModel):
    ''' response model for Tag-centric endpoints '''
    tag: TagModel

class TagsResponseModel(BaseModel):
    ''' response model for multi-Tag-centric endpoints '''
    tags: list[TagModel]

class ImageResponseModel(BaseModel):
    ''' response model for Image-centric endpoints '''
    image: ImageModel

class ImagesResponseModel(BaseModel):
    ''' response model for multi-Image-centric endpoints '''
    images: list[ImageModel]

class AuthorResponseModel(BaseModel):
    ''' response model for multi-Author-centric endpoints '''
    author: AuthorModel

class AuthorsResponseModel(BaseModel):
    ''' response model for multi-Author-centric endpoints '''
    authors: list[AuthorModel]

class FullAuthorResponseModel(BaseModel):
    ''' response model for FullAuthor endpoints '''
    author: FullAuthorModel

class FullAuthorsResponseModel(BaseModel):
    ''' response model for multi-FullAuthor endpoints '''
    authors: list[FullAuthorModel]

class PaginatedAuthorsResponseModel(AuthorsResponseModel):
    ''' response model for multi-Author endpoints that also provides pagination information '''
    pagination: PaginationModel

class AuthorAliasResponseModel(BaseModel):
    ''' response model for AuthorAlias-centric endpoints '''
    author_alias: AuthorAliasModel

class AuthorAliasesResponseModel(BaseModel):
    ''' response model for multi-AuthorAlias-centric endpoints '''
    author_aliases: list[AuthorAliasModel]

class FullAuthorAliasResponseModel(BaseModel):
    ''' response model for full AuthorAlias-centric endpoints '''
    author_alias: FullAuthorAliasModel

class PaginatedAuthorAliasesResponseModel(AuthorAliasesResponseModel):
    ''' response model for multi-AuthorAlias endpoints that also provides pagination information '''
    pagination: PaginationModel

class OperationResultModel(BaseModel):
    ''' Response model for true/false operation results being returned by endpoints '''
    success: bool

class HealthCheckResponseModel(BaseModel):
    ''' response model for healthcheck endpoint '''
    healthy: bool
