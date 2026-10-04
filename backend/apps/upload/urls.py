from django.urls import path
from . import views

urlpatterns = [
    path("image/", views.UploadImageView.as_view(), name="upload-image"),
    path("<int:pk>/status/", views.UploadStatusView.as_view(), name="upload-status"),
    path("<int:pk>/result/", views.UploadResultView.as_view(), name="upload-result"),
    path("<int:pk>/confirm/", views.UploadConfirmView.as_view(), name="upload-confirm"),
    path("ocr/extract/", views.OCRExtractView.as_view(), name="ocr-extract"),
    path("solve/", views.UploadSolveSelectedView.as_view(), name="upload-solve-selected"),
]
