import datetime
import json
import urllib
import zlib
import memcache

from django.shortcuts import render_to_response
from django.conf import settings

from models import SIGNALS
from datazilla.model import DatazillaModel
from datazilla.model import utils

APP_JS = 'application/json'

def graphs(request, project=""):
    """Render a graph page for the given project."""

    ####
    #Load any signals provided in the page
    ####
    signals = []
    timeRanges = utils.get_time_ranges()

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
        dm = DatazillaModel(project)
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
