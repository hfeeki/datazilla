from django.conf.urls.defaults import patterns, url, include

from tastypie.api import Api

from models import api as execution
from .. import API_VERSION


v1_api = Api(api_name=API_VERSION)

v1_api.register(execution.RunResource())


urlpatterns = patterns(
    "datazilla.api",
    url(r"", include(v1_api.urls)),
    )
