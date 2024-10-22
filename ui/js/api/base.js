class MinoriAPIConfig {
  constructor() {
    if (MinoriAPIConfig._instance) {
      throw new Error('Attempted to reinstantiate a singleton class.')
    }
    MinoriAPIConfig._instance = this;

    this.api_url = '';
  }

  set_api_url(api_url) {
    this.api_url = api_url;
  }
}
const api_config = new MinoriAPIConfig();

class MinoriBaseAPI {
  set_api_url(api_url) {
    return api_config.set_api_url(api_url);
  }

  build_url(url = '/', qs = null) {
    const base_url = '/api/';
    let suffix = '';
    if(qs) {
      suffix = '?' + this.build_qs(qs);
    }

    return `${api_config.api_url}${base_url}${url.replace(/^\/+/, '')}${suffix}`;
  }

  build_qs(args) {
    return Object.entries(args).map(([k, v]) => `${k}=${v}`).join('&');
  }
}

export { MinoriBaseAPI };
