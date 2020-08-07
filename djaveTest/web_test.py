from abc import abstractmethod
import os
from pathlib import Path
import re
import time

from django.conf import settings
from django.shortcuts import reverse
from djaveAPI.status_codes import is_server_error
from djaveClassMagic.find_models import all_models
from djaveLogin.calc_urls import append_next_url, NEXT_URL
from djaveReport.date_range_report import FROM_DATE, TO_DATE
from djaveURL import dict_as_query
import requests


# all_web_tests means that I don't have to maintain a list of existing web
# tests. I can just scan for them. In order for all_web_tests to work, every
# app's web tests need to be imported into my_specific_app/web_test/__init__.py
# The downside to that is, when unit tests run, the unit test loader ends up
# scanning through all the files and running all the imports. Normally this
# would be fine, but selenium is a special case. It's only needed locally for
# web testing. The last time I tried to deploy it as a dependency to Heroku,
# Heroku freaked out with incomprehensible error messages. Hence we need to do
# this hack where selenium stuff is imported within functions so as to avoid
# import errors when unit tests run as part of continuous integration.


def all_web_tests():
  return all_models(WebTest)


class WebTest(object):
  def __init__(self, server):
    self.server = server
    self.driver = None

  @abstractmethod
  def run(self):
    raise NotImplementedError('run')

  def pre_run(self):
    from selenium import webdriver
    # Chrome seems to raise a bunch more selenium exceptions, like element not
    # interactable or stale element reference. I WISH I could use just regular
    # old Chrome purely because it has a beautiful speaking voice for the demo.
    # Buuuut you aren't allowed to use Chrome exactly, you have to use Chromium
    # or something, which ships with no voices. The sparse help I could find
    # online about this was about hooking Chromium up to espeak, but espeak
    # sounds just as bad as Firefox.  So as far as I can tell, there's no way
    # to use Chrome's beautiful speaking voice in my demos :( That's not all
    # though. self.driver =
    # webdriver.Chrome(service_args=['--enable-speech-dispatcher'])
    self.driver = webdriver.Firefox()

  def close_driver(self):
    from selenium.common.exceptions import SessionNotCreatedException
    if self.driver:
      try:
        self.driver.close()
      except SessionNotCreatedException:
        # The driver is closed already.
        pass

  def go_to_url(self, url):
    self.maybe_pause()
    self.driver.get(url)
    self.close_django_toolbar()
    if self.on_django_server_error_screen():
      raise Exception(
          'It appears I am on an error screen and the test has failed.')

  def on_django_server_error_screen(self):
    return bool(
        self.finds('exception_value', raise_exception_if_not_found=False))

  def go_to_view(self, view_name, query_string='', **kwargs):
    url = self.server_plus_reverse(view_name, **kwargs)
    if query_string:
      if query_string[0] != '?':
        url += '?'
      url += query_string
    self.go_to_url(url)

  def go_to_dated_report(self, view_name, from_date, to_date):
    query_string = dict_as_query({
        FROM_DATE: from_date.isoformat(), TO_DATE: to_date.isoformat()})
    self.go_to_view(view_name, query_string=query_string)

  def get_view_json(self, view_name, *args, **kwargs):
    response = requests.get(
        self.server_plus_reverse(view_name, *args, **kwargs))
    if is_server_error(response):
      if self.server == 'http://127.0.0.1:8000':
        raise Exception('Server error. Look at your ./manage.py runserver')
      raise Exception('Server error. Check {}/admin/errors/stayderror/'.format(
          self.server))
    return response.json()

  def server_plus_reverse(self, view_name, *args, **kwargs):
    path = reverse(view_name, args=args, kwargs=kwargs)
    return '{}{}'.format(self.server, path)

  def close_django_toolbar(self):
    from selenium.common.exceptions import NoSuchElementException
    # The debug toolbar gets in the way of elements when you try to click on
    # them sometimes.
    try:
      toolbar = self.driver.find_element_by_id('djDebugToolbar')
      if toolbar.value_of_css_property('display') == 'block':
        self.driver.find_element_by_id('djHideToolBarButton').click()
    except NoSuchElementException:
      pass

  def default_server(self):
    # return settings.STAGE_SERVER is also a common one. Or you can just do
    # ./manage.py my_web_test --server=https://stage.hihoward.com
    return 'http://127.0.0.1:8000'

  def wait(self, seconds):
    """ Seconds can be a float """
    time.sleep(seconds)

  def wait_closure(
      self, closure, error_message=None, wait_seconds=10,
      fail_on_timeout=True):
    attempts = 0
    poll_interval = 0.1
    max_attempts = wait_seconds / poll_interval
    while attempts < max_attempts:
      if closure():
        return
      self.wait(poll_interval)
      attempts += 1
    if fail_on_timeout:
      raise Exception(error_message or 'Closure was never True')

  def maybe_pause(self):
    """ When you're using ./manage.py runserver --settings
    main.web_test_settings you can press ` to pause and unpause during
    web demos and tests. """
    def done():
      return self._js_variable_undefined_or_true('un_pause')
    self.wait_closure(done, wait_seconds=8 * 60 * 60)

  def wait_for_class(self, class_name):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions
    WebDriverWait(self.driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.CLASS_NAME, class_name)))
    return self.find(class_name)

  def wait_for_xpath(self, xpath):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions
    WebDriverWait(self.driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, xpath)))
    return self.driver.find_element_by_xpath(xpath)

  def wait_for_text(self, xpath, expected_text):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions
    WebDriverWait(self.driver, 10).until(
        expected_conditions.text_to_be_present_in_element(
            (By.XPATH, xpath), expected_text))
    return self.driver.find_element_by_xpath(xpath)

  def raise_if_on_error_screen(self):
    if self.on_error_screen():
      message = 'There\'s an on-screen Django error. '
      if settings.LOCAL:
        message += 'Check your ./manage.py runserver. '
      else:
        message += 'Check for server error emails from {}. '.format(
            settings.THIS_SERVERS_BASE_URL)
      message += 'The error message is: {}'.format(
          self.driver.find_element_by_xpath('//div[@id="summary"]/pre').text)
      raise Exception(message)

  def on_error_screen(self):
    return 1 == len(self.driver.find_elements_by_id('traceback'))

  def click_button(self, container_or_button_id):
    from selenium.common.exceptions import NoSuchElementException
    try:
      button = self.driver.find_element_by_xpath(
          '//*[@id="{}"]//*[@class="button"]'.format(container_or_button_id))
    except NoSuchElementException:
      button = self.driver.find_element_by_xpath(
          '//*[@id="{}"]'.format(container_or_button_id))
    assert button.is_displayed()
    button.click()

  def screen_height(self):
    return self.driver.execute_script('return window.screen.height;')

  def scrolled_to(self):
    return self.driver.execute_script('return window.pageYOffset;')

  def is_scrolled_to(self, element):
    scrolled_to = self.scrolled_to()
    screen_height = self.screen_height()
    above = scrolled_to < element.location['y']
    below = scrolled_to + screen_height >= element.location['y']
    return above and below

  def scroll_to_bottom(self):
    self._scroll('document.body.scrollHeight')

  def scroll_to_element(self, element_or_clue):
    element = self.get_element(element_or_clue)
    self._scroll(str(element.location['y']))

  def _scroll(self, scrollTop):
    script = (
        "$('html, body').animate("
        "{scrollTop: " + scrollTop + "}, 800);")
    self.driver.execute_script(script)
    self.wait(.8)

  def img_path(self, img_file_name):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    app_dir = Path(this_dir).parent.as_posix()
    img_dir = os.path.join(app_dir, 'static')
    return os.path.join(img_dir, img_file_name)

  def do_file_upload(self, container, img_path):
    id_upload = container.find_element_by_xpath('.//input[@type="file"]')
    id_upload.send_keys(img_path)

  def login(self, email_address):
    self.find('email').send_keys(email_address)
    self.find('emailmealoginlink').click()
    self.click_login_link(email_address)

  def enter_date(self, element, date):
    element.send_keys(date.isoformat())

  def click_sign_up_link(self, email_address):
    self._click_login_or_sign_up_helper(email_address, 'djave_sign_up')

  def click_login_link(self, email_address):
    self._click_login_or_sign_up_helper(email_address, 'djave_login')

  def _click_login_or_sign_up_helper(self, email_address, view_name):
    find_login_token_url = '{}?email={}'.format(
        self.server_plus_reverse('login_token'), email_address)
    token = requests.get(find_login_token_url).json()['token']
    next_url = None
    next_url_finder = re.compile('{}=(.+)'.format(NEXT_URL))
    found = next_url_finder.findall(self.driver.current_url)
    if found:
      next_url = found[0]
    login_url = append_next_url(
        self.server_plus_reverse(view_name, token=token), next_url)
    self.go_to_url(login_url)

  def find(self, clue):
    return self.finds(clue)[0]

  def finds(self, clue, raise_exception_if_not_found=True, attempt=0):
    elts = self.driver.find_elements_by_class_name(clue)
    if len(elts):
      return elts
    elts = self.driver.find_elements_by_name(clue)
    if len(elts):
      return elts
    elts = self.driver.find_elements_by_id(clue)
    if len(elts):
      return elts
    elts = self.driver.find_elements_by_tag_name(clue)
    if len(elts):
      return elts
    if raise_exception_if_not_found:
      if attempt == 3:
        raise Exception('I was unable to find {}'.format(clue))
      time.sleep(.5)
      return self.finds(
          clue, raise_exception_if_not_found=raise_exception_if_not_found,
          attempt=attempt + 1)

  def find_with_value(self, clue, value):
    for elt in self.finds(clue):
      if elt.get_property('value') == value:
        return elt
    raise Exception('Never found {} with value {}'.format(clue, value))

  def find_pk(self, elt):
    return int(
        elt.find_element_by_xpath('ancestor::tr').get_attribute('data-pk'))

  def find_with_text(self, tag_name, text):
    found = self.finds_with_text(tag_name, text)
    if found:
      return found[0]
    raise Exception('I was unable to find a {} with {}'.format(tag_name, text))

  def finds_with_text(self, tag_name, text):
    found = []
    for elt in self.driver.find_elements_by_tag_name(tag_name):
      if elt.text.find(text) >= 0:
        found.append(elt)
    return found

  def get_element(self, element_or_clue):
    if isinstance(element_or_clue, str):
      return self.find(element_or_clue)
    return element_or_clue
