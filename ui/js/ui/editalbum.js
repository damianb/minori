import { esc, format_error_msg } from '../common.js';
import { ImageEditElem } from '../elems.js';
import { MinoriUI } from './base.js';

class MinoriEditAlbumUI extends MinoriUI {
  constructor() {
    super();

    this.album_id = null;
    this.album = null;
    this.images = null;
    this.image_deletes_permitted = false;

    this.dropzone = document.querySelector('dropzone');
    this.return_hoist = document.querySelector('#album-return');
    this.album_fields_hoist = document.querySelector('#album-fields');
    this.hoist = document.querySelector('#images');
    this.image_count_hoist = document.querySelector('#images-count');
    this.image_elem = new ImageEditElem(this, this.hoist);
    this.delete_button = document.querySelector('#album-delete-button');
    this.hide_button = document.querySelector('#album-hide-button');
    this.show_button = document.querySelector('#album-show-button');

    this.archive_mimetypes = [
      'application/zip',
      'application/zip-compressed',
      'application/x-zip-compressed',
      'application/vnd.comicbook+zip'
    ];

    this.archive_extensions = [
      'zip',
      'cbz'
    ];

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
    const els = this.hoist.querySelectorAll(ImageEditElem.TagName);
    // reset album fields here?
    els.forEach(el => this.hoist.removeChild(el));
  }

  async load() {
    this.album_id = this.extract_id_from_hash(0);
    this.album = await this.api.albums.get_one(this.album_id);
    this.images = await this.api.images.get_all(this.album_id);

    this.update_return_button();
    this.album_fields_hoist.querySelector('#title').value = this.album.title;
    this.album_fields_hoist.querySelector('#author').value = this.album.author_alias.name;
    this.album_fields_hoist.querySelector('#description').value = this.album.description;
    this.album_fields_hoist.querySelector('#url').value = this.album.url;

    this.toggle_delete_button(this.album.disabled);
    this.toggle_toggle_buttons(this.album.disabled);
    this.load_images();

    this.image_count_hoist.classList.remove('collapse');
    this.update_page_title('Editing: ' + this.album.title);
    this.toggle_loading_spinner(false);
    this.toggle_show_content(true);
  }

  load_images() {
    let i = 0;
    this.images.forEach((image) => {
      const is_first = i === 0;
      const is_last = i === (this.images.length - 1);
      this.image_elem.update(image);

      if(!!this.album.cover && image.id === this.album.cover.id) {
        this.image_elem.set_current_cover(true);
      }
      this.image_elem.set_image_order_hints(is_first, is_last);
      this.image_elem.set_delete_enabled(this.image_deletes_permitted);
      this.image_elem.display();
      i++;
    }, this);

    this.image_count_hoist.innerText = this.images.length;
  }

  reload() {
    this.toggle_loading_spinner(true);
    this.toggle_show_content(false);

    this.flush();
    return this.load();
  }

