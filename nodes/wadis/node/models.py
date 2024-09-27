from nodes.wadis.node.model.data import *
from nodes.wadis.node.model.atmos import *
from nodes.wadis.node.model.saga import *
#See django/db/models/base.py in 52 (app_label = model_module.__name__.split('.')[-2]) because the table cache is made by app_label.

import importlib
import inspect
import django.db
from django.conf import settings
def set_databases_settings():
	import_libs = {}
	if settings.DATABASES:
		databases_settings = {}
		for database_type in settings.DATABASES:
			prefix = 'saga4_'
			if database_type.startswith(prefix):
				substance_suffix = database_type[len(prefix):]
				substances = Substancecorr.objects.filter(database_type=database_type).\
					values_list('id_substance', flat=True)
				for substance in substances:
					database_name = database_type + '_' + str(substance)
					databases_settings[database_name] = settings.DATABASES[database_type]
					databases_settings[database_name]['NAME'] = database_name
					import_libs[database_name] = "nodes.wadis.node.model." + substance_suffix + "." + database_type
			else:
				databases_settings[database_type] = settings.DATABASES[database_type]
		settings.DATABASES = databases_settings

		django.db.reset_queries()
		django.db.close_old_connections()
		django.db.connections = django.db.ConnectionHandler(databases_settings)

	return import_libs
import_libs = set_databases_settings()
for database_name in import_libs:
	globals()[database_name] = importlib.import_module(import_libs[database_name])
	for name, obj in inspect.getmembers(globals()[database_name]):
		if inspect.isclass(obj) and issubclass(obj, django.db.models.Model) and hasattr(obj, 'objects'):
			# obj.objects = obj.objects.using(database_name)
			pass

