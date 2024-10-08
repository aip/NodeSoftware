import sys
import os
from django.http import QueryDict, HttpRequest
from django.utils.importlib import import_module
from lxml import objectify, etree
from django.db import connections

from django.conf import settings
#Warning! Forced DEBUG = FALSE in DjangoTestSuiteRunner->setup_test_environment->settings.DEBUG = False

from nodes.wadis.node.models import *
import nodes.wadis.node.model.data as data
import nodes.wadis.node.transforms as transforms
import nodes.wadis.node.queryfunc as queryfunc


test = import_module(settings.UTILPKG + ".test")
inchi = import_module(settings.UTILPKG + ".inchi")
dicts = import_module('nodes.' + settings.NODENAME + '.' + settings.NODEPKG + '.dictionaries')
if 'NodeID' in dicts.RETURNABLES:
	NODEID = dicts.RETURNABLES['NodeID']
else:
	NODEID = 'fake'

DEBUG = False
import unittest
from django.test import SimpleTestCase as TestCase

from django.test.client import Client
from vamdctap import views


from other.verification.check import XSAMS_NS, RulesParser, Rule, \
	XSAMS_FILE_ABS_PATH, VERIFICATION_FILE_ABS_PATH
from other.verification.test import getXSD


xsamsXSD=getXSD(XSAMS_FILE_ABS_PATH)
verificationXSD = getXSD(VERIFICATION_FILE_ABS_PATH)
testClient = Client()


def print_all_queries(databases=[]):
	for x in connections:
		if not databases or x in databases:
			print x
			for query in connections[x].queries:
				print query['time']
				print query['sql']


def toDict(queryDict):
	dict = {}
	for key in queryDict:
		dict[key] = queryDict[key]
	return dict

def removeSelfSource(objTree):
	for source in objTree.xpath('//xsams:Sources/xsams:Source[contains(./xsams:Comments[1]/text(), "This Source is a self-reference.")]', namespaces={"xsams":XSAMS_NS}):
		source[0].getparent().remove(source)



#pyprof2calltree -k -i vamdc_profile.log
@test.profile('vamdc_profile.log')
def getBigFile():
	settings.DEBUG = True
	#query = 'LANG=VSS2&FORMAT=VERIFICATION&QUERY=SELECT All WHERE InChI =\'InChI=1S/H2O/h1H2/i/hD\''
	#query = "LANG=VSS2&FORMAT=XSAMS&QUERY=select * where (RadTransWavenumber >= 1239.0 AND RadTransWavenumber <= 1240.0) AND ((InchiKey IN ('A', 'XLYOFNOQVPJJNP-DYCDLGHISA-N','XLYOFNOQVPJJNP-DQGQKLTASA-N')))"
	query = "LANG=VSS2&FORMAT=VERIFICATION&QUERY=select * where (RadTransWavenumber >= 1239.0 AND RadTransWavenumber <= 1240.0) AND ((InchiKey IN ('A', 'XLYOFNOQVPJJNP-DYCDLGHISA-N','XLYOFNOQVPJJNP-DQGQKLTASA-N')))"

	request = HttpRequest()
	request.META["SERVER_NAME"] = 'localhost'
	request.META["SERVER_PORT"] = '80'
	request.META["REMOTE_ADDR"] = '127.0.0.1'
	request.META["QUERY_STRING"] = query

	request.REQUEST = toDict(QueryDict(query))

	return views.sync(request).content
#getBigFile()



