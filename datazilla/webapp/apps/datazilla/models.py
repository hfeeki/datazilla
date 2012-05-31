from django.conf import settings
from django.db import models
from django.http import HttpResponse

import memcache
import datetime
import json
import urllib
import zlib

from datazilla.model.DatazillaModel import DatazillaModel
from datazilla.model import utils

# Create your models here.

class ProjectModel(object):
    """
    The model that for fetching specific data on a Project

    Make these into methods that the Resource can call.



    """

    def __init__(self, project):
        """Specify which project this model represents"""
        self.project=project


    def dataview(self, request, method=""):
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
            dm = DatazillaModel(self.project)
            if 'adapter' in DATAVIEW_ADAPTERS[method]:
                json = DATAVIEW_ADAPTERS[method]['adapter'](self.project,
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

        return json


def _getTestReferenceData(project, method, request, dm):

    refData = dm.getTestReferenceData()

    jsonData = json.dumps( refData )

    return jsonData


def _getTestRunSummary(project, method, request, dm):

    productIds = []
    testIds = []
    platformIds = []

    #####
    #Calling get_id_list() insures that we have only numbers in the
    #lists, this gaurds against SQL injection
    #####
    if 'product_ids' in request.GET:
        productIds = utils.get_id_list(request.GET['product_ids'])
    if 'test_ids' in request.GET:
        testIds = utils.get_id_list(request.GET['test_ids'])
    if 'platform_ids' in request.GET:
        platformIds = utils.get_id_list(request.GET['platform_ids'])

    timeKey = 'days_30'
    timeRanges = utils.get_time_ranges()
    if 'tkey' in request.GET:
        timeKey = request.GET['tkey']

    if not productIds:
        ##Set default productId##
        productIds = [12]

    jsonData = '{}'

    mc = memcache.Client([settings.DATAZILLA_MEMCACHED], debug=0)

    if productIds and (not testIds) and (not platformIds):

        if len(productIds) > 1:
            extendList = { 'data':[], 'columns':[] }
            for id in productIds:
                key = utils.get_cache_key(project, str(id), timeKey)
                compressedJsonData = mc.get(key)

                if compressedJsonData:
                    jsonData = zlib.decompress( compressedJsonData )
                    data = json.loads( jsonData )
                    extendList['data'].extend( data['data'] )
                    extendList['columns'] = data['columns']

            jsonData = json.dumps(extendList)

        else:
            key = utils.get_cache_key(
                project,
                str(productIds[0]),
                timeKey,
                )
            compressedJsonData = mc.get(key)

            if compressedJsonData:
                jsonData = zlib.decompress( compressedJsonData )

    else:
        table = dm.getTestRunSummary(timeRanges[timeKey]['start'],
                                     timeRanges[timeKey]['stop'],
                                     productIds,
                                     platformIds,
                                     testIds)

        jsonData = json.dumps( table )

    return jsonData


def _getTestValues(project, method, request, dm):

    data = {};

    if 'test_run_id' in request.GET:
        data = dm.getTestRunValues( request.GET['test_run_id'] )

    jsonData = json.dumps( data )

    return jsonData


def _getPageValues(project, method, request, dm):

    data = {};

    if ('test_run_id' in request.GET) and ('page_id' in request.GET):
        data = dm.getPageValues( request.GET['test_run_id'], request.GET['page_id'] )

    jsonData = json.dumps( data )

    return jsonData


def _getTestValueSummary(project, method, request, dm):

    data = {};

    if 'test_run_id' in request.GET:
        data = dm.getTestRunValueSummary( request.GET['test_run_id'] )

    jsonData = json.dumps( data )

    return jsonData


##################
# FROM VIEWS.PY

def setTestData(request):
    # @@@ TODO This looks like an API
    # this is not the submission of a form, so we should use tastypie for this.

    jsonData = '{"error":"No POST data found"}'

    if 'data' in request.POST:

        jsonData = request.POST['data']
        unquotedJsonData = urllib.unquote(jsonData)
        data = json.loads( unquotedJsonData )

        dm = DatazillaModel(project, 'graphs.json')
        dm.loadTestData( data, unquotedJsonData )
        dm.disconnect()

        jsonData = json.dumps( { 'loaded_test_pages':len(data['results']) } )

    return HttpResponse(jsonData, mimetype=APP_JS)


#####
#UTILITY METHODS
#####
"""
Make each of these into methods of a ProjectModel class, that we then have the
ProjectResource query to get the right info.

Not sure what the SIGNALS are for.
"""
DATAVIEW_ADAPTERS = { ##Flat tables SQL##
                      'test_run':{},
                      'test_value':{ 'fields':[ 'test_run_id', ] },
                      'test_option_values':{ 'fields':[ 'test_run_id', ] },
                      'test_aux_data':{ 'fields':[ 'test_run_id', ] },

                      ##API only##
                      'get_test_ref_data':{ 'adapter':_getTestReferenceData},

                      ##Visualization Tools##
                      'test_runs':{ 'adapter':_getTestRunSummary,
                                    'fields':['test_run_id',
                                              'test_run_data']
                      },

                      'test_chart':{ 'adapter':_getTestRunSummary,
                                     'fields':['test_run_id',
                                               'test_run_data'] },

                      'test_values':{ 'adapter':_getTestValues,
                                      'fields':['test_run_id'] },

                      'page_values':{ 'adapter':_getPageValues,
                                      'fields':['test_run_id',
                                                'page_id'] },

                      'test_value_summary':{ 'adapter':_getTestValueSummary,
                                             'fields':['test_run_id'] } }

SIGNALS = set()
for dv in DATAVIEW_ADAPTERS:
    if 'fields' in DATAVIEW_ADAPTERS[dv]:
        for field in DATAVIEW_ADAPTERS[dv]['fields']:
            SIGNALS.add(field)



###################
# FUTURE MODEL METHOD STRUCTURE




#    def test_run(self):
#        pass
#
#
#    def test_value(self, test_run_id):
#        pass
#
#
#    def test_option_values(self, test_run_id):
#        pass
#
#
#    def test_aux_data(self, test_run_id):
#        pass
#
#
#        ##API only##
#    def get_test_ref_data(self):
#        self._getTestReferenceData()
#
#
#        ##Visualization Tools##
#    def test_runs(self, test_run_id, test_run_data):
#        self._getTestRunSummary()
#
#
#    def test_chart(self, test_run_id, test_run_data):
#        self._getTestRunSummary()
#
#
#    def test_values(self, test_run_id):
#        self._getTestValues()
#
#
#    def page_values(self, test_run_id, page_id):
#        self._getPageValues()
#
#
#    def test_value_summary(self, test_run_id):
#        self._getTestValueSummary
#
#
