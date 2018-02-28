import random 
from query_on_wikidata import Linked_entity

#current version supporting individual links based on movie

driver_templates={
'actor':[],
'director':[],
'producer':[],
'genre':[],
'main subject':[]	
}

class Driver_temp:
	def __init__(self,interest=None,id=None):
		self.interest = interest
		if not self.interest:
			self.interest = 'movie'
		self.id = id
		self.result = Linked_entity(self.interest,self.id)
		self.result.load_dict()
		self.linked_results = {}

	def fill_template(self,link):
		self.linked_results = self.result.get_linked_entity(link)
		print(sel.linked_results)

x = Driver_temp('movie','<http://www.wikidata.org/entity/Q184843>')
x.fill_template(['director'])