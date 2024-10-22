import { esc } from "./common.js";

class UIElement {
  constructor(tag, ui, parent, data) {
    this.ui = ui;
    this.tag = tag;
    this.parent = parent;
    this.data = null;
    if(data) {
      this.update(data);
    }
  }

  update(data) {
    this.data = data;
  }

  get_parent() {
    return this.parent;
  }

  get_element() {
    return this.get_parent().querySelector(`${this.tag}[data-id='${this.data.id}']`);
  }

  display() {
    let el = this.get_element();
    if (el === null) {
      el = document.createElement(this.tag);
      this.get_parent().append(el);
    }

    el.outerHTML = this.render();
  }

  destroy() {
    if(this.data === null) {
      return;
    }

    const el = this.get_element();
    this.get_parent().removeChild(el);
  }

  lifecycle(data, destroy = false) {
    if (destroy) {
      this.destroy();
    }
    this.update(data);
    this.display();
  }

  render() {
    return `<${this.tag}><p>No render defined for UIElement.</p></${this.tag}>`;
  }
}

class ImageElem extends UIElement {
  static TagName = 'minori-image';
  constructor(ui, parent, data) {
    super(ImageElem.TagName, ui, parent, data);
  }

  image_url() {
    return `${this.ui.image_base_url}/images/${this.data.filename}`;
  }

  thumbnail_url() {
    return `${this.ui.image_base_url}/thumbs/${this.data.filename}`;
  }

  view_url() {
    return `/view.html#${esc(this.ui.extract_id_from_hash(0))}:${esc(this.data.id)}`;
  }

  static missing_image_svg() {
    return `
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 350 500'>
      <style>.t { font: bold 40px sans-serif; }</style>
      <text x='75' y='234' class='t'>NO IMAGE</text>
      <text x='105' y='280' class='t'>FOUND</text>
    </svg>`.replace('<', '%3c').replace('>', '%3e').replace('\n', '');
  }

  static render_image_missing_placeholder(extra_classes = '') {
    return `<img src="data:image/svg+xml,${ImageElem.missing_image_svg()}" class="missing-image ${extra_classes}" alt="No image found">`;
  }

  render_thumbnail(extra_classes = '') {
    return `<a href="${this.view_url()}"><img src="${this.thumbnail_url()}" class="album-image ${extra_classes}" alt="Album image" /></a>`;
  }

  render() {
    const image = this.data.uploaded ? this.render_thumbnail('rounded-3 img-thumbnail img-fluid') : ImageElem.render_image_missing_placeholder('rounded-3 img-thumbnail img-fluid');
    return `
    <${this.tag} data-id="${this.data.id}">
      <div class="col">
        ${image}
      </div>
    </${this.tag}>`;
  }
}

class FullImageElem extends ImageElem {
  static TagName = 'minori-image-page';
  constructor(ui, parent, data) {
    super(ui, parent, data);
    this.tag = FullImageElem.TagName;
  }

  render() {
    return `
    <${this.tag} data-id="${this.data.id}">
      <img src="${this.image_url()}" class="album-image" alt="Album image">
    </${this.tag}>`;
  }
}

class ImageCoverElem extends ImageElem {
  static TagName = 'minori-cover-image';
  constructor(ui, album, image) {
    super(ui, album, image);
    this.tag = ImageCoverElem.TagName;
  }

  get_parent() {
    return this.parent.get_element();
  }

  render(extra_classes = '') {
    return `
    <${this.tag} data-id="${this.data.id}">
      <img src="${this.thumbnail_url()}" class="album-cover ${extra_classes}" alt="Cover image">
    </${this.tag}>`;
  }
}

class ImageEditElem extends ImageElem {
  static TagName = 'minori-image-page';
  constructor(ui, parent, data) {
    super(ui, parent, data);
    this.tag = ImageEditElem.TagName;
    this.set_current_cover();
    this.set_image_order_hints();
    this.set_delete_enabled();
  }

  update(data) {
    super.update(data);
    this.set_current_cover();
    this.set_image_order_hints();
    this.set_delete_enabled();
  }

  set_delete_enabled(enabled = false) {
    this.delete_enabled = enabled;
  }

  set_image_order_hints(is_first = false, is_last = false) {
    this.is_first = is_first;
    this.is_last = is_last;
  }