class VerificationTest(TestCase):
	prefixURL = "/tap/sync?"
	# test data sources is only less than 1500 transitions
	query = 'LANG=VSS2&FORMAT=VERIFICATION&QUERY=SELECT All WHERE InChI =\'InChI=1S/H2O/h1H2/i/hD\' AND RadTransWavenumber > 1250.846 AND RadTransWavenumber < 1250.847'


	def setUp(self):
		data.idCount = 0
		self.request = HttpRequest()
		self.request.META["SERVER_NAME"] = 'localhost'
		self.request.META["SERVER_PORT"] = '80'
		self.request.META["REMOTE_ADDR"] = '127.0.0.1'
		self.request.META["QUERY_STRING"] = self.query

		self.queryDict = toDict(QueryDict(self.query))


	def testAddRules(self):
		rulesParser = RulesParser()
		# 2.6 set([]) ; 2.7 {}
		rulesParser.addRules = set([Rule(NODEID, "abs(nltcs:J + nltcs:Ka) <= 11"), Rule(NODEID, "abs(nltcs:Ka + nltcs:v1) <= pow(nltcs:v2, nltcs:Kc)")])
		queryfunc.rules = rulesParser.getRules()

		self.request.REQUEST = self.queryDict
		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)

		verificationXSD.assertValid(objTree)
		numberElements = objTree.xpath('//xsams:NumberOfVerificationByRule', namespaces={"xsams":XSAMS_NS})
		self.assertEquals(3, len(numberElements))

		numberElements = objTree.xpath('//xsams:NumberOfVerificationByRule[@name = "' + NODEID + 'RuleS01" or @name = "' + NODEID + 'RuleS02"]', namespaces={"xsams":XSAMS_NS})
		self.assertEquals(0, len(numberElements))
		for numberElement in numberElements:
			self.assertEquals("1", numberElement.attrib["correct"])
			self.assertEquals("2", numberElement.attrib["incorrect"])


	def testUseOnlyRules(self):
		rulesParser = RulesParser()
		rulesParser.useRules = set([Rule("nltcsRuleT02", None), Rule(NODEID, "abs(nltcs:J + nltcs:Ka) <= 11")])
		queryfunc.rules = rulesParser.getRules()

		self.request.REQUEST = self.queryDict
		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		verificationXSD.assertValid(objTree)

		numberElements = objTree.xpath('//xsams:NumberOfVerificationByRule', namespaces={"xsams":XSAMS_NS})
		self.assertEquals(3, len(numberElements))


	def testDelRules(self):
		rulesParser = RulesParser()
		rulesParser.delRules = set([Rule("nltcsRuleS01", None), Rule("nltcsRuleT02", None)])
		queryfunc.rules = rulesParser.getRules()

		self.request.REQUEST = self.queryDict
		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		verificationXSD.assertValid(objTree)

		numberElements = objTree.xpath('//xsams:NumberOfVerificationByRule', namespaces={"xsams":XSAMS_NS})
		self.assertEquals(3, len(numberElements))


	def testALL(self):
		settings.DEBUG = DEBUG
		self.queryDict["RETURN"] = 'ALL'
		self.request.REQUEST = self.queryDict
		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		verificationXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/verALL.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def testBAD(self):
		settings.DEBUG = DEBUG
		self.queryDict["RETURN"] = 'BAD'
		self.request.REQUEST = self.queryDict
		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		verificationXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/verBAD.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def testGOOD(self):
		settings.DEBUG = DEBUG
		self.queryDict["RETURN"] = 'GOOD'
		self.request.REQUEST = self.queryDict
		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		verificationXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/verGOOD.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def tearDown(self):
		queryfunc.rules = None
		pass



