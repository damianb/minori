class Image {
  constructor ({ id, filename, original_filename, uploaded, created_at, uploaded_at, album_order_key }) {
    this.id = id;
    this.filename = filename;
    this.original_filename = original_filename;
    this.uploaded = uploaded;
    this.album_order_key = album_order_key;

    this.created_at = created_at;
    this.uploaded_at = uploaded_at;

    this.create_date = new Date(created_at);
    this.upload_date = uploaded_at !== null ? new Date(uploaded_at) : null;
  }

  is_new() {
    // check if this was created within the last hour
    return (Date.now() - (1 * 60 * 60 * 1000)) < this.create_date.getTime();
  }
}

class Tag {
  constructor ({ id, namespace, name, description }) {
    this.id = id;
    this.namespace = namespace;
    this.name = name;
    this.description = description;
  }
}

class Author {
  constructor ({ id, name }) {
    this.id = id;
    this.name = name;
  }
}

class AuthorAlias {
  constructor ({ id, name }) {
    this.id = id;
    this.name = name;
  }
}

class FullAuthorAlias extends AuthorAlias {
  constructor ({ id, name, author }) {
    super(arguments[0]);

    this.author = author ? new Author(author) : null;
  }
}

class FullAuthor extends Author {
  constructor({ id, name, author_aliases }) {
    super(arguments[0]);

    this.author_aliases = (author_aliases || []).map(_author_alias => new AuthorAlias(_author_alias));
  }
}

class BaseAlbum {
  constructor ({ id, disabled, title, description, url, created_at }) {
    this.id = id;
    this.disabled = disabled;
    this.title = title;
    this.description = description;
    this.url = url;

    this.created_at = created_at;

    this.create_date = new Date(created_at);
  }

  state() {
    return this.disabled ? 'disabled' : 'active';
  }

  is_new() {
    // check if this was created within the last 3 days
    return (Date.now() - (3 * 24 * 60 * 60 * 1000)) < this.create_date.getTime();
  }
}

class Album extends BaseAlbum {
  constructor ({ id, disabled, title, description, url, created_at, author_alias }) {
    super(arguments[0]);

    this.author_alias = author_alias ? new FullAuthorAlias(author_alias) : null;
  }
}

class FullAlbum extends BaseAlbum {
  constructor ({ id, disabled, title, description, url, created_at, cover, tags, author_alias }) {
    super(arguments[0]);

    this.cover = cover ? new Image(cover) : null;
    this.tags = (tags || []).map(_tag => new Tag(_tag));

    this.author_alias = author_alias ? new FullAuthorAlias(author_alias) : null;
  }
}

class Pagination {
  constructor({ first_page, previous_page, current_page, next_page, last_page, total_records }) {
    this.first_page = first_page;
    this.previous_page = previous_page;
    this.current_page = current_page;
    this.next_page = next_page;
    this.last_page = last_page;

    this.total_records = total_records;
  }
}

export {
  Album,
  FullAlbum,
  Author,
  AuthorAlias,
  FullAuthorAlias,
  FullAuthor,
  Image,
  Pagination,
  Tag
};
