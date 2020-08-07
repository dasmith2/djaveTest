// Press ` to pause and unpause the web_test, which is really handy when you're
// tweaking the wording.
function pause_web_test() {
  var paused_div = $('<div id="paused">Paused</div>').appendTo($('body'));
  paused_div.css({
      'border': '1px solid', 'display': 'inline-block', 'padding': '5px',
      'position': 'absolute', 'bottom': 5, 'left': 5});
  paused_div.click(un_pause_web_test)
  // The web test uses Selenium to look for this variable.
  window.un_pause = false;
}

function un_pause_web_test() {
  $('#paused').remove();
  window.un_pause = true;
}

document.addEventListener('keyup', (e) => {
  if (e.key == '`') {
    if (window.un_pause === false) {
      un_pause_web_test();
    } else {
      pause_web_test();
    }
  }
});
