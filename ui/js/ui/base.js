import { MinoriAPI } from '../api.js';

class MinoriUI {
  constructor() {
    this.api = new MinoriAPI();
    this.image_base_url = '';
    this.allow_maint_mode = false;

    this.maint_mode = false;

    this.alerts_selector = document.querySelector('div.toast-container');
  }

  config_url() {
    return '/.ui/config.json';
  }

  async load_config() {
    const resp = await fetch(this.config_url());

    if(!resp.ok) {
      throw new Error('Failed to load UI config');
    }

    const config = await resp.json();
    this.api.set_api_url(config.api_url);
    this.image_base_url = config.image_base_url;
    this.allow_maint_mode = config.allow_maint_mode ?? false;

    this.toggle_maint_mode(false);
  }

  toggle_maint_mode(enabled = null) {
    if(!this.allow_maint_mode) {
      enabled = false;
    } else if(enabled === null) {
      enabled = !this.maint_mode;
    }

    this.maint_mode = !!enabled;
    document.querySelector('body').setAttribute('data-maint-mode', this.maint_mode.toString());
  }

  toast_tpl(type, message) {
    if (!['danger', 'warning', 'success', 'primary', 'secondary', 'info'].includes(type)) {
      throw new Error('Invalid alert type specified for alert template.');
    }

    let icon = '';
    if (type === 'danger' || type === 'warning') {
      icon = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-exclamation-circle" viewBox="0 0 20 20">
          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
          <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
        </svg>
      `;
    } else {
      icon = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 20 20">
          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
          <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/>
        </svg>
      `;
    }

    return `
      <div class="toast align-items-center my-1" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-indicator text-${type} rounded ms-3 align-self-center">${icon}</div>
          <div class="toast-body">
            ${message}
          </div>
          <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>
    `;
  }

  ui_toast(type, message) {
    const el = document.createElement('div');
    this.alerts_selector.append(el);
    el.innerHTML = this.toast_tpl(type, message);

    const toast = new bootstrap.Toast(el.querySelector('div.toast'), { autohide: true, delay: 7000, animation: true });
    toast.show();

    setTimeout(() => {
      this.alerts_selector.removeChild(el);
    }, 10 * 1000);
  }

  extract_id_from_hash(index) {
    const ids = window.location.hash.substring(1).split(':');
    if(index >= ids.length) {
      return false;
    }
    return ids[index];
  }

  toggle_loading_spinner(visible = false) {
    if(visible === true) {
      document.querySelector('#pending-load-spinner').classList.remove('collapse');
    } else {
      document.querySelector('#pending-load-spinner').classList.add('collapse');
    }
  }

  toggle_show_content(visible = false) {
    if(visible === true) {
      document.querySelector('#wrapper').classList.remove('pending-load');
    } else {
      document.querySelector('#wrapper').classList.add('pending-load');
    }
  }

  toggle_display_404(visible = true) {
    if(visible === true) {
      document.querySelector('#content-missing-msg').classList.remove('collapse');
    } else {
      document.querySelector('#content-missing-msg').classList.add('collapse');
    }
  }

  update_page_title(blurb = '') {
    document.querySelector('title').innerText = `minori${ blurb ? ' - ' + blurb : ''}`;
  }
}

export { MinoriUI };
