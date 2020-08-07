import secrets
import string
import time as time_time

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import TestCase as DjangoTestCase


def get_test_group(**kwargs):
  return Group.objects.create(name=kwargs.get('name', 'whatever'))


def get_test_user(**kwargs):
  username = kwargs.get('username', None)
  if not settings.TEST and not username:
    raise Exception(
        'Please dont create random test users in a persistent database')
  if username:
    existing = User.objects.filter(username=username).first()
    if existing:
      return existing
  username = kwargs.get('username', 'bernie_sanders' + random_string(5))
  email = kwargs.get('email', '{}@email.com'.format(username))
  user = User.objects.create(
      password=kwargs.get('password', 'asdf1234'),
      is_superuser=kwargs.get('is_superuser', False),
      username=username,
      first_name=kwargs.get('first_name', 'Bernie'),
      last_name=kwargs.get('last_name', 'Sanders'),
      email=email,
      is_staff=kwargs.get('is_staff', False),
      is_active=kwargs.get('is_active', True))
  groups = kwargs.get('groups', [])
  for group in groups:
    existing = Group.objects.filter(name=group).first()
    if not existing:
      existing = get_test_group(name=group)
    user.groups.add(existing)
  return user


class TestCase(DjangoTestCase):
  """ If a test takes more than a second, print out which test this is and how
  many seconds. This is helpful for when one out of hundreds of tests is
  running very slowly. Otherwise it can be quite tricky to figure out what's
  taking so long. """
  def setUp(self):
    self._started_at = time_time.time()
    super().setUp()

  def tearDown(self):
    if not hasattr(self, '_started_at'):
      raise Exception(
          'Put a call to super().setUp() in your setUp()')
    elapsed = time_time.time() - self._started_at
    if elapsed > 1.0:
      print('\n{} ({}s)'.format(self.id(), round(elapsed, 2)))


def random_string(length=7):
  choices = string.ascii_uppercase + string.digits
  return ''.join(secrets.choice(choices) for _ in range(length))


def recursive_assert_equal(expected, got, message_prefix):
  if expected.__class__ != got.__class__:
    raise AssertionError('{} I expected a {} but I got a {}'.format(
        message_prefix, expected.__class__, got.__class__))
  if isinstance(expected, list):
    if len(expected) != len(got):
      raise AssertionError((
          '{} I expected a list of length {} but I got a list of '
          'length {}').format(
              message_prefix, len(expected), len(got)))
    for i, expected_element in enumerate(expected):
      got_element = got[i]
      recursive_assert_equal(
          expected_element, got_element, '{} element {} explains: '.format(
              message_prefix, i))
  elif expected != got:
    raise AssertionError('{} I expected {} but I got {}'.format(
        message_prefix, expected, got))
