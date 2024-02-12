from django.contrib import admin
from .models import Program, Phase, Workout, Exercise, WorkoutExercise

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'creator')
    search_fields = ('name', 'creator__username')
    list_filter = ('creator',)

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ('program', 'number', 'weeks')
    search_fields = ('program__name',)
    list_filter = ('program',)

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('phase', 'name')
    search_fields = ('name', 'phase__program__name')
    list_filter = ('phase__program',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ('workout', 'exercise', 'sets', 'reps', 'note')
    search_fields = ('workout__name', 'exercise__name')
    list_filter = ('workout__phase__program', 'exercise')