  set_current_cover(is_cover = false) {
    this.is_cover = is_cover;
  }

  render_cover_svg() {
    return `
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-journal-bookmark-fill" viewBox="0 0 16 16">
      <path fill-rule="evenodd" d="M6 1h6v7a.5.5 0 0 1-.757.429L9 7.083 6.757 8.43A.5.5 0 0 1 6 8z"/>
      <path d="M3 0h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2v-1h1v1a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v1H1V2a2 2 0 0 1 2-2"/>
      <path d="M1 5v-.5a.5.5 0 0 1 1 0V5h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1zm0 3v-.5a.5.5 0 0 1 1 0V8h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1zm0 3v-.5a.5.5 0 0 1 1 0v.5h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1z"/>
    </svg>`;
  }

  render_up_svg() {
    return `
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-up" viewBox="0 0 16 16">
      <path fill-rule="evenodd" d="M8 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L7.5 2.707V14.5a.5.5 0 0 0 .5.5"/>
    </svg>`;
  }

  render_down_svg() {
    return `
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-down" viewBox="0 0 16 16">
      <path fill-rule="evenodd" d="M8 1a.5.5 0 0 1 .5.5v11.793l3.146-3.147a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 .708-.708L7.5 13.293V1.5A.5.5 0 0 1 8 1"/>
    </svg>`;
  }

  render_trash_svg() {
    return `
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
      <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
      <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
    </svg>`;
  }

  render() {
    const image = this.data.uploaded ? this.render_thumbnail('rounded') : this.render_image_missing_placeholder('rounded');

    return `
    <${this.tag} class="col" data-id="${this.data.id}">
      <div class="card h-100 border-0">
        ${image}
        <div class="card-body p-0"></div>
        <div class="card-footer pt-2 pb-0 px-0 border-0">
          <div class="d-flex justify-content-center">
            <div class="btn-toolbar image-controls">
              <div class="btn-group btn-group-sm" role="group">
                <button type="button" class="btn make-cover-btn capture btn-${ this.is_cover ? 'primary disabled' : 'secondary'}" title="Make cover">${this.render_cover_svg()}</button>
              </div>
              <div class="btn-group btn-group-sm ms-1" role="group">
                <button type="button" class="btn move-up-btn capture btn-secondary ${ this.is_first ? 'disabled' : '' }" title="Move up">${this.render_up_svg()}</button>
                <button type="button" class="btn move-down-btn capture btn-secondary ${ this.is_last ? 'disabled' : '' }" title="Move down">${this.render_down_svg()}</button>
              </div>

              <div class="btn-group btn-group-sm ms-1" role="group">
                <button type="button" class="btn delete-btn capture btn-danger ${ !this.delete_enabled ? 'disabled' : '' }" title="Delete image">${this.render_trash_svg()}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </${this.tag}>`;
  }
}

class AlbumListElem extends UIElement {
  static TagName = 'a.minori-album-list-entry';
  constructor(ui, parent, data ) {
    super(AlbumListElem.TagName, ui, parent, data);
  }

  album_url() {
    return `/album.html#${esc(this.data.id)}`;
  }

  author_url() {
    return `/author.html#${esc(this.data.author_alias.author.id)}`;
  }

  render_author() {
    if (!this.data.author_alias) {
      return '';
    }

    if (this.data.author_alias.name !== this.data.author_alias.author.name) {
      return `<span class="text-muted smalltext fw-light">by <span class="has-author-alias" title="a.k.a. ${esc(this.data.author_alias.author.name)}">${esc(this.data.author_alias.name)}</span></span>`;
    }

    return `<span class="text-muted smalltext fw-light">by ${esc(this.data.author_alias.name)}</span>`;
  }

  render() {
    return `
    <a href="${this.album_url()}" class="${this.tag.split('.')[1]} list-group-item list-group-item-action album-${esc(this.data.state())} ${this.data.is_new() ? 'album-new' : ''}" data-id="${esc(this.data.id)}" data-disabled="${this.data.disabled.toString()}">
      <span class="album-title">${esc(this.data.title)}</span>&nbsp;${this.render_author()}
    </a>`;
  }

}

class AuthorListElem extends UIElement {
  static TagName = 'a.minori-author-list-entry';
  constructor(ui, parent, data ) {
    super(AuthorListElem.TagName, ui, parent, data);
  }

