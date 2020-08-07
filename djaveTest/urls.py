from djaveTest.views import demo_done, demo_photo
from django.urls import path


djaveTest_urls = [
    path('demo_done', demo_done, name='demo_done'),
    path('demo_photo/<file_name>', demo_photo, name='demo_photo')]
