# apps/Dermatologia_IA/urls.py
from django.urls import path

from .views.generateReport_and_sendReportEmail import GenerateReportView, SendReportEmailView
from .views.view_report_user_IA import *

app_name = 'dermatology'

urlpatterns = [
  path('upload/', UploadImageView.as_view(), name='upload_image'),
  path('search-patients/', SearchPatientsView.as_view(), name='search_patients'),
  path('process/<int:image_id>/', ProcessImageView.as_view(), name='process_image'),  # result
  path('reports/list/', ReportListView.as_view(), name='report_list'),
  path('report_details/<int:image_id>/', ReportDetailView.as_view(), name='report_detail'),

  # URL para generar el reporte PDF y enviarlo por email
  path('generate/report/<int:image_id>/', GenerateReportView.as_view(), name='generate_report'),
  path('send_report_email/<int:image_id>/', SendReportEmailView.as_view(), name='send_report_email'),

  # URLs para la gestión de pacientes
  path('pacientes/', PatientListView.as_view(), name='patient-list'),
  path('pacientes/nuevo/', PatientCreateView.as_view(), name='patient-create'),
  path('pacientes/<int:pk>/editar/', PatientUpdateView.as_view(), name='patient-update'),
]
