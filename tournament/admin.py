from django.contrib import admin
from .models import Tournament, Participant, Game, SetResult


# Register your models here.
admin.site.register(Tournament)
admin.site.register(Participant)
admin.site.register(Game)
admin.site.register(SetResult)
