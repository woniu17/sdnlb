from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'lb.views.home', name='home'),
    url(r'^ajax_del_member$', 'lb.views.ajax_del_member', name='ajax_del_member'),
)
