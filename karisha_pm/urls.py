from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from core.admin_views import AdminDashboardView


urlpatterns = (
    [
        path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
        path('admin/', admin.site.urls),
        
        path("", views.MainView.as_view(), name="main"),
        path("thanks/", views.ThanksView.as_view(), name="thanks"),
        path("visits/", views.VisitListView.as_view(), name="visit_list"),
        path("review/create", views.ReviewCreateView.as_view(), name="review_create"),
        path("api/master-services/", views.get_master_services, name="get_master_services"),
        path("visits/update/<int:visit_id>/<int:status>/", views.update_visit_status, name="update_visit_status"),
        path("reviews/", views.ReviewListView.as_view(), name="review_list"),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)