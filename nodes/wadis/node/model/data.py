import sys

from django.db import models


class DataSource(models.Model):
	name = models.CharField(max_length = 120)
	description = models.TextField()
	id_biblio = models.IntegerField()
	biblio_index = models.TextField(blank = True)
	owner = models.CharField(max_length = 32)
	type = models.IntegerField()
	composition = models.CharField(max_length = 7)
	status = models.CharField(max_length = 8)
	pub_time_ds = models.DateTimeField()


	def getMethod(self):
		return methods[self.type].id if self.type is not None else None


	class Meta:
		abstract = True



class EnergyDataSource(DataSource):
	id_energy_ds = models.IntegerField(primary_key = True)


	def __unicode__(self):
		return u'ID:%s %s ' % (self.id_energy_ds, self.name)


	class Meta(DataSource.Meta):
		abstract = True
		db_table = 'energy_ds'



class TransitionDataSource(DataSource):
	id_transition_ds = models.IntegerField(primary_key = True)


	def __unicode__(self):
		return u'ID:%s %s ' % (self.id_transition_ds, self.name)


	class Meta(DataSource.Meta):
		abstract = True
		db_table = 'transition_ds'



class LineprofDataSource(DataSource):
	id_transition_ds = models.IntegerField(primary_key = True, db_column = 'id_lineprof_ds')
	temperature = models.FloatField()
	pressure = models.FloatField()


	def __unicode__(self):
		return u'ID:%s %s ' % (self.id_transition_ds, self.name)


	class Meta(DataSource.Meta):
		abstract = True
		db_table = 'lineprof_ds'


prefix = None

class Data(models.Model):
	id_substance = models.IntegerField()


	def getCase(self):
		return sys.modules[self.__class__.__module__].prefix


	class Meta:
		abstract = True



class EnergyData(Data):
	id_energy = models.BigIntegerField(primary_key = True)
	id_energy_ds = None
	energy = models.FloatField()
	energy_delta = models.FloatField(null = True, blank = True)
	defining_tr_n = models.IntegerField(null = True, blank = True)



	def qns(self):
		return []


	def __unicode__(self):
		return u'ID:%s %s %s =%s=%s=' % (self.id_energy, self.id_energy_ds, self.id_substance, self.energy, self.energy_delta)


	class Meta(Data.Meta):
		abstract = True
		db_table = 'energy'



class Data2(Data):
	id_transition = None
	id_transition_ds = None
	wavenumber = None
	wavenumber_err = None
	einstein_coefficient = None
	einstein_coefficient_err = None
	intensity = None
	intensity_err = None

	up = 0
	low = 0


	def up(self):
		return []


	def low(self):
		return []


	class Meta(Data.Meta):
		abstract = True



class TransitionData(Data2):
	id_transition = models.BigIntegerField(primary_key = True, db_column = 'id_transition')
	wavenumber = None
	wavenumber_err = None
	einstein_coefficient = None
	einstein_coefficient_err = None


	def __unicode__(self):
		return u'ID:%s %s %s =%s=%s=%s=%s=' % (self.id_transition, self.id_transition_ds, self.id_substance, self.wavenumber, self.wavenumber_err, self.einstein_coefficient, self.einstein_coefficient_err)


	class Meta(Data2.Meta):
		abstract = True
		db_table = 'transition'


class TransitionDataW(TransitionData):
	wavenumber = models.FloatField(db_column = 'wavelength')
	wavenumber_err = models.FloatField(db_column = 'wavelength_err', null = True, blank = True)
	einstein_coefficient = models.FloatField(db_column = 'einstein_coefficient', null = True, blank = True)
	einstein_coefficient_err = models.FloatField(db_column = 'einstein_coefficient_err', null = True, blank = True)

	class Meta(TransitionData.Meta):
		abstract = True


class LineprofData(Data2):
	id_transition = models.BigIntegerField(primary_key = True, db_column = 'id_lineprof')
	wavenumber = models.FloatField(db_column = 'wavelength')
	wavenumber_err = models.FloatField(db_column = 'wavelength_err', null = True, blank = True)
	intensity = models.FloatField(null = True, blank = True)
	intensity_err = models.FloatField(null = True, blank = True)


	def __unicode__(self):
		return u'ID:%s %s %s =%s=%s=%s=%s=' % (self.id_transition, self.id_transition_ds, self.id_substance, self.wavenumber, self.wavenumber_err, self.intensity, self.intensity_err)


	class Meta(Data2.Meta):
		abstract = True
		db_table = 'lineprof'



class LineprofHsA(models.Model):
	id_transition = None
	id_substance_act = models.IntegerField()
	halfwidth = models.FloatField(null = True, blank = True)
	halfwidth_err = models.FloatField(null = True, blank = True)
	halfwidth_td = models.FloatField(null = True, blank = True)
	halfwidth_td_err = models.FloatField(null = True, blank = True)
	shift = models.FloatField(null = True, blank = True)
	shift_err = models.FloatField(null = True, blank = True)
	shift_td = models.FloatField(null = True, blank = True)
	shift_td_err = models.FloatField(null = True, blank = True)


	def __unicode__(self):
		return u'ID:%s %s =%s=%s=%s=%s=' % (self.id_transition, self.id_substance_act, self.halfwidth, self.halfwidth_td, self.shift, self.shift_td)


	class Meta:
		abstract = True
		db_table = 'lineprof_hs'



