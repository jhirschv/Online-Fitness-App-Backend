from django.utils import timezone
from .models import Program, Phase, Workout, Exercise, WorkoutExercise, User, UserProgramProgress, PhaseProgress, WorkoutSession, ExerciseLog

def set_or_update_user_program_progress(user, program_id):
    program = Program.objects.get(id=program_id)

    UserProgramProgress.objects.filter(user=user, is_active=True).exclude(program=program).update(is_active=False)
    
    user_program_progress, created = UserProgramProgress.objects.get_or_create(
        user=user,
        program=program,
        defaults={
            'current_phase': program.phases.first(),  # Assuming you want to start with the first phase
            'is_active': True,
            'start_date': timezone.now(),
        }
    )
    
    if not created:
        # If an existing progress is found, simply ensure it's marked as active
        user_program_progress.is_active = True
        user_program_progress.current_phase = program.phases.first()  # Reset to the first phase if reactivating
        user_program_progress.save()

    return user_program_progress