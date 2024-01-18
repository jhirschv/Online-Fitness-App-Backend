from django.contrib import admin

from .models import Workout, Exercise

class ExerciseInline(admin.TabularInline):
    model = Workout.exercises.through
    extra = 1

class WorkoutAdmin(admin.ModelAdmin):
    inlines = [ExerciseInline]
    exclude = ('exercises',)

admin.site.register(Exercise)
admin.site.register(Workout, WorkoutAdmin)
