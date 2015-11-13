from wadis.node.model.fake import *
from wadis.node.model.atmos import *
from wadis.node.model.saga import *
#See django/db/models/base.py in 52 (app_label = model_module.__name__.split('.')[-2]) because the table cache is made by app_label.
from wadis.node.model.h2o import saga2
from wadis.node.model.co2 import saga2_co2
from wadis.node.model.diatomic import saga2_diatomic
from wadis.node.model.n2o import saga2_n2o
from wadis.node.model.c2h2 import saga2_c2h2

