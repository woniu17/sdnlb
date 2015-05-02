from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'lb.views.home', name='home'),
    url(r'^ajax_del_member$', 'lb.views.ajax_del_member', name='ajax_del_member'),
    url(r'^ajax_add_member$', 'lb.views.ajax_add_member', name='ajax_add_member'),
    url(r'^ajax_upd_member$', 'lb.views.ajax_upd_member', name='ajax_upd_member'),
    url(r'^ajax_get_member_list$', 'lb.views.ajax_get_member_list', name='ajax_get_member_list'),
)
