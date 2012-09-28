function displayTable(project) {
    $('#summary_project_name').html(project);

    $.ajax({
               url: "/" + project + "/refdata/perftest/runs_by_branch?days_ago=30&show_test_runs=True"
           }).done(function(data) {
                       var table = $('#templates .branch_results').clone();

                       for (var branch in data) {
                           var table_aaData = [];
                           for (var i = 0; i < data[branch]["test_runs"].length; i++) {
                               var run = data[branch]["test_runs"][i];
                               table_aaData.push([run["date_run"], run["product"], run["version"], run["revision"]]);
                           }

                           table.find('#branch_name').html(branch);
                           $('#results .data').html(table);

                           this.resultsTable = table.find('table').dataTable({
                                                                                 aaData: table_aaData,
                                                                                 aoColumns: [
                                                                                     { sTitle: 'date run' },
                                                                                     { sTitle: 'product' },
                                                                                     { sTitle: 'version' },
                                                                                     { sTitle: 'revision' }
                                                                                 ],
                                                                                 bJQueryUI: true,
                                                                                 bPaginate: false,
                                                                                 bDestroy: true,
                                                                                 sScrollY: 300,
                                                                                 bAutoWidth: true

                                                                             });
                       }
                   })
}