  bind_event_handlers() {
    window.addEventListener('dragstart', (ev) => {
      return this.check_drag(ev);
    });
    window.addEventListener('dragenter', (ev) => {
      this.toggle_display_dropzone(true);
      return this.check_drag(ev);
    });
    this.dropzone.addEventListener('dragleave', (ev) => {
      this.toggle_display_dropzone(false);
    });
    this.dropzone.addEventListener('dragenter', (ev) => {
      return this.check_drag(ev);
    });
    this.dropzone.addEventListener('dragover', (ev) => {
      return this.check_drag(ev);
    });
    this.dropzone.addEventListener('drop', (ev) => {
      return this.handle_drop(ev);
    });

    this.album_fields_hoist.querySelector('button#save-fields').addEventListener('click', (ev) => {
      const title = this.album_fields_hoist.querySelector('#title');
      const author = this.album_fields_hoist.querySelector('#author');
      const description = this.album_fields_hoist.querySelector('#description');
      const url = this.album_fields_hoist.querySelector('#url');

      this.api.albums.update(this.album_id, title.value, author.value, description.value, url.value)
        .then((album) => {
          this.album = album;

          this.album_fields_hoist.querySelector('#title').value = this.album.title;
          this.album_fields_hoist.querySelector('#author').value = this.album.author_alias.name;
          this.album_fields_hoist.querySelector('#description').value = this.album.description;
          this.album_fields_hoist.querySelector('#url').value = this.album.url;
          this.update_page_title('Editing: ' + this.album.title);
        })
        .then(() => this.ui_toast('success', 'Album updated'))
        .catch((err) => {
          this.ui_toast('danger', format_error_msg(err));
          throw err;
        });

      ev.preventDefault();
    });

    document.querySelector('button#album-hide-button').addEventListener('click', (ev) => {
      this.api.albums.toggle(this.album_id, true)
        .then((album) => {
          this.album = album;

          this.toggle_delete_button(true);
          this.toggle_toggle_buttons(true);
        })
        .then(() => this.ui_toast('success', 'Album updated'))
        .catch((err) => {
          this.ui_toast('danger', format_error_msg(err));
          throw err;
        });

      ev.preventDefault();
    });
    document.querySelector('button#album-show-button').addEventListener('click', (ev) => {
      this.api.albums.toggle(this.album_id, false)
        .then((album) => {
          this.album = album;

          this.toggle_delete_button(false);
          this.toggle_toggle_buttons(false);
        })
        .then(() => this.ui_toast('success', 'Album updated'))
        .catch((err) => {
          this.ui_toast('danger', format_error_msg(err));
          throw err;
        });

      ev.preventDefault();
    });

    // document.querySelector('button#album-thumbnails-button').addEventListener('click', (ev) => {
    //   this.api.albums.regen_thumbnails(this.album_id)
    //     .then(() => { this.reload() })
    //     .then(() => this.ui_toast('success', 'Image thumbnails regenerated'))
    //     .catch((err) => {
    //       this.ui_toast('danger', format_error_msg(err));
    //       throw err;
    //     });

    //   ev.preventDefault();
    // });

    document.querySelector('button#album-delete-button').addEventListener('click', (ev) => {
      if (ev.target.classList.contains('disabled')) {
        ev.preventDefault();
        return;
      }

      this.api.albums.delete(this.album_id)
        .then(() => {
          this.update_return_button('/');
          this.toggle_show_content(false);
          this.toggle_display_404(true);
        })
        .then(() => this.ui_toast('success', 'Album deleted'))
        .catch((err) => {
          this.ui_toast('danger', format_error_msg(err));
          throw err;
        });

        ev.preventDefault();
    });

    document.querySelector('button#upload').addEventListener('click', (ev) => {
      const file = document.querySelector('input#file');
      if (!file.value) {
        return;
      }

      if (this.check_if_file_is_archive(file.files[0])) {
        // if it's a zip, we upload to the archive endpoint
        this.toggle_show_content(false);
        this.toggle_loading_spinner(true);
        this.api.images.upload_archive(this.album_id, file)
          .then(() => this.reload())
          .then(() => {
            file.value = '';
            this.ui_toast('success', 'Archive uploaded');
          })
          .catch((err) => {
            this.ui_toast('danger', format_error_msg(err));
            throw err;
          });
      } else {
        // assume it's an image
        this.api.images.create(this.album_id)
          .then((image) => {
            return this.api.images.upload(this.album_id, image.id, file)
              .catch((err) => {
                return this.api.images.delete(this.album_id, image.id).then(() => { throw err })
              })
          })
          .then(async () => {
            this.images = await this.api.images.get_all(this.album_id);
          })
          .then(() => {
            this.ui_toast('success', 'Image uploaded');
            file.value = '';
            this.flush();
            this.load_images();
          })
          .catch((err) => {
            this.ui_toast('danger', format_error_msg(err));
            throw err;
          });
      }

      ev.preventDefault();
    });

    this.hoist.addEventListener('click', (ev) => {
      if (ev.target.classList.contains('disabled')) {
        return;
      }

      if (ev.target.classList.contains('make-cover-btn')) {
        const image_id = ev.target.closest('minori-image-page').getAttribute('data-id');

        this.image_mark_cover_handler(image_id)
          .then(() => {
            this.flush();
            this.load_images();
          })
          .then(() => this.ui_toast('success', 'Image set as cover'))
          .catch((err) => {
            this.ui_toast('danger', format_error_msg(err));
            throw err;
          });

        ev.preventDefault();
      } else if (ev.target.classList.contains('move-up-btn')) {
        const image_id = ev.target.closest('minori-image-page').getAttribute('data-id');

        this.image_move_up_handler(image_id)
          .then(() => {
            this.flush();
            this.load_images();
          })
          .then(() => this.ui_toast('success', 'Image order updated'))
          .catch((err) => {
            this.ui_toast('danger', format_error_msg(err));
            throw err;
          });

        ev.preventDefault();
      } else if (ev.target.classList.contains('move-down-btn')) {
        const image_id = ev.target.closest('minori-image-page').getAttribute('data-id');

        this.image_move_down_handler(image_id)
          .then(() => {
            this.flush();
            this.load_images();
          })
          .then(() => this.ui_toast('success', 'Image order updated'))
          .catch((err) => {
            this.ui_toast('danger', format_error_msg(err));
            throw err;
          });

        ev.preventDefault();
      } else if (ev.target.classList.contains('delete-btn')) {
        const image_id = ev.target.closest('minori-image-page').getAttribute('data-id');

        this.image_delete_handler(image_id)
          .then(() => {
            this.flush();
            this.load_images();
          })
          .then(() => this.ui_toast('success', 'Image deleted'))
          .catch((err) => {
            this.ui_toast('danger', format_error_msg(err));
            throw err;
          });

        ev.preventDefault();
      }
    });

    document.querySelector('button#deletion-safety').addEventListener('click', (ev) => {
      const new_state = !this.image_deletes_permitted;
      ev.target.querySelector('span').innerText = new_state ? 'Disable image deletion' : 'Enable image deletion';
      ev.target.setAttribute('title', new_state ? 'Disable image deletion' : 'Enable image deletion');
      if (new_state) {
        ev.target.classList.remove('btn-warning');
        ev.target.classList.add('btn-danger');
      } else {
        ev.target.classList.add('btn-warning');
        ev.target.classList.remove('btn-danger');
      }

      this.image_deletes_permitted = !this.image_deletes_permitted;
      this.flush();
      this.load_images();
      ev.preventDefault();
    });

    document.querySelector('button#reload').addEventListener('click', (ev) => {
      this.reload();
      ev.preventDefault();
    });
  }

