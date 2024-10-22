const timeformat = new Intl.RelativeTimeFormat('en', {
  style: 'narrow',
  numeric: 'auto'
});

function days_between(one, another) {
  // witchcraft.gif
  return Math.round(Math.abs((+one) - (+another))/8.64e7);
}

function esc(content) {
  let p = document.createElement('p');
  p.textContent = content;
  return p.innerHTML;
}

async function build_error(resp, message) {
  const res = await resp.json();
  const msg = message + ' - ' + (res.error || ((res.detail || [])[0] || {})['msg'] || 'Unknown error');
  const err = new Error(msg);
  err.status = resp.status;

  return err;
}

function format_error_msg(err) {
  return err.toString().replace(/^(Error\: )/, '');
}

function isTouchDevice() {
  return (('ontouchstart' in window)); // || (navigator.maxTouchPoints > 0) || (navigator.msMaxTouchPoints > 0));
}

export { timeformat, days_between, esc, build_error, format_error_msg, isTouchDevice };
