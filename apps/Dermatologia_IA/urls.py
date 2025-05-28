# core/Dermatologia_IA/urls.py
from django.urls import path

from .views.generateReport_and_sendReportEmail import GenerateReportView, SendReportEmailView
from .views.view_report_user_IA import UploadImageView, ProcessImageView, ReportListView, ReportDetailView

app_name = 'dermatology'

urlpatterns = [
    path('upload/', UploadImageView.as_view(), name='upload_image'),
    path('process/<int:image_id>/', ProcessImageView.as_view(), name='process_image'),
    path('reports/list/', ReportListView.as_view(), name='report_list'),
    path('report_details/<int:image_id>/', ReportDetailView.as_view(), name='report_detail'),

    # URL para generar el reporte PDF y enviarlo por email
    path('generate/report/<int:image_id>/', GenerateReportView.as_view(), name='generate_report'),
    path('send_report_email/<int:image_id>/', SendReportEmailView.as_view(), name='send_report_email'),
]
