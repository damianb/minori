import { format_error_msg } from '../common.js';
import { AuthorListElem, AuthorPaginationElem } from '../elems.js';
import { MinoriUI } from './base.js';

class MinoriAuthorlistUI extends MinoriUI {
  constructor() {
    super();

    this.hoist = document.querySelector('#authors');
    this.pagination_hoist = document.querySelector('#pagination-hoist');

    this.author_elem = new AuthorListElem(this, this.hoist);
    this.pagination_elem = new AuthorPaginationElem(this, this.pagination_hoist);

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
    const els = this.hoist.querySelectorAll(AuthorListElem.TagName);
    els.forEach(el => this.hoist.removeChild(el));
  }

  async load() {
    const { authors, pagination } = await this.api.authors.get_page(this.current_page);
    authors.forEach((author) => {
      this.author_elem.lifecycle(author, false);
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
  }
}

export { MinoriAuthorlistUI };