  author_url() {
    return `/author.html#${esc(this.data.id)}`;
  }

  render() {
    return `
    <a href="${this.author_url()}" class="${this.tag.split('.')[1]} list-group-item list-group-item-action" data-id="${esc(this.data.id)}">
      <span>${esc(this.data.name)}</span></span>
    </a>`;
  }
}

class AuthorAliasListElem extends UIElement {
  static TagName = 'a.minori-authoralias-list-entry';
  constructor(ui, parent, data ) {
    super(AuthorAliasListElem.TagName, ui, parent, data);
  }

  authoralias_url() {
    return `/authoralias.html#${esc(this.data.id)}`;
  }

  render() {
    return `
    <a href="${this.authoralias_url()}" class="${this.tag.split('.')[1]} list-group-item list-group-item-action" data-id="${esc(this.data.id)}">
      <span>${esc(this.data.name)}</span></span>
    </a>`;
  }
}

class AlbumElem extends UIElement {
  static TagName = 'minori-album';
  constructor(ui, parent, data) {
    super(AlbumElem.TagName, ui, parent, data);
  }

  update(data) {
    super.update(data);
    this.cover = data.cover ? new ImageCoverElem(this.ui, this, data.cover) : null;
  }

  album_url() {
    return `/album.html#${esc(this.data.id)}`;
  }

  album_edit_url() {
    return `/edit.html#${esc(this.data.id)}`;
  }

  render() {
    const cover = this.cover ? this.cover.render('card-img-top') : ImageElem.render_image_missing_placeholder('card-img-top no-cover');

    return `
    <${this.tag} class="album-${esc(this.data.state())} ${this.data.is_new() ? 'album-new' : ''}" data-id="${esc(this.data.id)}" data-disabled="${this.data.disabled.toString()}">
      <div class="col">
        <div class="card">
          <a href="${this.album_url()}">${cover}</a>
          <div class="card-body px-3 py-2">
            <p class="card-text album-title">${esc(this.data.title)}</p>
          </div>
        </div>
      </div>
    </${this.tag}>`;
  }
}

class AlbumMetadataElem extends AlbumElem {
  view_url() {
    return `/view.html#${esc(this.data.id)}`;
  }

  author_url() {
    return `/author.html#${esc(this.data.author_alias.author.id)}`;
  }

  render_author() {
    if (!this.data.author_alias) {
      return '';
    }

    if (this.data.author_alias.name !== this.data.author_alias.author.name) {
      return `<span class="text-muted smalltext fw-light">by <a class="has-author-alias" title="a.k.a. ${esc(this.data.author_alias.author.name)}" href="${esc(this.author_url())}">${esc(this.data.author_alias.name)}</a></span>`;
    }

    return `<span class="text-muted smalltext fw-light">by <a href="${esc(this.author_url())}">${esc(this.data.author_alias.name)}</a></span>`;
  }

  render_source() {
    if(!this.data.url) {
      return '';
    }

    return `<p class="card-text"><a href="${esc(this.data.url)}">Original source</a></p>`;
  }

  render() {
    const cover = this.cover ? this.cover.render('card-img-top album-card-rounding') : ImageElem.render_image_missing_placeholder('card-img-top album-card-rounding');

    return `
    <${this.tag} class="card mb-3 col-8 col-sm-12 col-md-11 col-lg-7 album-${esc(this.data.state())} ${this.data.is_new() ? 'album-new' : ''}" data-id="${this.data.id}">
      <div class="row g-0">
        <div class="col-sm-3">
          <a href="${this.view_url()}">${cover}</a>
        </div>
        <div class="col-sm-9">
          <div class="card-body p-2point5">
            <h3 class="card-title text-end album-title">${esc(this.data.title)}</h3>
            <p class="card-text text-end mb-0">${this.render_author()}</p>
            <p class="card-text lh-sm smalltext mt-2 mb-0 ${ this.data.description == '' ? 'collapse' : '' } text-justify text-sm-start">${esc(this.data.description)}</p>
            <!--${this.render_source()}-->
          </div>
        </div>
      </div>
    </${this.tag}>
    `;
  }
}

class AuthorMetadataElem extends UIElement {
  static TagName = 'minori-author';
  constructor(ui, parent, data) {
    super(AuthorMetadataElem.TagName, ui, parent, data);
  }

  update(data) {
    super.update(data);
  }

