from django.urls import path
from .views import index, home, about, contact

urlpatterns = [
    # path('', home, name='home'),
    # path('about/', about, name='about'),
    # path('contact/', contact, name='contact'),
    path('feedback/', index, name='index'),
]
