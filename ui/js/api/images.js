import { MinoriBaseAPI } from './base.js'
import { build_error } from '../common.js';
import { Image } from '../models.js';

class MinoriImagesAPI extends MinoriBaseAPI {
  async get_all(id) {
    id = encodeURIComponent(id);
    const resp = await fetch(this.build_url(`/albums/${id}/images`))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get album images');
    }

    return (await resp.json()).images.map(i => new Image(i));
  }

  async create(id) {
    id = encodeURIComponent(id);

    const resp = await fetch(this.build_url(`/albums/${id}/images/-/create`), {
      method: 'POST'
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to create album image');
    }

    return new Image((await resp.json()).image);
  }

  async upload(album_id, image_id, file_elem) {
    album_id = encodeURIComponent(album_id);
    image_id = encodeURIComponent(image_id);

    const form = new FormData();
    form.append('file', file_elem.files[0]);

    const resp = await fetch(this.build_url(`/albums/${album_id}/images/${image_id}/upload`), {
      method: 'PUT',
      body: form
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to upload album image');
    }

    return new Image((await resp.json()).image);
  }

  async upload_archive(id, file_elem) {
    id = encodeURIComponent(id);

    const form = new FormData();
    form.append('file', file_elem.files[0]);

    const resp = await fetch(this.build_url(`/albums/${id}/images/-/bulkcreate`), {
      method: 'POST',
      body: form
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to upload album image archive');
    }

    return (await resp.json()).images.map(i => new Image(i));
  }

  async get_one(album_id, image_id) {
    album_id = encodeURIComponent(album_id);
    image_id = encodeURIComponent(image_id);
    const resp = await fetch(this.build_url(`/albums/${album_id}/images/${image_id}`))

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to get album image');
    }

    return new Image((await resp.json()).image);
  }

  async update_order(album_id, image_id, order) {
    album_id = encodeURIComponent(album_id);
    image_id = encodeURIComponent(image_id);

    const resp = await fetch(this.build_url(`/albums/${album_id}/images/${image_id}/order`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order })
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to update album image order');
    }

    return new Image((await resp.json()).image);
  }

  async mark_as_cover(album_id, image_id) {
    album_id = encodeURIComponent(album_id);
    image_id = encodeURIComponent(image_id);

    const resp = await fetch(this.build_url(`/albums/${album_id}/images/${image_id}/make-cover`), {
      method: 'POST'
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to mark album image as cover');
    }
  }

  async delete(album_id, image_id) {
    album_id = encodeURIComponent(album_id);
    image_id = encodeURIComponent(image_id);

    const resp = await fetch(this.build_url(`/albums/${album_id}/images/${image_id}`), {
      method: 'DELETE'
    });

    if(!resp.ok) {
      throw await build_error(resp, 'Failed to delete album image');
    }
  }
}

export { MinoriImagesAPI };