  check_if_file_is_archive(file) {
    if (file.type == '') {
      return this.archive_extensions.includes(file.name.split('.').pop());
    }

    return this.archive_mimetypes.includes(file.type);
  }

  update_return_button(dest = '') {
    if (!dest) {
      dest = `/album.html#${esc(this.album_id)}`;
    }
    this.return_hoist.querySelector('a').setAttribute('href', dest);
    this.return_hoist.classList.remove('collapse');
  }

  async image_mark_cover_handler(image_id) {
    await this.api.images.mark_as_cover(this.album_id, image_id);
    this.album = await this.api.albums.get_one(this.album_id);
    this.images = await this.api.images.get_all(this.album_id);
  }

  async image_move_up_handler(image_id) {
    // check to see if we need to bake in the order first
    const needs_baked = this.images.some((image) => image.album_order_key === 0);
    if (needs_baked) {
      await this.bake_in_image_order();
      this.images = await this.api.images.get_all(this.album_id);
    }

    let prior_image = null;
    let image = null;
    for (const i in this.images) {
      image = this.images[i];

      if (image_id === image.id) {
        break;
      }
      prior_image = image;
    }

    if (prior_image === null) {
      throw new Error('Image cannot be moved up any further.')
    }

    const old_album_order_key = image.album_order_key;
    const new_album_order_key = prior_image.album_order_key;

    await this.api.images.update_order(this.album_id, image.id, new_album_order_key);
    await this.api.images.update_order(this.album_id, prior_image.id, old_album_order_key);
    this.images = await this.api.images.get_all(this.album_id);
  }

  async image_move_down_handler(image_id) {
    // check to see if we need to bake in the order first
    const needs_baked = this.images.some((image) => image.album_order_key === 0);
    if (needs_baked) {
      await this.bake_in_image_order();
      this.images = await this.api.images.get_all(this.album_id);
    }

    let found_image = null;
    let next_image = null;
    for (const i in this.images) {
      let image = this.images[i];

      if (found_image !== null) {
        next_image = image;
        break;
      }

      if (image_id === image.id) {
        found_image = image;
      }
    }

    if (next_image === null) {
      throw new Error('Image cannot be moved down any further.')
    }
    const image = found_image;

    const old_album_order_key = image.album_order_key;
    const new_album_order_key = next_image.album_order_key;

    await this.api.images.update_order(this.album_id, image.id, new_album_order_key);
    await this.api.images.update_order(this.album_id, next_image.id, old_album_order_key);
    this.images = await this.api.images.get_all(this.album_id);
  }

  async image_delete_handler(image_id) {
    await this.api.images.delete(this.album_id, image_id);
    this.images = await this.api.images.get_all(this.album_id);
  }

  async bake_in_image_order() {
    try {
      for (const i in this.images) {
        const image = this.images[i];
        await this.api.images.update_order(this.album_id, image.id, Number(i)+1);
      }
    } catch(err) {
      this.ui_toast('danger', format_error_msg(err));
      throw err;
    }
  }

  toggle_display_dropzone(visible = true) {
    if(visible === true) {
      this.dropzone.classList.remove('collapse');
    } else {
      this.dropzone.classList.add('collapse');
    }
  }


  check_drag(ev) {
    if (ev?.dataTransfer?.types?.includes('Files')) {
      ev.dataTransfer.dropEffect = 'copy';
      ev.dataTransfer.effectAllowed = 'copy';

      ev.preventDefault();
      return false;
    }
  }

  handle_drop(ev) {
    const dt = new DataTransfer();
    dt.items.add(ev.dataTransfer.files[0]);
    document.querySelector('#file').files = dt.files;

    this.toggle_display_dropzone(false);

    ev.preventDefault();
    return false;
  }

  toggle_delete_button(enabled = false) {
    if(enabled === true) {
      this.delete_button.classList.remove('disabled');
    } else {
      this.delete_button.classList.add('disabled');
    }
  }

  toggle_toggle_buttons(disabled = false) {
    if(disabled === true) {
      this.hide_button.classList.add('collapse');
      this.show_button.classList.remove('collapse');
    } else {
      this.hide_button.classList.remove('collapse');
      this.show_button.classList.add('collapse');
    }
  }
}

export { MinoriEditAlbumUI };
