import { MinoriBaseAPI } from './base.js'
import { build_error } from '../common.js';
import { FullAlbum, Author, FullAuthor, AuthorAlias, Pagination } from '../models.js';

class MinoriAuthorsAPI extends MinoriBaseAPI {
  async get_page(page = 1) {
    const resp = await fetch(this.build_url('/authors', { page }))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get authors');
    }

    const json = await resp.json();
    return {
      authors: json.authors.map(i => new Author(i)),
      pagination: new Pagination(json.pagination)
    };
  }

  async get_one(author_id) {
    author_id = encodeURIComponent(author_id);
    const resp = await fetch(this.build_url(`/authors/${author_id}`))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get author');
    }

    return new FullAuthor((await resp.json()).author);
  }

  async update_name(author_id, name, update_corresponding_authoralias = true) {
    author_id = encodeURIComponent(author_id);
    const resp = await fetch(this.build_url(`/authors/${author_id}`, { update_corresponding_authoralias }), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to update author name');
    }

    return new Author((await resp.json()).author);
  }

  async delete(author_id) {
    author_id = encodeURIComponent(author_id);
    const resp = await fetch(this.build_url(`/authors/${author_id}`), {
      method: 'DELETE'
    })

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to delete author');
    }
  }

  async get_aliases(author_id) {
    author_id = encodeURIComponent(author_id);
    const resp = await fetch(this.build_url(`/authors/${author_id}/aliases`))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get author aliases');
    }

    return (await resp.json()).author_aliases.map(i => new AuthorAlias(i));
  }

  async get_albums(author_id, page = 1, include_disabled = undefined) {
    author_id = encodeURIComponent(author_id);
    const resp = await fetch(this.build_url(`/authors/${author_id}/albums`, { page, include_disabled }))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get author albums');
    }

    const json = await resp.json();
    return {
      albums: json.albums.map(i => new FullAlbum(i)),
      pagination: new Pagination(json.pagination)
    };
  }

  async merge_into_another(author_id, consumed_author_id, preserve_consumed_author = false) {
    author_id = encodeURIComponent(author_id);
    consumed_author_id = encodeURIComponent(consumed_author_id);

    const resp = await fetch(this.build_url(`/authors/${author_id}/merge/${consumed_author_id}`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preserve_consumed_author })
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to merge authors');
    }
  }
}

export { MinoriAuthorsAPI };
