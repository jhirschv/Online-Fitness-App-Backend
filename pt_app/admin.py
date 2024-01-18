from django.contrib import admin

from .models import Workout, Exercise

class WorkoutAdmin(admin.ModelAdmin):
    filter_horizontal = ('exercises',)

admin.site.register(Exercise)
admin.site.register(Workout, WorkoutAdmin)
