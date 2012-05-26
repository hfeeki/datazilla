from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import Resource


class ProjectData(object):
    proj_data = "whatever"
    uuid = 1



class ProjectResource(Resource):
    proj_data = fields.CharField(attribute="proj_data")

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

        results = []
        result = ProjectData()
        result.proj_data = {
            "project": self.project,
            "method": self.method,
            }
        results.append(result)
        return results


    def obj_get_list(self, request=None, **kwargs):
        self.project = kwargs["project"]
        self.method = kwargs["method"]

        return self.get_object_list(request)


    def obj_get(self, request=None, **kwargs):
        pass
        # I don't think we do this, because the endpoint will
        # only support getting all data for the project


    def dataview(request, project="", method=""):
        # @@@ TODO This looks like an API
        # this is getting raw data, so we should use tastypie for this.

        procPath = "graphs.views."
        ##Full proc name including base path in json file##
        fullProcPath = "{0}{1}".format(procPath, method)

        if settings.DEBUG:
            ###
            #Write IP address and datetime to log
            ###
            print "Client IP:{0}".format(request.META['REMOTE_ADDR'])
            print "Request Datetime:{0}".format(str(datetime.datetime.now()))

        json = ""
        if method in DATAVIEW_ADAPTERS:
            dm = DatazillaModel(project, 'graphs.json')
            if 'adapter' in DATAVIEW_ADAPTERS[method]:
                json = DATAVIEW_ADAPTERS[method]['adapter'](project,
                                                            method,
                                                            request,
                                                            dm)
            else:
                if 'fields' in DATAVIEW_ADAPTERS[method]:
                    fields = []
                    for f in DATAVIEW_ADAPTERS[method]['fields']:
                        if f in request.POST:
                            fields.append( dm.dhub.escapeString( request.POST[f] ) )
                        elif f in request.GET:
                            fields.append( dm.dhub.escapeString( request.GET[f] ) )

                    if len(fields) == len(DATAVIEW_ADAPTERS[method]['fields']):
                        json = dm.dhub.execute(
                            proc=fullProcPath,
                            debug_show=settings.DEBUG,
                            placeholders=fields,
                            return_type='table_json')

                    else:
                        json = ('{ "error":"{0} fields required, {1} provided" }'.format(
                            str(len(DATAVIEW_ADAPTERS[method]['fields'])),
                            str(len(fields))))

                else:

                    json = dm.dhub.execute(proc=fullProcPath,
                                           debug_show=settings.DEBUG,
                                           return_type='table_json')

            dm.disconnect()

        else:
            json = '{ "error":"Data view name %s not recognized" }' % method

        return HttpResponse(json, mimetype=APP_JS)
