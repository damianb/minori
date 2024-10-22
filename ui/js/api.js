import { MinoriBaseAPI } from './api/base.js';
import { MinoriAlbumsAPI } from './api/albums.js';
import { MinoriImagesAPI } from './api/images.js';
import { MinoriAuthorsAPI } from './api/authors.js';
import { MinoriAuthorAliasesAPI } from './api/authoraliases.js';

class MinoriAPI {
  constructor() {
    this.apis = {
      'base': new MinoriBaseAPI(),
      'albums': new MinoriAlbumsAPI(),
      'images': new MinoriImagesAPI(),
      'authors': new MinoriAuthorsAPI(),
      'authoraliases': new MinoriAuthorAliasesAPI(),
    }
  }

  set_api_url(api_url) {
    return this.base.set_api_url(api_url);
  }

  get base() {
    return this.apis['base'];
  }

  get albums() {
    return this.apis['albums'];
  }

  get images() {
    return this.apis['images'];
  }

  get authors() {
    return this.apis['authors'];
  }

  get authoraliases() {
    return this.apis['authoraliases'];
  }
}

export { MinoriAPI };
