from datetime import datetime

from django.core.management.base import BaseCommand
from djaveDT import get_readable_duration
from djaveTest.web_test import all_web_tests


class Command(BaseCommand):
  """ This is the thing that makes this work:
  python manage.py web_test my_web_test
  """
  def handle(self, *args, **options):
    server = options.get('server', None)
    web_test_instance = None
    start_with = options.get('start_with', None)
    first_test = True
    single_web_test_class_path = options['web_test']
    web_test_classes = self.web_test_classes(single_web_test_class_path)

    if not web_test_classes:
      if single_web_test_class_path:
        print('I was unable to find the {} web test'.format(
            single_web_test_class_path))
      else:
        print('I was unable to find any web tests')

    for web_test_class in web_test_classes:
      if not first_test:
        web_test_instance.close_driver()
      web_test_instance = web_test_class(server=server)
      test_name = web_test_instance.__class__.__module__
      if first_test and start_with and test_name.find(start_with) == -1:
        print('Skipping {}'.format(test_name))
      else:
        print(test_name)
        web_test_instance.pre_run()
        start = datetime.now()
        web_test_instance.run()
        duration_delta = datetime.now() - start
        print('Success in {}'.format(get_readable_duration(duration_delta)))
        first_test = False

  def web_test_classes(self, single_web_test_class_path):
    to_return = []
    for web_test_class in all_web_tests():
      if single_web_test_class_path:
        if web_test_class.__module__.find(single_web_test_class_path) >= 0:
          to_return.append(web_test_class)
      else:
        to_return.append(web_test_class)
    return to_return

  def add_arguments(self, parser):
    parser.add_argument('web_test', nargs='?', default=None, help=(
        'Only run web tests whose names contain this (optional) argument'))
    parser.add_argument(
        '--server', help='What server would you like to run this test on?',
        default='http://127.0.0.1:8000')
    parser.add_argument('--start_with', help=(
        'If this command runs more than one web test, jump into the middle of '
        'the webtests starting with the first test whose name contains this '
        'argument.'))