  render() {
    return `
    <${this.tag} data-id="${esc(this.data.id)}">
      <h3>author: <span id="author-name">${esc(this.data.name)}</span></h3>
    </${this.tag}>`;
  }
}

class PaginationElem extends UIElement {
  static TagName = 'minori-pagination';
  constructor(ui, parent, data) {
    super(PaginationElem.TagName, ui, parent, data);

    this.svg_width = 18;
    this.svg_height = 18;
  }

  get_element() {
    return this.get_parent().querySelector(`${this.tag}`);
  }

  get_current_page() {
    return 0;
  }

  get_total_pages() {
    return 0;
  }

  first_page_url() {
    // stub method
    return false;
  }

  previous_page_url() {
    // stub method
    return false;
  }

  current_page_url() {
    // stub method
    return false;
  }

  next_page_url() {
    // stub method
    return false;
  }

  last_page_url() {
    // stub method
    return false;
  }

  render_first_page_link() {
    const link_url = this.first_page_url();
    const disabled = link_url === false;

    return `
    <li class="page-item ${disabled ? 'disabled' : ''}">
      <a class="page-link capture nav-first" href="${link_url ?? '#'}" ${disabled ? 'tabindex="-1" aria-disabled="true"' : ''} aria-label="First" title="First">
        <svg xmlns="http://www.w3.org/2000/svg" width="${this.svg_width}" height="${this.svg_height}" fill="currentColor" class="bi bi-chevron-bar-left" viewBox="0 0 16 16" aria-hidden="true">
          <title>First image</title>
          <path fill-rule="evenodd" d="M11.854 3.646a.5.5 0 0 1 0 .708L8.207 8l3.647 3.646a.5.5 0 0 1-.708.708l-4-4a.5.5 0 0 1 0-.708l4-4a.5.5 0 0 1 .708 0M4.5 1a.5.5 0 0 0-.5.5v13a.5.5 0 0 0 1 0v-13a.5.5 0 0 0-.5-.5"/>
        </svg>
      </a>
    </li>`;
  }

  render_previous_page_link() {
    const link_url = this.previous_page_url();
    const disabled = link_url === false;

    return `
    <li class="page-item ${disabled ? 'disabled' : ''}">
      <a class="page-link capture nav-prev" href="${link_url ?? '#'}" ${disabled ? 'tabindex="-1" aria-disabled="true"' : ''} aria-label="Previous" title="Previous">
        <svg xmlns="http://www.w3.org/2000/svg" width="${this.svg_width}" height="${this.svg_height}" fill="currentColor" class="bi bi-chevron-left" viewBox="0 0 16 16" aria-hidden="true">
          <path fill-rule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0"/>
        </svg>
      </a>
    </li>`;
  }

  render_current_page_link() {
    const link_url = this.current_page_url();
    const disabled = link_url === false;

    return `
    <li class="page-item ${disabled ? 'disabled' : ''}">
      <a class="page-link nav-focus" href="${link_url ?? '#'}" ${disabled ? 'tabindex="-1" aria-disabled="true"' : ''}>${this.get_current_page()} / ${this.get_total_pages()}</a>
    </li>`;
  }

  render_next_page_link() {
    const link_url = this.next_page_url();
    const disabled = link_url === false;

    return `
    <li class="page-item ${disabled ? 'disabled' : ''}">
      <a class="page-link capture nav-next" href="${link_url ?? '#'}" ${disabled ? 'tabindex="-1" aria-disabled="true"' : ''} aria-label="Next" title="Next">
        <svg xmlns="http://www.w3.org/2000/svg" width="${this.svg_width}" height="${this.svg_height}" fill="currentColor" class="bi bi-chevron-right" viewBox="0 0 16 16" aria-hidden="true">
          <path fill-rule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708"/>
        </svg>
      </a>
    </li>`;
  }

