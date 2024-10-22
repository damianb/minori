import { MinoriBaseAPI } from './base.js'
import { build_error } from '../common.js';
import { Album, FullAlbum, Pagination } from '../models.js';

class MinoriAlbumsAPI extends MinoriBaseAPI {
  async get_page(page = 1, include_disabled = undefined) {
    const resp = await fetch(this.build_url('/albums', { page, include_disabled }))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get albums');
    }

    const json = await resp.json();
    return {
      albums: json.albums.map(i => new FullAlbum(i)),
      pagination: new Pagination(json.pagination)
    };
  }

  async get_all(include_disabled = undefined) {
    const resp = await fetch(this.build_url('/albums/all', { include_disabled }))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get albums');
    }

    return (await resp.json()).albums.map(i => new Album(i));
  }

  async create(title, author, description, url) {
    let args = {
      title: title ?? undefined,
      author: author ?? undefined,
      description: description ?? undefined,
      url: url ?? undefined
    }

    const resp = await fetch(this.build_url('/albums/-/create'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(args)
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to create album');
    }

    return new Album((await resp.json()).album);
  }

  async get_one(id) {
    id = encodeURIComponent(id);
    const resp = await fetch(this.build_url(`/albums/${id}`))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get album');
    }

    return new FullAlbum((await resp.json()).album);
  }

  async update(id, title, author, description, url) {
    id = encodeURIComponent(id);

    const resp = await fetch(this.build_url(`/albums/${id}`), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, author, description, url })
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to update album');
    }

    return new Album((await resp.json()).album);
  }

  async regen_thumbnails(id) {
    id = encodeURIComponent(id);

    const resp = await fetch(this.build_url(`/albums/${id}/regen-thumbnails`), {
      method: 'POST'
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to regenerate album image thumbnails');
    }
  }

  async toggle(id, state) {
    id = encodeURIComponent(id);
    const resp = await fetch(this.build_url(`/albums/${id}/toggle`, { state }), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to toggle album');
    }

    return new Album((await resp.json()).album);
  }

  async delete(id) {
    id = encodeURIComponent(id);
    const resp = await fetch(this.build_url(`/albums/${id}`), {
      method: 'DELETE'
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to delete album');
    }
  }
}

export { MinoriAlbumsAPI };