class LineprofPpA(models.Model):
	id_transition_ds = None
	substance_act = models.IntegerField(unique = True)
	p_pressure = models.FloatField()


	def __unicode__(self):
		return u'ID:%s %s' % (self.id_transition_ds, self.substance_act)


	class Meta:
		abstract = True
		db_table = 'lineprof_pp'



class EnergyDigestA(models.Model):
	id_energy_ds = None
	id_substance = models.IntegerField()
	energy_min = models.FloatField()
	energy_max = models.FloatField()
	line_count = models.BigIntegerField()
	flags = models.CharField(max_length = 62)
	pub_time = models.DateTimeField()


	def __unicode__(self):
		return u'ID:%s %s' % (self.id_energy_ds, self.id_substance)


	class Meta:
		abstract = True
		db_table = 'energy_digest'



class TransitionDigestA(models.Model):
	id_transition_ds = None
	id_substance = models.IntegerField()
	wavenumber_min = None
	wavenumber_max = None
	line_count = models.BigIntegerField()
	flags = models.CharField(max_length = 78)
	pub_time = models.DateTimeField()


	def __unicode__(self):
		return u'ID:%s %s' % (self.id_transition_ds, self.id_substance)


	class Meta:
		abstract = True
		db_table = 'transition_digest'


class TransitionDigestAW(TransitionDigestA):
	wavenumber_min = models.FloatField(db_column = 'wavelength_min')
	wavenumber_max = models.FloatField(db_column = 'wavelength_max')

	class Meta(TransitionDigestA.Meta):
		abstract = True


class LineprofDigestA(models.Model):
	id_transition_ds = None
	id_substance = models.IntegerField()
	wavenumber_min = models.FloatField(db_column = 'wavelength_min')
	wavenumber_max = models.FloatField(db_column = 'wavelength_max')
	intensity_min = models.FloatField(null = True, blank = True)
	intensity_max = models.FloatField(null = True, blank = True)
	intensity_sum = models.FloatField(null = True, blank = True)
	line_count = models.BigIntegerField()
	flags = models.CharField(max_length = 57)
	pub_time = models.DateTimeField()


	def __unicode__(self):
		return u'ID:%s %s' % (self.id_transition_ds, self.id_substance)


	class Meta:
		abstract = True
		db_table = 'lineprof_digest'



class LineprofHsDigestA(models.Model):
	id_transition_ds = None
	id_substance = models.IntegerField()
	id_substance_act = models.IntegerField()
	flags = models.CharField(max_length = 91)


	def __unicode__(self):
		return u'ID:%s %s %s=%s=' % (self.id_transition_ds, self.id_substance, self.id_substance_act, self.flags)


	class Meta:
		abstract = True
		db_table = 'lineprof_hs_digest'



class Method(object):
	def __init__(self, id, category, description):
		self.id = id
		self.category = category
		self.description = description



def getMethods():
	#See XSAMS-schema. Allowed values are: experiment, theory, ritz, recommended, evaluated, empirical, scalingLaw, semiempirical, compilation, derived, observed
	methods = []
	methods.insert(0, Method("Theory", "theory", "theory"))
	methods.insert(1, Method("Exp", "experiment", "experiment"))
	return methods



def getCategoryTypeDict():
	categoryTypeDict = {}
	for type, method in enumerate(methods):
		categoryTypeDict[method.category] = type
	return categoryTypeDict


methods = getMethods()
categoryTypeDict = getCategoryTypeDict()

def toStr(item):
	strValue = 'X'
	if item is not None:
		if type(item) == tuple:
			if type(item[0]) == str and len(item[0]) > 4 and item[0][-4:] == 'Mode':
				return ''
			value = item[1]
		else:
			value = item

		if value is not None:
			if not (type(value) == int and value < 0):
				if type(value) == tuple:
					strValue = '.'.join(filter(bool, map(toStr, value)))
				else:
					strValue = str(value)
					if strValue == '+':
						strValue = '1'
					elif strValue == '-':
						strValue = '0'
	return strValue


idCount = 0
def makeStateId(id_substance, qns):
	global idCount
	idCount += 1
	return 'M' + str(id_substance - 1000000) + '-' + '.'.join(filter(bool, map(toStr, qns))) + '-' + str(idCount)



class State(object):
	def __init__(self, id_substance, case, obj, *args, **kwargs):
		self.case = case
		self._wrappedObj = obj
		self.id = None

		for arg in args:
			self.id = makeStateId(id_substance, arg)
			self.qns = dict(arg)
		self.qns.update(kwargs)


	def __getattr__(self, item):
		if item in self.__dict__:
			return getattr(self, item)
		elif item in self.qns:
			if type(self.qns[item]) == int and  self.qns[item] < 0:
				return None
			else:
				if type(self.qns[item]) == unicode and len(self.qns[item]) > 1:
					return self.qns[item][:-1].lstrip('0') + self.qns[item][-1:]
				else:
					return self.qns[item]
		elif self._wrappedObj and hasattr(self._wrappedObj, item):
			return getattr(self._wrappedObj, item)
		elif item == 'id_energy_ds':
			return EnergyDataSource()
		else:
			return None


	def __eq__(self, other):
		return self.id == other.id


	def __hash__(self):
		return hash(self.id)


	def __cmp__(self, other):
		if self.id < other.id:
			return -1
		elif self.id > other.id:
			return 1
		else:
			return 0


