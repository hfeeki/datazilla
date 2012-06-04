from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import Resource

from ..views import dataview, setTestData

import json

class ProjectData(object):

    def __init__(self, data, columns):
        self.data = data
        self.columns = columns

        # required for tastypie to work, but not very meaningful since the data
        # object is nested and opaque to the ProjectResource
        self.uuid = 1


class ProjectResource(Resource):
    data = fields.ListField(attribute="data")
    columns = fields.ListField(attribute="columns")

    class Meta:
        resource_name = 'project'


    def get_resource_uri(self, bundle_or_obj):
        kwargs = {
            'resource_name': self._meta.resource_name,
            }

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.uuid
        else:
            kwargs['pk'] = bundle_or_obj.uuid

        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)


    def get_object_list(self, request, project, method):
        """Main entry point for getting data for the stored project and method"""

        dv_res = dataview(request, project=project, method=method)
        dv_obj = json.loads(dv_res)

        pd = ProjectData(data=dv_obj["data"], columns=dv_obj["columns"])
        return [pd]


    def obj_get_list(self, request=None, **kwargs):
        """Persist the project and method for a data request"""
        project = kwargs["project"]
        method = kwargs["method"]

        return self.get_object_list(request, project, method)


    def obj_create(self, bundle, request=None, **kwargs):
        """Post a set of data for a project"""
        project = kwargs["project"]
        setTestData(request, project=project)

        #TODO @@@ in the bundle, we should respond with what setTestData sends
        # us or with something equivalent.
        return bundle
