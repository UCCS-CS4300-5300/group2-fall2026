from django.contrib import admin
from django.urls import include,path
urlpatterns=[path("admin/",admin.site.urls),path("",include("core.urls"))]
urlpatterns += [path("npcs/", include("core.npc_urls"))]