  render_last_page_link() {
    const link_url = this.last_page_url();
    const disabled = link_url === false;

    return `
    <li class="page-item ${disabled ? 'disabled' : ''}">
      <a class="page-link capture nav-last" href="${link_url ?? '#'}" ${disabled ? 'tabindex="-1" aria-disabled="true"' : ''} aria-label="Last" title="Last">
        <svg xmlns="http://www.w3.org/2000/svg" width="${this.svg_width}" height="${this.svg_height}" fill="currentColor" class="bi bi-chevron-bar-right" viewBox="0 0 16 16" aria-hidden="true">
          <path fill-rule="evenodd" d="M4.146 3.646a.5.5 0 0 0 0 .708L7.793 8l-3.647 3.646a.5.5 0 0 0 .708.708l4-4a.5.5 0 0 0 0-.708l-4-4a.5.5 0 0 0-.708 0M11.5 1a.5.5 0 0 1 .5.5v13a.5.5 0 0 1-1 0v-13a.5.5 0 0 1 .5-.5"/>
        </svg>
      </a>
    </li>`;
  }

  render() {
    return `
    <${this.tag}>
      <ul class="pagination pagination-lg justify-content-center mb-0">
        ${this.render_first_page_link()}
        ${this.render_previous_page_link()}
        ${this.render_current_page_link()}
        ${this.render_next_page_link()}
        ${this.render_last_page_link()}
      </ul>
    </${this.tag}>
    `;
  }
}

class AlbumPaginationElem extends PaginationElem {
  page_url(page) {
    return `/#${esc(page)}`;
  }

  get_current_page() {
    return this.data.current_page;
  }

  get_total_pages() {
    return this.data.last_page;
  }

  first_page_url() {
    return (this.data.first_page !== this.data.current_page) ? this.page_url(this.data.first_page) : false;
  }

  previous_page_url() {
    return this.data.previous_page !== false ? this.page_url(this.data.previous_page) : false;
  }

  current_page_url() {
    return '/list.html';
  }

  next_page_url() {
    return this.data.next_page !== false ? this.page_url(this.data.next_page) : false;
  }

  last_page_url() {
    return (this.data.last_page !== this.data.current_page) ? this.page_url(this.data.last_page) : false;
  }
}

class ImagePaginationElem extends PaginationElem {
  get_current_page() {
    return this.data.current_page;
  }

  get_total_pages() {
    return this.data.total_pages;
  }

  album_url() {
    return `/album.html#${esc(this.data.album_id)}`;
  }

  view_url(image_id) {
    return `/view.html#${esc(this.data.album_id)}:${esc(image_id)}`;
  }

  image_url(filename) {
    return `${this.ui.image_base_url}/images/${filename}`;
  }

  first_page_url() {
    return this.data.first_id !== false ? this.view_url(this.data.first_id) : false;
  }

  previous_page_url() {
    return this.data.previous_id !== false ? this.view_url(this.data.previous_id) : false;
  }

  current_page_url() {
    return this.image_url(this.data.full_image_uri);
  }

  next_page_url() {
    return this.data.next_id !== false ? this.view_url(this.data.next_id) : false;
  }

  last_page_url() {
    return this.data.last_id !== false ? this.view_url(this.data.last_id) : false;
  }

  render_current_page_link() {
    const link_url = this.current_page_url();
    const disabled = link_url === false;

    return `
    <li class="page-item">
      <a class="page-link nav-focus" href="${link_url ?? '#'}" ${disabled ? 'tabindex="-1" aria-disabled="true"' : ''} target="_blank" title="Open image in new tab">${this.get_current_page()} / ${this.get_total_pages()}</a>
    </li>`;
  }
}

class AuthorPaginationElem extends PaginationElem {
  page_url(page) {
    return `/authors.html#${esc(page)}`;
  }

  get_current_page() {
    return this.data.current_page;
  }

  get_total_pages() {
    return this.data.last_page;
  }

  first_page_url() {
    return (this.data.first_page !== this.data.current_page) ? this.page_url(this.data.first_page) : false;
  }

  previous_page_url() {
    return this.data.previous_page !== false ? this.page_url(this.data.previous_page) : false;
  }

  current_page_url() {
    return false;
  }

  next_page_url() {
    return this.data.next_page !== false ? this.page_url(this.data.next_page) : false;
  }

  last_page_url() {
    return (this.data.last_page !== this.data.current_page) ? this.page_url(this.data.last_page) : false;
  }
}

export {
  UIElement,
  ImageElem,
  FullImageElem,
  ImageCoverElem,
  ImageEditElem,
  AlbumElem,
  AlbumListElem,
  AuthorListElem,
  AuthorAliasListElem,
  AuthorMetadataElem,
  AlbumMetadataElem,
  ImagePaginationElem,
  AlbumPaginationElem,
  AuthorPaginationElem
};
