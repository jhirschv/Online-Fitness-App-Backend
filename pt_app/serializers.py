from rest_framework import serializers
from .models import Program, Workout, Exercise, WorkoutExercise, User, WorkoutSession, ExerciseLog, ExerciseSet, Message, ChatSession, TrainerRequest,TrainerClientRelationship 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Max
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
from django.utils.text import capfirst
from django.utils.timesince import timesince
from django.core.files.images import get_image_dimensions
import uuid

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9_]+$',
                message='Username must be alphanumeric and can include underscores',
                code='invalid_username'
            ),
            MinLengthValidator(4, message="Username must be at least 4 characters long."),
            MaxLengthValidator(20, message="Username must be no longer than 20 characters.")
        ]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9!@#$%^&*()_+=\[\]{};:\'"\\|,.<>\/?~-]+$',
                message="Password must consist of alphanumeric and special characters only."
            ),
            MinLengthValidator(8, message="Password must be at least 8 characters long."),
            MaxLengthValidator(20, message="Password must be no longer than 20 characters.")
        ]
    )
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('username', 'password', 'email')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    
class GuestRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=False,  # No longer required in the incoming request
        default='',
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9_]+$',
                message='Username must be alphanumeric and can include underscores',
                code='invalid_username'
            ),
            MinLengthValidator(4, message="Username must be at least 4 characters long."),
            MaxLengthValidator(20, message="Username must be no longer than 20 characters.")
        ]
    )
    password = serializers.CharField(
        required=False,  # No longer required in the incoming request
        default='',
        write_only=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9!@#$%^&*()_+=\[\]{};:\'"\\|,.<>\/?~-]+$',
                message="Password must consist of alphanumeric and special characters only."
            ),
            MinLengthValidator(8, message="Password must be at least 8 characters long."),
            MaxLengthValidator(20, message="Password must be no longer than 20 characters.")
        ]
    )
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'guest')

    def validate(self, data):
        # Generate values
        data['username'] = f"guest_{uuid.uuid4().hex[:8]}"
        data['email'] = f"{data['username']}@example.com"
        data['password'] = uuid.uuid4().hex[:20]

        # Apply validators manually since these fields are read-only and would skip normal validation
        for validator in self.fields['username'].validators:
            validator(data['username'])
        for validator in self.fields['password'].validators:
            validator(data['password'])

        return data

    def create(self, validated_data):
        # Extract the plaintext password from validated data before creating the user
        plaintext_password = validated_data['password']

        # Create the user object
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=plaintext_password,  # Django hashes the password here
            guest=True
        )

        # Return both the user object and the plaintext password
        return user, plaintext_password

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
    
class PublicKeySerializer(serializers.Serializer):
    public_key = serializers.CharField()

    def validate_public_key(self, value):
        # Add validation logic for public key if necessary
        return value
    
class TrainerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerRequest
        fields = '__all__'

class TrainerClientRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerClientRelationship
        fields = '__all__'
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'id', 'trainers', 'clients','profile_picture']
        extra_kwargs = {
            'profile_picture': {'required': False}
        }

    def validate_profile_picture(self, value):
        """
        Validates the uploaded image.
        - Checks that it is a JPEG, PNG, or MPO file by MIME type.
        - Ensures the file size does not exceed 2MB.
        """
        # Validate file type by MIME type
        valid_mime_types = ['image/jpeg', 'image/png', 'image/mpo']
        mime_type = value.content_type  # Directly access content_type
        print(f"File MIME type: {mime_type}")  # Log the MIME type
        if mime_type not in valid_mime_types:
            raise serializers.ValidationError("File must be a JPEG or PNG image.")

        # Validate file size
        if value.size > 10 * 1024 * 1024:  # 2MB limit
            raise serializers.ValidationError("Image file too large ( > 2MB ).")

        # Optionally, validate image dimensions
        width, height = get_image_dimensions(value)
        if width > 8000 or height > 8000:
            raise serializers.ValidationError("Image dimensions should not be greater than 4000x4000 pixels.")

        return value

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(write_only=True, required=False)  # Not required if you're updating and not changing the exercise
    exercise = ExerciseSerializer(read_only=True)
    workout = serializers.PrimaryKeyRelatedField(queryset=Workout.objects.all(), write_only=True, required=False)
    order = serializers.IntegerField(required=False)

    class Meta:
        model = WorkoutExercise
        fields = ['id', 'exercise', 'exercise_name', 'sets', 'reps', 'note', 'workout', 'order']  

    def create(self, validated_data):
        exercise_name = validated_data.pop('exercise_name', None)

        # Capitalize the first letter of each word for consistency
        exercise_name = capfirst(exercise_name)

        # Check if an Exercise instance with creator=null exists for the given exercise_name
        universal_exercise = Exercise.objects.filter(name=exercise_name, creator=None).first()

        # Check if an Exercise instance with creator=request.user exists for the given exercise_name
        user_specific_exercise = Exercise.objects.filter(name=exercise_name, creator=self.context['request'].user).first()

        # Determine which Exercise instance to use or create
        if universal_exercise:
            exercise = universal_exercise
        elif user_specific_exercise:
            exercise = user_specific_exercise
        else:
            # Create a new Exercise instance with creator=request.user
            exercise = Exercise.objects.create(name=exercise_name, creator=self.context['request'].user)

        validated_data['exercise'] = exercise

        workout_exercise = WorkoutExercise.objects.create(**validated_data)
        return workout_exercise

    def update(self, instance, validated_data):
        exercise_name = validated_data.pop('exercise_name', None)

        # If an exercise name is provided, use it to get or create an Exercise instance
        if exercise_name:
            instance.exercise, created = Exercise.objects.get_or_create(name=exercise_name)
            instance.exercise.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class WorkoutSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    workout_exercises = WorkoutExerciseSerializer(many=True)
    program = serializers.PrimaryKeyRelatedField(queryset=Program.objects.all(), write_only=True, required=False)

    class Meta:
        model = Workout
        fields = '__all__'

    def create(self, validated_data):
        workout_exercises_data = validated_data.pop('workout_exercises', [])
        
        # Check if 'order' is provided, if not, determine the next order value
        if 'order' not in validated_data or validated_data['order'] is None:
            current_max_order = Workout.objects.filter(program=validated_data['program']).aggregate(Max('order'))['order__max']
            validated_data['order'] = (current_max_order or 0) + 1

        workout = Workout.objects.create(**validated_data)
        for workout_exercise_data in workout_exercises_data:
            workout_exercise_serializer = WorkoutExerciseSerializer(data=workout_exercise_data, context={'request': self.context['request'], 'workout': workout})
            if workout_exercise_serializer.is_valid(raise_exception=True):
                workout_exercise_serializer.save(workout=workout)
        return workout

    def update(self, instance, validated_data):
        workout_exercises_data = validated_data.pop('workout_exercises', None)
    
        # Update the Workout instance itself
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if workout_exercises_data is not None:
            # Clear existing workout_exercises and recreate them only if workout_exercises_data is provided
            instance.workout_exercises.all().delete()
            for workout_exercise_data in workout_exercises_data:
                workout_exercise_serializer = WorkoutExerciseSerializer(
                    data=workout_exercise_data, 
                    context={'request': self.context.get('request'), 'workout': instance}  # Pass the request object if available
                )
                if workout_exercise_serializer.is_valid(raise_exception=True):
                    workout_exercise_serializer.save(workout=instance)

        return instance
    
class WorkoutOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()

class ExerciseOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()

class ProgramSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    workouts = WorkoutSerializer(many=True, required=False)

    class Meta:
        model = Program
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        workouts_data = validated_data.pop('workouts', [])
        program = Program.objects.create(**validated_data)
        for workout_data in workouts_data:
            workout_serializer = WorkoutSerializer(data=workout_data, context={'program': program, 'request': request})
            if workout_serializer.is_valid(raise_exception=True):
                workout_serializer.save(program=program, creator=program.creator)
        return program

#workout journal feature
        
class ExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = ['id', 'exercise_log', 'set_number', 'reps', 'weight_used', 'video', 'is_logged']

class ExerciseSetVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = ['video']

class ExerciseLogSerializer(serializers.ModelSerializer):
    sets = ExerciseSetSerializer(many=True, read_only=True, source='exercise_sets')
    workout_exercise = WorkoutExerciseSerializer(read_only=True)

    class Meta:
        model = ExerciseLog
        fields = ['id', 'workout_exercise', 'sets_completed', 'note', 'sets']

class WorkoutSessionSerializer(serializers.ModelSerializer):
    workout = WorkoutSerializer(read_only=True)
    exercise_logs = ExerciseLogSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutSession
        fields = ['id', 'workout', 'date', 'completed', 'exercise_logs', 'active']
    
#Message feature
    
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

class ChatSessionSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    class Meta:
        model = ChatSession
        fields = ['id', 'created_at', 'participants', 'last_message']

    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()  # Get the most recent message
        if last_message:
            time_since = timesince(last_message.timestamp).split(',')[0]  # Simplify to the most significant unit
            if last_message.sender == self.context['request'].user:
                return {"message": f"You: {last_message.content}", "timestamp": time_since, "exact_time": last_message.timestamp.isoformat(), "read": last_message.read, "id": last_message.id, "sender": "user"}
            else:
                return {"message": last_message.content, "timestamp": time_since, "exact_time": last_message.timestamp.isoformat(), "read": last_message.read, "id": last_message.id, "sender": "other_user"}
        return None