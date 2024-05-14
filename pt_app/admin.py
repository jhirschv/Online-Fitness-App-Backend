from django.contrib import admin
from .models import Program, Workout, Exercise, WorkoutExercise, User, UserProgramProgress, WorkoutSession, ExerciseLog, ExerciseSet, Message, ChatSession, TrainerRequest, TrainerClientRelationship 
from django.utils.html import format_html

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'id')

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'creator')
    search_fields = ('name', 'creator__username')
    list_filter = ('creator',)
    filter_horizontal = ('participants',)

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'is_ai_generated')
    search_fields = ('name',) 

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'id')
    search_fields = ('name',)

@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ('workout', 'exercise', 'sets', 'reps', 'note', 'id')
    search_fields = ('workout__name', 'exercise__name')  # This is correct as a tuple
    list_filter = ('exercise',) 

@admin.register(UserProgramProgress)
class UserProgramProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'is_active', 'start_date')
    search_fields = ('user__username', 'program__name')
    list_filter = ('program','is_active')
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

class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'workout_session', 'workout_exercise', 'sets_completed', 'note')  # Add other fields as needed

    def get_queryset(self, request):
        # This method can be used to modify the queryset. For example, you can optimize queries by selecting related fields
        qs = super().get_queryset(request)
        return qs.select_related('workout_session', 'workout_exercise')
    
@admin.register(TrainerRequest)
class TrainerRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')

@admin.register(TrainerClientRelationship)
class TrainerClientRelationshipAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'client', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('trainer__username', 'client__username')
    
admin.site.register(WorkoutSession)
admin.site.register(ExerciseLog, ExerciseLogAdmin)
admin.site.register(ExerciseSet, ExerciseSetAdmin)
admin.site.register(Message)
admin.site.register(ChatSession)

