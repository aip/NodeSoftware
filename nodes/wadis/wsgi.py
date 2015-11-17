import os
import sys

from django.core.wsgi import get_wsgi_application

# EDIT THE FOLLOWING TWO LINES
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'nodes.' + os.path.basename(os.path.dirname(__file__)) + '.settings'

application = get_wsgi_application()