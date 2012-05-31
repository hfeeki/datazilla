from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import Resource

from ..models import ProjectModel

import json

class ProjectData(object):
    data = "whatever"
    uuid = 1



class ProjectResource(Resource):
    data = fields.ListField(attribute="data")
    columns = fields.ListField(attribute="columns")

    class Meta:
        resource_name = 'project'
#        object_class=ProjectModel

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

        proj = ProjectModel(self.project)

        pd = ProjectData()
        data = json.loads(proj.dataview(request, self.method))["data"]
        columns = json.loads(proj.dataview(request, self.method))["columns"]
        pd.data = data
        pd.columns = columns
#        results = json.loads(proj.dataview(request, self.method))

        return [pd]


    def obj_get_list(self, request=None, **kwargs):
        self.project = kwargs["project"]
        self.method = kwargs["method"]

        return self.get_object_list(request)


#    def obj_get(self, request=None, **kwargs):
#        pass
#        # I don't think we do this, because the endpoint will
#        # only support getting all data for the project
#

