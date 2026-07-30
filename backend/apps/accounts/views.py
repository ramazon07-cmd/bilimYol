from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Classroom, ParentStudent
from .permissions import IsAdminRole, ReadOnlyOrAdmin
from .serializers import ClassroomSerializer, ParentStudentSerializer, UserSerializer


User = get_user_model()


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
    search_fields = ["username", "full_name", "email", "phone"]
    filterset_fields = ["role", "is_active"]
    ordering_fields = ["full_name", "date_joined"]

    def get_queryset(self):
        return User.objects.all().order_by("full_name")


class ClassroomViewSet(viewsets.ModelViewSet):
    serializer_class = ClassroomSerializer
    permission_classes = [ReadOnlyOrAdmin]
    search_fields = ["name", "program"]
    filterset_fields = ["grade", "teacher", "is_active"]

    def get_queryset(self):
        user = self.request.user
        queryset = Classroom.objects.select_related("teacher").prefetch_related("enrollments__student")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.TEACHER:
            return queryset.filter(teacher=user)
        if user.role == User.Role.STUDENT:
            return queryset.filter(students=user)
        child_ids = user.children_links.values_list("student_id", flat=True)
        return queryset.filter(students__id__in=child_ids).distinct()


class ParentStudentViewSet(viewsets.ModelViewSet):
    serializer_class = ParentStudentSerializer
    permission_classes = [ReadOnlyOrAdmin]

    def get_queryset(self):
        user = self.request.user
        queryset = ParentStudent.objects.select_related("parent", "student")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(Q(parent=user) | Q(student=user))
