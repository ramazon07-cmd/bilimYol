from django.contrib import admin

from .models import DiagnosticReport, ExamAssignment, ExamAttempt, Roadmap, RoadmapStage, SkillResult, StudentAnswer, SubjectResult, TopicResult, WeeklyTask


admin.site.register(ExamAssignment)
admin.site.register(ExamAttempt)
admin.site.register(StudentAnswer)
admin.site.register(DiagnosticReport)
admin.site.register(SubjectResult)
admin.site.register(TopicResult)
admin.site.register(SkillResult)
admin.site.register(Roadmap)
admin.site.register(RoadmapStage)
admin.site.register(WeeklyTask)
