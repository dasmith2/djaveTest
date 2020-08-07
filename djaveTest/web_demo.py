from random import choice
import time

from djaveTest.web_test import WebTest
from django.template.loader import render_to_string


class WebDemo(WebTest):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.transcript = []
    self.go_slow()

  def warm_up(self):
    self.go_to_first_view()

    if self._go_slow:
      self.say('Warming up blah blah blah')
      seconds = input(
          'Start after seconds delay, or leave blank to start immediately: ')
      try:
        for i in reversed(range(int(seconds))):
          time.sleep(1)
          print(i)
      except ValueError:
        pass

  def go_to_first_view(self):
    self.go_to_view(self.first_view())

  def first_url(self):
    return 'djave_sign_up'

  def go_fast(self):
    self._go_slow = False

  def go_slow(self):
    self._go_slow = True

  def execute_script(self, script, *args):
    from selenium.common.exceptions import JavascriptException
    try:
      return self.driver.execute_script(script, *args)
    except JavascriptException as ex:
      if self.on_error_screen():
        raise Exception('Server error.')
      raise ex

  def say(self, message, wait=False):
    self.transcript.append(message)
    if self._go_slow:
      # Literally cause the browser to say the message out loud in a Stephen
      # Hawking voice. You have to use ’ instead of ' otherwise Stephen
      # literally spells out the unicode.
      message_safe = message.replace("'", "’").replace('\n', ' ')
      script = render_to_string('js/say.js', {'say_this': message_safe})
      self.execute_script(script)
      if wait:
        self.wait_talking()
    self.maybe_pause()

  def move_mouse(
      self, element_or_clue, offset_x=5, offset_y=20, wait=False, quick=False):
    """ 7 and 18 are chosen fairly specifically. If you have a small "Did"
    button, say, and you use 10 and 10, say, then when you try to click,
    Selenium outsmarts itself.
    selenium.common.exceptions.ElementClickInterceptedException: Message:
    Element <button class="did" name="did" type="submit"> is not clickable at
    point (450,232) because another element <img src="/static/cursor.png">
    obscures it """
    element = self.get_element(element_or_clue)
    if self._go_slow:
      location = element.location
      context = {
          'x': location['x'] + offset_x, 'y': location['y'] + offset_y,
          'step': 3 if quick else 1}
      script = render_to_string('js/move_fake_mouse.js', context)
      self.execute_script(script)
      if wait:
        self.wait_mouse()
    self.maybe_pause()

  def show_photo_say(self, file_name, say):
    self.go_to_view('demo_photo', file_name=file_name)
    self.say(say, wait=True)

  def move_type(self, element_or_clue, keys, clear_first=False):
    from selenium.webdriver.common.keys import Keys
    element = self.get_element(element_or_clue)
    if self._go_slow:
      self.move_click(element)
      self.move_mouse(element, 10, 30)
    if clear_first:
      if self._go_slow:
        self.type(
            element, [Keys.BACKSPACE] * len(element.get_property('value')))
      else:
        element.clear()
    self.type(element, keys)

  def say_move_enter_date(self, element_or_clue, date, say):
    self.say(say)
    self.move_enter_date(element_or_clue, date)
    self.wait_talking()

  def move_enter_date(self, element_or_clue, date):
    element = self.get_element(element_or_clue)
    if self._go_slow:
      self.move_mouse(element, wait=True)
    self.enter_date(element, date)

  def say_move(self, element_or_clue, say):
    self.say(say)
    self.move_mouse(element_or_clue)
    self.wait_talking()
    self.wait_mouse()

  def say_move_click(self, element_or_clue, say):
    self.say(say)
    self.move_click(element_or_clue, wait_talking=True)

  def say_move_type(self, element_or_clue, keys, say, clear_first=False):
    self.say(say)
    self.move_type(element_or_clue, keys, clear_first=clear_first)
    self.wait_talking()

  def say_scroll(self, element_or_clue, say):
    self.say(say)
    self.scroll_to_element(element_or_clue)
    self.wait_talking()

  def move_click(self, element_or_clue, wait_talking=False, quick=False):
    # I only seem to have these problems in Chrome.
    from selenium.common.exceptions import (
        StaleElementReferenceException, ElementNotInteractableException)
    attempts = 0
    while attempts < 3:
      attempts += 1
      element = self.get_element(element_or_clue)
      if self._go_slow:
        self.move_mouse(element, quick=quick)
        self.wait_mouse()
        self.hover(element)
        if wait_talking:
          self.wait_talking()
      try:
        element.click()
        # Often when you click something you navigate to a new page, and the
        # demo and test should always halt in its tracks if it sees the error
        # screen.
        self.raise_if_on_error_screen()
        return
      except StaleElementReferenceException:
        pass
      except ElementNotInteractableException:
        time.sleep(.1)
    raise Exception('I got selenium exceptions 3 times in a row.')

  def hover(self, element_or_clue):
    self._hover_helper(element_or_clue, 'addClass')

  def hover_off(self, element_or_clue):
    self._hover_helper(element_or_clue, 'removeClass')

  def _hover_helper(self, element_or_clue, js_function):
    element = self.get_element(element_or_clue)
    self.execute_script(
        "$(arguments[0]).{}('hover');".format(js_function), element)

  def type(self, element_or_clue, keys):
    """ Pretend you're a user painstakingly manually typing in keys """
    element = self.get_element(element_or_clue)
    if self._go_slow:
      self.put_keyboard_caret_at_end(element)
      for key in keys:
        element.send_keys(key)
        if self._go_slow:
          self.wait(choice(range(5)) / 20.0)
    else:
      element.send_keys(keys)

  def put_keyboard_caret_at_end(self, element_or_clue):
    from selenium.webdriver.common.keys import Keys
    element = self.get_element(element_or_clue)
    keys = [Keys.RIGHT] * len(element.get_property('value'))
    element.send_keys(keys)

  def wait_talking(self):
    if self._go_slow:

      def closure():
        return self._js_variable_undefined_or_true('done_talking')
      self.wait_closure(closure, wait_seconds=20)
      self.maybe_pause()

  def wait_mouse(self):
    if self._go_slow:

      def done():
        return self._js_variable_undefined_or_true('done_moving_fake_mouse')
      self.wait_closure(done, wait_seconds=20)
      self.maybe_pause()

  def _js_variable_undefined_or_true(self, variable_name):
    script = 'return typeof(window.{}) == "undefined" || window.{};'.format(
        variable_name, variable_name)
    return_value = self.execute_script(script)
    return return_value is True

  def sign_up(self, email_address):
    self.say_move_type('email', email_address, """
        This is the sign up page. No passwords necessary. I enter my email""")

    self.say_move_click('email_me', 'and click the button.')
    self.say("""
        It emailed me a secure, single-use sign up link. Lets go take a
        look.""", wait=True)
    self.go_to_view(
        'sign_up_email_preview', query_string='to={}'.format(email_address))
    self.say_move('a', """
        This is the sign up email. Once I click the link, it will create an
        account for me. It should keep me logged in for a very long time.""")
    self.click_sign_up_link(email_address)

  def wait(self, seconds):
    if self._go_slow:
      super().wait(seconds)