class TapSyncTest(TestCase):
	prefixURL = "/tap/sync?"
	query = "LANG=VSS2&FORMAT=XSAMS&QUERY="


	def setUp(self):
		data.idCount = 0

		self.request = HttpRequest()
		self.request.META["SERVER_NAME"] = 'localhost'
		self.request.META["SERVER_PORT"] = '80'
		self.request.META["REMOTE_ADDR"] = '127.0.0.1'
		self.request.META["QUERY_STRING"] = self.query

		self.queryDict = toDict(QueryDict(self.query))


	def testNoData(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE RadTransWavelength > 0 AND RadTransWavelength < 0"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		response = views.sync(self.request)
		self.assertEquals(204, response.status_code)
		self.assertEquals('', response.content)


	def testNoDataForHeadRequest(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE RadTransWavelength > 0 AND RadTransWavelength < 0"
		self.queryDict["QUERY"] = sql
		self.request.method = 'HEAD'
		self.request.REQUEST = self.queryDict

		response = views.sync(self.request)
		self.assertEquals(204, response.status_code)
		self.assertEquals('', response.content)


	def testSyncWavelength(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE RadTransWavelength > 0 AND RadTransWavelength < 4000"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		response = views.sync(self.request)
		self.assertEquals(200, response.status_code)

		content = response.content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		xsamsXSD.assertValid(objTree)


	def testSyncWavelengthForHeadRequest(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE RadTransWavelength > 0 AND RadTransWavelength < 4000"
		self.queryDict["QUERY"] = sql
		self.request.method = 'HEAD'
		self.request.REQUEST = self.queryDict

		response = views.sync(self.request)
		headers = response.items()
		headers.pop(1)

		self.assertEquals(200, response.status_code)
		expected_headers = [
			('VAMDC-COUNT-SPECIES', '1'),
			('VAMDC-COUNT-STATES', '133'),
			('Access-Control-Expose-Headers', 'VAMDC-COUNT-SOURCES, VAMDC-COUNT-MOLECULES, VAMDC-COUNT-SPECIES, VAMDC-COUNT-STATES, VAMDC-COUNT-RADIATIVE, VAMDC-TRUNCATED, VAMDC-APPROX-SIZE'),
			('VAMDC-COUNT-MOLECULES', '1'),
			('VAMDC-COUNT-SOURCES', '3'),
			('Access-Control-Allow-Origin', '*'),
			('Last-Modified', 'Thu, 05 Nov 2015 18:00:00 GMT'),
			('VAMDC-APPROX-SIZE', '0.110'),
			('VAMDC-COUNT-RADIATIVE', '168'),
			('Content-Type', 'text/xml'),
			('VAMDC-TRUNCATED', '100')
		]

		self.assertSequenceEqual(expected_headers, headers)
		self.assertEquals('', response.content)


	def testSelectSpecies(self):
		settings.DEBUG = DEBUG
		sql = "SELECT SPECIES"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		# print(actual)
		xsamsXSD.assertValid(objTree)


	def testGetSources(self):
		settings.DEBUG = DEBUG

		transitions = saga4_h2o_1000021.Transition.objects.using('saga4_h2o_1000021').select_related().filter(id_transition_ds=17)
		sources = queryfunc.getSources(transitions)
		if len(sources) == 1:
			self.assertEquals('2', sources[0].getArticleNumber())
			authors = [u'L.S. Rothman',
					   u'D. Jacquemart',
					   u'A. Barbe',
					   u'D.C. Benner',
					   u'M. Birk',
					   u'L.R. Brown',
					   u'M. Carleer',
					   u'C.Chackerian Jr',
					   u'K. Chance',
					   u'L.H. Coudert',
					   u'V. Dana',
					   u'V.M. Devi',
					   u'J.-M. Flaud',
					   u'R.R. Gamache',
					   u'A.Goldman',
					   u'J.-M. Hartmann',
					   u'K.W. Jucks',
					   u'A.G. Maki',
					   u'J.-Y. Mandin',
					   u'S.T. Massie',
					   u'J. Orphal',
					   u'A. Perrin',
					   u'C.P. Rinsland',
					   u'M.A.H. Smith',
					   u'J. Tennyson',
					   u'R.N. Tolchenov',
					   u'R.A. Toth',
					   u'J. Vander Auwera',
					   u'P. Varanasi',
					   u'G. Wagner']
			self.assertEquals(authors, sources[0].getAuthorList())
			self.assertEquals('journal', sources[0].biblioTypeName)
			self.assertRegexpMatches(sources[0].biblioannotation, r" HITRAN ")
			self.assertEquals('10.1016/j.jqsrt.2004.10.008', sources[0].bibliodoi)
			self.assertEquals(931, sources[0].biblioid)
			self.assertEquals('Journal of Quantitative Spectroscopy and Radiation Transfer', sources[0].getSourceName())
			self.assertEquals('139', sources[0].getPageBegin())
			self.assertEquals('204', sources[0].getPageEnd())
			self.assertEquals('The HITRAN 2004 Molecular Spectroscopic Database', sources[0].biblioname)
			self.assertEquals(None, sources[0].bibliourl)
			self.assertEquals('96', sources[0].bibliovolume)
			self.assertEquals(2005, sources[0].biblioyear)
		else:
			self.fail("Sources is empty")


	def testSyncSelectSaga2_co2(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE ((Inchi='InChI=1S/CO2/c2-1-3'  AND RadTransWavenumber > 6503.53 AND RadTransWavenumber < 6503.5736) AND MethodCategory = 'experiment')"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		xsamsXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/co2.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def testSyncSelectSaga2_n2o(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE ((Inchi='InChI=1S/N2O/c1-2-3'  AND RadTransWavenumber > 0.838 AND RadTransWavenumber < 0.839) AND MethodCategory = 'experiment')"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		xsamsXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/n2o.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def testSyncSelectSaga2_c2h2(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE ((Inchi='InChI=1S/C2H2/c1-2/h1-2H'  AND RadTransWavenumber > 615 AND RadTransWavenumber < 615.15) AND MethodCategory = 'experiment')"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		xsamsXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/c2h2.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def testSyncSelectSaga2_nh3(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE ((Inchi='InChI=1S/H3N/h1H3'  AND RadTransWavenumber > 4300 AND RadTransWavenumber < 4301) AND MethodCategory = 'experiment')"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		response = views.sync(self.request)
		self.assertEquals(204, response.status_code)
		self.assertEquals('', response.content)


	def testSyncSelectSaga2_co(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE ((Inchi='InChI=1S/CO/c1-2'  AND RadTransWavenumber > 2135.3135 AND RadTransWavenumber < 2135.3137) AND MethodCategory = 'experiment')"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		xsamsXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/co.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def testSyncSelectMoleculeEnergy(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE StateEnergy > 9895.327 AND StateEnergy < 9895.328"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		# print_all_queries()
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		xsamsXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/Energy.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def testSyncSelectMoleculeH_17OD_W_EC(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE ((Inchi='InChI=1S/H2O/h1H2/i1+1/hD'  AND RadTransWavenumber > 1234.23 AND RadTransWavenumber < 1244.24) AND MethodCategory = 'experiment')"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		xsamsXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/H_17OD_W_EC.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def testSyncSelectMoleculeH_17OD_W_Int(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE ((Inchi='InChI=1S/H2O/h1H2/i1+1/hD'  AND RadTransWavenumber > 1234.23 AND RadTransWavenumber < 1244.24 AND RadTransProbabilityIdealisedIntensity < 1) AND MethodCategory = 'experiment')"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		content = views.sync(self.request).content
		objTree = objectify.fromstring(content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		xsamsXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/H_17OD_W_Int.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def testSyncSelectMoleculeInchiKey(self):
		settings.DEBUG = DEBUG
		sql = "SELECT All WHERE (InchiKey='RWSOTUBLDIXVET-IQRQJSDFSA-N'  AND RadTransWavenumber > 40 AND RadTransWavenumber < 45) OR (Inchi IN ('InChI=1S/H2O/h1H2') AND RadTransWavenumber > 1239.2185 AND RadTransWavenumber < 1239.2191)"
		self.queryDict["QUERY"] = sql
		self.request.REQUEST = self.queryDict

		objTree = objectify.fromstring(views.sync(self.request).content)
		removeSelfSource(objTree)
		actual = etree.tostring(objTree, pretty_print=True)
		xsamsXSD.assertValid(objTree)

		expected = etree.tostring(objectify.fromstring(open(settings.BASE_PATH + "/nodes/" + settings.NODENAME + "/test/InchiKey.xml").read()), pretty_print=True)
		self.assertEquals(expected, actual)


	def testSelectMoleculeInchiKey(self):
		sql = "SELECT+All+WHERE+InchiKey='RWSOTUBLDIXVET-IQRQJSDFSA-N'"
		objTree = objectify.fromstring(testClient.get(self.prefixURL + self.query + sql.strip()).content)
		xsamsXSD.assertValid(objTree)


	def testSelectRadTransWavenumber(self):
		sql = "SELECT+All+WHERE+RadTransWavenumber+>+1239+AND+RadTransWavenumber+<+1240"
		content = testClient.get(self.prefixURL + self.query + sql.strip()).content
		objTree = objectify.fromstring(content)
		try:
			xsamsXSD.assertValid(objTree)
		except:
			print(content)

	def tearDown(self):
		pass



class TransformsTestCase(TestCase):
	def setUp(self):
		pass


	def testInchi2Id(self):
		self.assertEquals(['inner.id_substance', 'in', '(', '1000021', ')'], transforms.inchi2Id('Inchi', 'in', '(', "'InChI=1S/H2O/h1H2'", ')'))

	def testInchiKey2Id(self):
		self.assertEquals(['inner.id_substance', 'in', '(', '1000021', ')'], transforms.inchiKey2Id('Inchi', 'in', '(', "'XLYOFNOQVPJJNP-UHFFFAOYSA-N'", ')'))

	def testMethodCategory2Type(self):
		self.assertEquals(['inner.type', '=', '0'], transforms.methodCategory2Type('MethodCategory', '=', '"theory"'))

	def tearDown(self):
		pass



class SagaModelTestCase(TestCase):
	def setUp(self):
		pass


	def testGetCharge(self):
		self.assertEquals("+1", Substancecorr.objects.get(id_substance=1000529).getCharge())

	def testGetLatexFormula(self):
		substance = Substancecorr.objects.get(id_substance=1000529)
		self.assertEquals("$NO^+$", substance.getLatexFormula())

		substance.plain_name = "_17H12_2O_1plus_1Fe_2minus_2S2I_plus"
		self.assertEquals("$^{17}H_{12}^2O^+Fe^{2-}^2S_2I^+$", substance.getLatexFormula())

	def testGetABCFormula(self):
		substance = Substancecorr.objects.get(id_substance=1000388)
		self.assertEquals("CH2O2", substance.getABCFormula())

		substance.plain_name = "_17H12_2O_1T2_1Fe_2Ti3_2S2F_2plus"
		self.assertEquals("FFeH14OS2Ti3+2", substance.getABCFormula())

	def testGetSubstances(self):
		self.assertEquals("XLYOFNOQVPJJNP-UHFFFAOYSA-N", SubstanceDict.byInchi["InChI=1S/H2O/h1H2"].id_inchi_key)


	def tearDown(self):
		pass



class InchiTestCase(TestCase):
	def setUp(self):
		pass


	def testInchiToInciKey(self):
		self.assertEquals("XLYOFNOQVPJJNP-UHFFFAOYSA-N", inchi.inchiToInchiKey("InChI=1S/H2O/h1H2"))


	def tearDown(self):
		pass



def suite():
	tsuite = unittest.TestSuite()

	tsuite.addTest(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))

	return tsuite
