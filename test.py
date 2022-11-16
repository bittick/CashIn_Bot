import requests
from settings import django_url

r = requests.get(django_url + f'user/{83201441}/')
print(r.text)

float('123dw')