from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import Resource

from ..views import dataview

import json

class ProjectData(object):
    data = "whatever"
    uuid = 1



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


    def get_object_list(self, request):
        """Main entry point for get data"""

        pd = ProjectData()
        dv_res = dataview(request, project=self.project, method=self.method)
        dv_obj = json.loads(dv_res)
        pd.data = dv_obj["data"]
        pd.columns = dv_obj["columns"]

        return [pd]


    def obj_get_list(self, request=None, **kwargs):
        self.project = kwargs["project"]
        self.method = kwargs["method"]

        return self.get_object_list(request)



