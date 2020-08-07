{% load static %}

window.done_moving_fake_mouse = false;

function int_to_px(i) {
  return i + 'px';
}

function px_to_int(px) {
  return parseInt(px.replace('px', ''));
}

function move_mouse(x, y) {
  var mouse = get_mouse();
  var frame = function() {
    var mtop = px_to_int(mouse.css('top'));
    var mleft = px_to_int(mouse.css('left'));
    if (mtop == y && mleft == x) {
      window.done_moving_fake_mouse = true;
      clearInterval(window.move_mouse_id);
    } else {
      window.done_moving_fake_mouse = false;
      if (mtop > y) {
        mtop -= Math.min({{ step }}, mtop - y);
      } else if (mtop < y) {
        mtop += Math.min({{ step }}, y - mtop);
      }
      if (mleft > x) {
        mleft -= Math.min({{ step }}, mleft - x);
      } else if (mleft < x) {
        mleft += Math.min({{ step }}, x - mleft);
      }
      mouse.css('top', int_to_px(mtop));
      mouse.css('left', int_to_px(mleft));
    }
  };

  if (window.move_mouse_id) {
    clearInterval(window.move_mouse_id);
  }
  window.move_mouse_id = setInterval(frame, 5);
}

function get_mouse() {
  if (!window.fake_mouse) {
    var mouse_src = '{% static "cursor.png" %}';
    window.fake_mouse = $('<img>').attr('src', mouse_src).appendTo($('body'));
    window.fake_mouse.css('position', 'absolute').css('top', 0).css('left', 0);
  }
  return window.fake_mouse;
}

move_mouse({{ x }}, {{ y }});
