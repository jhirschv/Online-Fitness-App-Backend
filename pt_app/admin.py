from django.contrib import admin
from .models import Program, Phase, Workout, Exercise, WorkoutExercise, User, UserProgramProgress, PhaseProgress, WorkoutSession, ExerciseLog, ExerciseSet, Message, ChatSession
from django.utils.html import format_html

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'id')

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'creator')
    search_fields = ('name', 'creator__username')
    list_filter = ('creator',)

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ('program', 'name', 'weeks', 'id')
    search_fields = ('program__name',)
    list_filter = ('program',)

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('phase', 'name', 'id')
    search_fields = ('name', 'phase__program__name')
    list_filter = ('phase__program',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'id')
    search_fields = ('name',)

@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ('workout', 'exercise', 'sets', 'reps', 'note', 'id')
    search_fields = ('workout__name', 'exercise__name')
    list_filter = ('workout__phase__program', 'exercise')

@admin.register(UserProgramProgress)
class UserProgramProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'current_phase', 'is_active', 'start_date')
    search_fields = ('user__username', 'program__name', 'current_phase__name')
    list_filter = ('program', 'current_phase', 'is_active')
    date_hierarchy = 'start_date'  # Enables a quick date drill down

class ExerciseSetAdmin(admin.ModelAdmin):
    list_display = ('exercise_log', 'set_number', 'reps', 'weight_used', 'video_link', 'id')
    list_filter = ('exercise_log', 'set_number')
    search_fields = ('exercise_log__workout_exercise__exercise__name', 'set_number')
    ordering = ('exercise_log', 'set_number')
    fieldsets = (
        (None, {
            'fields': ('exercise_log', 'set_number')
        }),
        ('Details', {
            'fields': ('reps', 'weight_used', 'video')
        }),
    )

    def video_link(self, obj):
        if obj.video:
            return format_html('<a href="{0}" target="_blank">View Video</a>', obj.video.url)
        return "No Video"

    video_link.short_description = "Video"

admin.site.register(PhaseProgress)
admin.site.register(WorkoutSession)
admin.site.register(ExerciseLog)
admin.site.register(ExerciseSet, ExerciseSetAdmin)
admin.site.register(Message)
admin.site.register(ChatSession)

