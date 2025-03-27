from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views


urlpatterns = (
    [
        path('admin/', admin.site.urls),
        path("", views.MainView.as_view(), name="main"),
        path("thanks/", views.ThanksView.as_view(), name="thanks"),
        path("visits/", views.VisitListView.as_view(), name="visit_list"),
        path("review/create", views.ReviewCreateView.as_view(), name="review_create"),
        path("api/master-services/", views.get_master_services, name="get_master_services"),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)