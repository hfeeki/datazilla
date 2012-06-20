from MySQLdb import IntegrityError
from optparse import make_option
from django.core.management.base import BaseCommand
from datazilla.model import PushLogModel
import urllib
import json
import datetime
from django.conf import settings



class Command(BaseCommand):
    """
    Management command to update the pushlog table with the latest pushes.

    example resulting url:
        https://hg.mozilla.org/integration/mozilla-inbound/json-pushes?full=1&startdate=06/04/2012&enddate=06/07/2012


    """

    help = "Update the repo pushlog table."

    option_list = BaseCommand.option_list + (

        make_option("--repo_host",
                    action="store",
                    dest="repo_host",
                    default=None,
                    help="The host name for the repo (e.g. hg.mozilla.org)"),

        make_option("--uri",
                    action="store",
                    dest="uri",
                    default="integration/mozilla-inbound/json-pushes",
                    help="(optional) The URI for fetching the pushlogs from " +
                    "the given repo_host."),

        make_option("--enddate",
                    action="store",
                    dest="enddate",
                    default=None,
                    help="(optional) The ending date range for pushlogs in " +
                         "the format: MM/DD/YYYY.  Default to today."),

        make_option("--numdays",
                    action="store",
                    dest="numdays",
                    default=None,
                    help="Number of days worth of pushlogs to return."),
        )


    def handle(self, *args, **options):
        """ Store pushlog data in the database. """

        repo_host = options.get("repo_host")
        uri = options.get("uri")
        enddate = options.get("enddate")
        numdays = int(options.get("numdays"))

        if not repo_host:
            self.stdout.write("You must supply a host name for the repo pushlogs " +
                              "to store: --repo_host hostname\n")
            return

        if not numdays:
            self.stdout.write("You must supply the number of days data.\n")
            return

        if enddate:
            #create a proper datetime.date for calculation of startdate
            m, d, y = enddate.split("/")
            _enddate = datetime.date(month=int(m), day=int(d), year=int(y))
        else:
            _enddate = datetime.date.today()

        # calculate the startdate

        _startdate = _enddate - datetime.timedelta(days=numdays)

        params = {
            "full": 1,
            "startdate": _startdate.strftime("%m/%d/%y"),
        }
        # enddate is optional.  the endpoint will just presume today,
        # if not given.
        if enddate:
            params.update({"enddate": enddate})

        url = "https://{0}/{1}?{2}".format(
            repo_host,
            uri,
            urllib.urlencode(params)
        )

        # fetch the JSON content from the constructed URL.
        res = urllib.urlopen(url)

        json_data = res.read()
        data = json.loads(json_data)

        plm = PushLogModel()
        ds = plm.sources["hgmozilla"]

        # one pushlog
        for pushlog_json_id, pushlog in data.items():
            # make sure the push_log_id isn't confused with a previous iteration

            placeholders = [
                pushlog_json_id,
                pushlog["date"],
                pushlog["user"],
                ]
            try:
                push_log_id = self._insert_data_and_get_id(
                    ds,
                    "set_push_log",
                    placeholders=placeholders,
                    )

                # process the nodes of the pushlog
                # TODO: should this table be called "changesets" instead?
                for cs in pushlog["changesets"]:
                    placeholders = [
                        cs["node"],
                        cs["author"],
                        cs["branch"],
                        cs["desc"],
                        push_log_id,
                        ]

                    try:
                        node_id = self._insert_data_and_get_id(
                            ds,
                            "set_node",
                            placeholders=placeholders,
                            )

                        # process the files of nodes
                        for file in cs["files"]:
                            placeholders = [
                                node_id,
                                file,
                                ]
                            try:
                                self._insert_data(
                                    ds,
                                    "set_file",
                                    placeholders=placeholders,
                                    )
                            except IntegrityError, e:
                                self.stdout.write("Skip dup- pushlog: {0}, node: {1}, file: {2}".format(
                                    pushlog_json_id,
                                    cs["node"],
                                    file,
                                ))

                    except IntegrityError, e:
                        self.stdout.write("Skip dup- pushlog: {0}, node: {1}".format(
                            pushlog_json_id,
                            cs["node"],
                            ))


            except IntegrityError:
                self.stdout.write("Skip dup- pushlog: {0}".format(
                    pushlog_json_id,
                ))

        ds.disconnect()


    def _insert_data(self, ds, statement, placeholders, executemany=False):

        return ds.dhub.execute(
            proc='hgmozilla.inserts.' + statement,
            debug_show=settings.DEBUG,
            placeholders=placeholders,
            executemany=executemany,
            return_type='iter',
            )


    def _insert_data_and_get_id(self, ds, statement, placeholders):

        self._insert_data(ds, statement, placeholders)

        id_iter = ds.dhub.execute(
            proc='hgmozilla.selects.get_last_insert_id',
            debug_show=settings.DEBUG,
            return_type='iter',
            )

        return id_iter.get_column_data('id')


