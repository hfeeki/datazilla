from django.conf.urls.defaults import *
from datazilla.webapp.apps.datazilla import views

urlpatterns = patterns(
    '',
    (r'^$', views.graphs),
    (r'^help$', views.getHelp),

    # api --------------------------------------------------------------------
    url(r"^api/(?P<method>\w+)/$", include("datazilla.webapp.apps.datazilla.api.urls")),

#    (r'^load_test$', views.setTestData),
#    (r'^api/(?P<method>\w+)$', views.dataview),
)
