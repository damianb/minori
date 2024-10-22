import { format_error_msg } from '../common.js';
import { AuthorMetadataElem, AuthorAliasListElem, AlbumElem, AlbumPaginationElem } from '../elems.js';
import { MinoriUI } from './base.js';

class MinoriAuthorUI extends MinoriUI {
  constructor() {
    super();

    this.author_id = null;

    this.author_hoist = document.querySelector('#author-metadata');
    this.author_aliases_hoist = document.querySelector('#author-aliases');
    this.album_hoist = document.querySelector('#albums');
    this.pagination_hoist = document.querySelector('#pagination-hoist');

    this.album_count_hoist = document.querySelector('#albums-count');

    this.author_elem = new AuthorMetadataElem(this, this.author_hoist);
    this.alias_elem = new AuthorAliasListElem(this, this.author_aliases_hoist);
    this.album_elem = new AlbumElem(this, this.album_hoist);
    this.pagination_elem = new AlbumPaginationElem(this, this.pagination_hoist);

    this.current_page = Math.floor(this.extract_id_from_hash(1) || 1);

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
    let els = this.author_aliases_hoist.querySelectorAll(AuthorAliasListElem.TagName);
    els.forEach(el => this.author_aliases_hoist.removeChild(el));

    els = this.album_hoist.querySelectorAll(AlbumElem.TagName);
    els.forEach(el => this.album_hoist.removeChild(el));
  }

  async load() {
    this.author_id = this.extract_id_from_hash(0);
    this.current_page = Math.floor(this.extract_id_from_hash(1) || 1);
    const author = await this.api.authors.get_one(this.author_id);
    const aliases = await this.api.authors.get_aliases(this.author_id);
    const { albums, pagination } = await this.api.authors.get_albums(this.author_id, this.current_page, this.maint_mode);

    this.author_elem.lifecycle(author);

    aliases.forEach((authoralias) => {
      this.alias_elem.lifecycle(authoralias, false);
    }, this);

    albums.forEach((album) => {
      this.album_elem.lifecycle(album, false);
    }, this);

    this.pagination_elem.lifecycle(pagination);

    this.album_count_hoist.innerText = pagination.total_records;
    this.album_count_hoist.classList.remove('collapse');

    this.update_page_title(`Author Details: ${author.name}`);
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
    window.addEventListener('hashchange', (ev) => {
      if (this.current_page !== this.extract_id_from_hash(1)) {
        this.toggle_show_content(false);
        this.toggle_loading_spinner(true);
        this.current_page = this.extract_id_from_hash(1);
        this.flush();
        this.load()
          .catch(err => {
            this.ui_toast('danger', format_error_msg(err));
            throw err;
          });
      }
    });

    // document.querySelector('button[type="submit"]').addEventListener('click', (ev) => {
    //   window.setTimeout(() => {
    //     window.location.href = this.album_elem.album_edit_url();
    //   }, 1);
    //   ev.preventDefault();
    // });

    document.querySelector('button#reload').addEventListener('click', (ev) => {
      this.reload();
      ev.preventDefault();
    });

    document.querySelector('img#homelab-icon').addEventListener('click', (ev) => {
      this.toggle_maint_mode();
      this.reload();
      ev.preventDefault();
    });
  }
}

export { MinoriAuthorUI };
