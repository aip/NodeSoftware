from django.conf.urls import *

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
                       # Uncomment the next line to enable the admin:
                       # (r'^admin/', include(admin.site.urls)),
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       (r'^tap/', include('vamdctap.urls')),
                       (r'', include('nodes.wadis.node.urls')),
                       )

handler500 = 'vamdctap.views.tapServerError'
handler404 = 'vamdctap.views.tapNotFoundError'
