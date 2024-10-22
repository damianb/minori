import { format_error_msg } from '../common.js';
import { AlbumElem, AlbumPaginationElem } from '../elems.js';
import { MinoriUI } from './base.js';

class MinoriBookshelfUI extends MinoriUI {
  constructor() {
    super();

    this.hoist = document.querySelector('#albums');
    this.pagination_hoist = document.querySelector('#pagination-hoist');

    this.album_elem = new AlbumElem(this, this.hoist);
    this.pagination_elem = new AlbumPaginationElem(this, this.pagination_hoist);

    this.current_page = Math.floor(this.extract_id_from_hash(0) || 1);

    this.load_config()
      .then(this.load.bind(this))
      .then(this.bind_event_handlers.bind(this))
      .catch(err => {
        this.ui_toast('danger', format_error_msg(err));
        throw err;
      });
  }

  flush() {
    const els = this.hoist.querySelectorAll(AlbumElem.TagName);
    els.forEach(el => this.hoist.removeChild(el));
  }

  async load() {
    const { albums, pagination } = await this.api.albums.get_page(this.current_page, this.maint_mode);
    albums.forEach((album) => {
      this.album_elem.lifecycle(album, false);
    }, this);

    this.pagination_elem.lifecycle(pagination);
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
      this.api.albums.create()
        .then((album) => {
          this.ui_toast('success', 'Album created, redirecting...');

          return new AlbumElem(this, this.hoist, album);
        })
        .then((album_elem) => {
          return window.setTimeout(() => {
            window.location.href = album_elem.album_edit_url();
          }, 1000);
        })
        .catch((err) => {
          this.ui_toast('danger', format_error_msg(err));
          throw err;
        });

      ev.preventDefault();
    });

    window.addEventListener('hashchange', (ev) => {
      if (this.current_page !== this.extract_id_from_hash(0)) {
        this.toggle_show_content(false);
        this.toggle_loading_spinner(true);
        this.current_page = this.extract_id_from_hash(0);
        this.flush();
        this.load()
          .catch(err => {
            this.ui_toast('danger', format_error_msg(err));
            throw err;
          });
      }
    });

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

export { MinoriBookshelfUI };
