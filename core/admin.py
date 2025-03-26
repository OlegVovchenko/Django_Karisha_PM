from django.contrib import admin
from .models import Master, Service, Visit, Review

admin.site.register(Master)
admin.site.register(Service)
admin.site.register(Visit)
admin.site.register(Review)