import { format_error_msg } from '../common.js';
import { AlbumListElem } from '../elems.js';
import { MinoriUI } from './base.js';

class MinoriAlbumlistUI extends MinoriUI {
  constructor() {
    super();

    this.hoist = document.querySelector('#albums');
    this.album_count_hoist = document.querySelector('#albums-count');

    this.album_elem = new AlbumListElem(this, this.hoist);

    this.load_config()
      .then(this.load.bind(this))
      .then(this.bind_event_handlers.bind(this))
      .catch(err => {
        this.ui_toast('danger', format_error_msg(err));
        throw err;
      });
  }

  flush() {
    const els = this.hoist.querySelectorAll(AlbumListElem.TagName);
    els.forEach(el => this.hoist.removeChild(el));
  }

  async load() {
    const albums = await this.api.albums.get_all(this.maint_mode);
    albums.forEach((album) => {
      this.album_elem.lifecycle(album, false);
    }, this);

    this.album_count_hoist.innerText = albums.length;
    this.album_count_hoist.classList.remove('collapse');
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
    document.querySelector('button#reload').addEventListener('click', (ev) => {
      this.reload();
      ev.preventDefault();
    });

    document.querySelector('img#homelab-icon').addEventListener('click', (ev) => {
      this.toggle_maint_mode();
      this.reload();
      ev.preventDefault();
    });

    window.setInterval(() => {
      this.reload();
    }, 15 * 60 * 1000 /* every 15 mins */);
  }
}

export { MinoriAlbumlistUI };
