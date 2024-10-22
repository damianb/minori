import { format_error_msg } from '../common.js';
import { AlbumMetadataElem, ImageElem } from '../elems.js';
import { MinoriUI } from './base.js';

class MinoriAlbumUI extends MinoriUI {
  constructor() {
    super();

    this.album_id = null;
    this.album_metadata_hoist = document.querySelector('#album-meta');
    this.hoist = document.querySelector('#images');
    this.image_count_hoist = document.querySelector('#images-count');
    this.album_elem = new AlbumMetadataElem(this, this.album_metadata_hoist);
    this.image_elem = new ImageElem(this, this.hoist);

    this.load_config()
      .then(this.load.bind(this))
      .then(this.bind_event_handlers.bind(this))
      .catch(err => {
        if (err.status === 404) {
          this.toggle_display_404(true);
          this.toggle_loading_spinner(false);

          return;
        }

        this.ui_toast('danger', format_error_msg(err));
        throw err;
      });
  }

  flush() {
    const els = this.hoist.querySelectorAll(ImageElem.TagName);
    els.forEach(el => this.hoist.removeChild(el));
  }

  async load() {
    this.album_id = this.extract_id_from_hash(0);
    const album = await this.api.albums.get_one(this.album_id);
    const images = await this.api.images.get_all(this.album_id);
    this.album_elem.lifecycle(album, false);

    images.forEach((image) => {
      this.image_elem.lifecycle(image, false);
    }, this);

    this.image_count_hoist.innerText = images.length;
    this.image_count_hoist.classList.remove('collapse');
    this.update_page_title(album.title);
    this.toggle_loading_spinner(false);
    this.toggle_show_content(true);
  }

  reload() {
    this.toggle_loading_spinner(true);
    this.toggle_show_content(false);
    this.flush();
    return this.load();
  }

  bind_event_handlers() {
    document.querySelector('button[type="submit"]').addEventListener('click', (ev) => {
      window.setTimeout(() => {
        window.location.href = this.album_elem.album_edit_url();
      }, 1);
      ev.preventDefault();
    });

    document.querySelector('button#download').addEventListener('click', (ev) => {
      window.setTimeout(() => {
        const album_id = encodeURIComponent(this.album_id);
        window.open(this.api.base.build_url(`/albums/${album_id}/download`), '_blank').focus();
      }, 1);
      ev.preventDefault();
    });

    document.querySelector('button#reload').addEventListener('click', (ev) => {
      this.reload();
      ev.preventDefault();
    });

    // for now, we won't use an automatic reload on album image lists
    // window.setInterval(() => {
    //   this.reload();
    // }, 15 * 60 * 1000 /* every 15 mins */);
  }
}

export { MinoriAlbumUI };
