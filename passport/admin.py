from django.contrib import admin

from .models import Classroom, Guardianship, Passport, Profile, Student, StudentRecord


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'grade']
    list_filter = ['grade']
    search_fields = ['first_name', 'last_name']


@admin.register(Guardianship)
class GuardianshipAdmin(admin.ModelAdmin):
    list_display = ['guardian', 'student', 'relationship']


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'period']
    filter_horizontal = ['teachers', 'students']


@admin.register(StudentRecord)
class StudentRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'source', 'date', 'title']
    list_filter = ['source', 'date']
    search_fields = ['title', 'body']


admin.site.register(Passport)
