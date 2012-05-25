from django.conf.urls.defaults import patterns, url, include

from tastypie.api import Api

from resources import ProjectResource
from .. import API_VERSION

# if we version the api
#v1_api = Api(api_name="v1")
#v1_api.register(ProjectResource())

project_resource = ProjectResource()

urlpatterns = patterns(
    "datazilla.api",
    url(r"", include(project_resource.urls)),
    )
#    (r'^load_test$', views.setTestData),
#    (r'^api/(?P<method>\w+)$', views.dataview),
