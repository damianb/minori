import { format_error_msg } from '../common.js';
import { FullImageElem, ImagePaginationElem } from '../elems.js';
import { MinoriUI } from './base.js';

class MinoriImageUI extends MinoriUI {
  constructor() {
    super();

    this.hoist = document.querySelector('#image-hoist');
    this.pagination_hoist = document.querySelector('#pagination-hoist');

    this.return_hoist = document.querySelector('#album-return');
    this.image_elem = new FullImageElem(this, this.hoist);
    this.pagination_elem = new ImagePaginationElem(this, this.pagination_hoist);

    this.current_album_id = this.extract_id_from_hash(0);
    this.current_image_id = this.extract_id_from_hash(1);
    this.album = null;
    this.images = {};
    this.images_list = [];
    this.pagination_data = {};

    this.load_config()
      .then(this.load.bind(this))
      .then(this.bind_event_handlers.bind(this))
      .then(this.render.bind(this))
      .catch(err => {
        if (err.status === 404) {
          this.toggle_display_404(true);
          this.toggle_show_content(false);
          this.toggle_loading_spinner(false);

          return;
        }

        this.ui_toast('danger', format_error_msg(err));
        throw err;
      });
  }

  async load() {
    this.album = await this.api.albums.get_one(this.current_album_id);
    const images = await this.api.images.get_all(this.current_album_id);
    this.images = {};
    this.images_list = [];
    images.forEach((image) => {
      this.images[image.id] = image;
      this.images_list.push(image.id);
    });

    if(this.current_image_id === false) {
      this.current_image_id = this.images_list[0];
      window.location.hash = `${this.current_album_id}:${this.current_image_id}`
    }

    if(!this.images_list.includes(this.current_image_id)) {
      throw { status: 404 }
    }
  }

  render() {
    this.pagination_data = this.get_image_pagination(this.current_image_id);
    this.pagination_elem.lifecycle(this.pagination_data);
    this.update_return_button();
    this.image_elem.lifecycle(this.images[this.current_image_id]);

    const theImage = this.hoist.querySelector('img');
    let visibleFired = false;
    const makeVisible = () => {
      visibleFired = true;
      this.toggle_loading_spinner(false);
      this.toggle_show_content(true);
    };

    theImage.addEventListener('load', makeVisible);
    if(theImage.complete && visibleFired === false) {
      theImage.removeEventListener('load', makeVisible);
      makeVisible();
    }

    this.preload_adjacent_images();
    this.update_page_title(`${this.album.title} (${this.pagination_data.current_page}/${this.pagination_data.total_pages})`);
  }

  bind_event_handlers() {
    this.pagination_hoist.addEventListener('click', (ev) => {
      const classList = ev.target.classList;
      if (classList.contains('disabled')) {
        return;
      }

      if (classList.contains('nav-focus')) {
        return;
      }

      if (classList.contains('nav-first')
          || classList.contains('nav-prev')
          || classList.contains('nav-next')
          || classList.contains('nav-last')) {
        window.location.href = ev.target.href;
        ev.preventDefault();
      }
    });

    this.hoist.addEventListener('click', (ev) => {
      if (!ev.target.classList.contains('album-image')) {
        return;
      }

      const edgeSize = ev.target.clientWidth / 3;
      if(ev.offsetX <= edgeSize) {
        // previous page
        ev.preventDefault();
        if(this.pagination_data.previous_id === false) {
          return;
        }

        window.location.href = this.pagination_hoist.querySelector('.nav-prev').href;
      } else if (ev.offsetX >= (ev.target.clientWidth - edgeSize)) {
        // next page
        ev.preventDefault();
        if(this.pagination_data.next_id === false) {
          return;
        }

        window.location.href = this.pagination_hoist.querySelector('.nav-next').href;
      }
    });

    window.addEventListener('hashchange', (ev) => {
      // if nothing changed, ignore this event
      if (this.current_album_id === this.extract_id_from_hash(0) && this.current_image_id === this.extract_id_from_hash(1)) {
        return;
      }

      if (this.current_album_id !== this.extract_id_from_hash(0)) {
        this.toggle_display_404(false);
        this.toggle_show_content(false);
        this.toggle_loading_spinner(true);
        this.current_album_id = this.extract_id_from_hash(0);
        this.current_image_id = this.extract_id_from_hash(1);
        this.load()
          .then(this.render.bind(this))
          .catch(err => {
            if (err.status === 404) {
              this.toggle_display_404(true);
              this.toggle_show_content(false);
              this.toggle_loading_spinner(false);
              this.update_page_title();
            }

            this.ui_toast('danger', format_error_msg(err));
            throw err;
          });
      } else if (this.current_image_id !== this.extract_id_from_hash(1)) {
        this.nav_update();
      }
    });
  }

  update_return_button() {
    this.return_hoist.querySelector('a').setAttribute('href', this.pagination_elem.album_url());
    this.return_hoist.classList.remove('collapse');
  }

  nav_update() {
    this.toggle_show_content(false);
    this.toggle_loading_spinner(true);
    this.current_image_id = this.extract_id_from_hash(1);
    this.render();
  }

  preload_adjacent_images() {
    if(this.pagination_data.previous_id) {
      const prevImg = new Image();
      prevImg.src = this.pagination_elem.image_url(this.images[this.pagination_data.previous_id].filename);
    }

    if(this.pagination_data.next_id) {
      const nextImg = new Image();
      nextImg.src = this.pagination_elem.image_url(this.images[this.pagination_data.next_id].filename);
    }
  }

  get_image_pagination(image_id) {
    // safeguard, this shouldn't get this far
    if(!this.images_list.includes(image_id)) {
      return false;
    }

    const image_index = this.images_list.indexOf(image_id);

    return {
      'album_id': this.current_album_id,
      'full_image_uri': this.images[image_id].filename,
      'current_page': image_index + 1,
      'total_pages': this.images_list.length,
      'first_id': image_index !== 0 ? this.images_list[0] : false,
      'previous_id': image_index !== 0 ? this.images_list[image_index - 1] : false,
      'current_id': image_id,
      'next_id': (image_index + 1) !== this.images_list.length ? this.images_list[image_index + 1] : false,
      'last_id': (image_index + 1) !== this.images_list.length ? this.images_list[this.images_list.length - 1] : false
    };
  }
}

export { MinoriImageUI };
