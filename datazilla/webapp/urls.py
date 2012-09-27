from django.conf.urls.defaults import patterns, include

from datazilla.webapp.apps.datazilla import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'webapp.views.home', name='home'),
    # url(r'^webapp/', include('webapp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    (r'^$', views.landing),

    (r'^(?P<project>\w+)/?', include('datazilla.webapp.apps.datazilla.urls')),

    # return statistics about Datazilla not particular to a project
    (r'^refdata/', include("datazilla.webapp.apps.datazilla.stats.urls_no_project")),

    )
