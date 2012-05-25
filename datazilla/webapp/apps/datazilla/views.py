import os
import datetime
import json
import urllib
import datetime
import time
import zlib
import memcache

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render_to_response
from django.conf import settings
from django.http import HttpResponse

from datazilla.model.DatazillaModel import DatazillaModel

APP_JS = 'application/json'

def graphs(request, project=""):
    """Render a graph page for the given project."""

    ####
    #Load any signals provided in the page
    ####
    signals = []
    timeRanges = DatazillaModel.getTimeRanges()

    for s in SIGNALS:
        if s in request.POST:
            signals.append({
                "value": urllib.unquote(request.POST[s]),
                "name": s,
                })
    ###
    #Get reference data
    ###
    cacheKey = "{0}_reference_data".format(str(project))
    jsonData = '{}'
    mc = memcache.Client([settings.DATAZILLA_MEMCACHED], debug=0)
    compressedJsonData = mc.get(cacheKey)

    timeKey = 'days_30'

    ##reference data found in the cache: decompress##
    if compressedJsonData:

        jsonData = zlib.decompress( compressedJsonData )

    else:
        ####
        #reference data has not been cached:
        #serialize, compress, and cache
        ####
        dm = DatazillaModel(project, 'graphs.json')
        refData = dm.getTestReferenceData()
        dm.disconnect()

        refData['time_ranges'] = timeRanges

        jsonData = json.dumps(refData)

        mc.set(str(project) + '_reference_data', zlib.compress( jsonData ) )

    data = { 'time_key':timeKey,
             'reference_json':jsonData,
             'signals':signals }

    ####
    #Caller has provided the view parent of the signals, load in page.
    #This occurs when a data view is in its Pane form and is detached
    #to exist on it's own page.
    ####
    parentIndexKey = 'dv_parent_dview_index'
    if parentIndexKey in request.POST:
        data[parentIndexKey] = request.POST[parentIndexKey]

    return render_to_response('graphs.views.html', data)

def getHelp(request):
    """Return a help screen."""

    data = {}
    return render_to_response('help/dataview.generic.help.html', data)


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

        dm.disconnect();

    else:
        json = '{ "error":"Data view name %s not recognized" }' % method

    return HttpResponse(json, mimetype=APP_JS)


def _getTestReferenceData(project, method, request, dm):

    refData = dm.getTestReferenceData()

    jsonData = json.dumps( refData )

    return jsonData


def _getTestRunSummary(project, method, request, dm):

    productIds = []
    testIds = []
    platformIds = []

    #####
    #Calling _getIdList() insures that we have only numbers in the
    #lists, this gaurds against SQL injection
    #####
    if 'product_ids' in request.GET:
        productIds = DatazillaModel.getIdList(request.GET['product_ids'])
    if 'test_ids' in request.GET:
        testIds = DatazillaModel.getIdList(request.GET['test_ids'])
    if 'platform_ids' in request.GET:
        platformIds = DatazillaModel.getIdList(request.GET['platform_ids'])

    timeKey = 'days_30'
    timeRanges = DatazillaModel.getTimeRanges()
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
                key = DatazillaModel.getCacheKey(project, str(id), timeKey)
                compressedJsonData = mc.get(key)

                if compressedJsonData:
                    jsonData = zlib.decompress( compressedJsonData )
                    data = json.loads( jsonData )
                    extendList['data'].extend( data['data'] )
                    extendList['columns'] = data['columns']

            jsonData = json.dumps(extendList)

        else:
            key = DatazillaModel.getCacheKey(project,
                                             str(productIds[0]),
                                             timeKey)
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

#####
#UTILITY METHODS
#####
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
