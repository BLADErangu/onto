import random 
import sys
sys.path.append('..')
from query_on_wikidata import Linked_entity
from ontologies.wikidata import OntologyManager
from coherence_bot.coherence_bot import random_norepeat

#current version supporting individual links based on movie
# each parent list is a list of type of returns and child list has various templates for each type
driver_templates={
'cast member':[['Oh I really like {}. I really love the performance as {}  in {}. Have you watched {}.'],
				['I agree, that\'s a nice movie. {} was played by {}. He was also starred in {} as {}.']],
'director':['I agree, that\'s a nice movie. Did you know {} was directed by {} who also directed {}. Have you watched the other movie?'],
'producer':['I agree, that\'s a nice movie. Did you know {} was produced by {} who also produced {}. Have you watched the other movie?'],
'genre':['I agree, that\'s a nice movie. Did you know {} was of genre {}. {} is of the same genre. Have you watched the other movie?'],
'main subject':['I agree, that\'s a nice movie. Did you know {}\'s main subject is {}. {} is also on the sae subject. Have you watched the other movie?'],


}

# hbuman entity prop linked entity

# oh i really like this {actor}. i really love the performance of the actor in the movie {}

class Driver_temp:
	def __init__(self,type=None ,occupation=None,id=None):
		self.type = type
		self.id = id
		self.occupation = occupation
		self.result = Linked_entity(ltype= self.type,loccupation=self.occupation,Id=self.id)
		self.result.load_dict()

		self.linked_results = {}

	def fill_template(self,link):
		self.linked_results = self.result.get_linked_entity(link)
		#print(self.linked_results)
		if  ('character_role' and 'linked_character_role') in self.linked_results.keys():
			template = driver_templates[self.linked_results['linked_props']][1][0].format(\
			self.linked_results['character_role'],
			self.linked_results['prop'],
			self.linked_results['linked_entity'],
			self.linked_results['linked_character_role'])
		elif ('linked_entity') in self.linked_results.keys():
			template = driver_templates[self.linked_results['linked_props']][0].format(\
			self.linked_results['entity'],
			self.linked_results['prop'],
			self.linked_results['linked_entity'])
		elif self.type == 'human':
			if  ('character_role') in self.linked_results.keys():
				template = driver_templates[self.linked_results['linked_props']][0][0].format(\
				self.linked_results['prop'],
				self.linked_results['character_role'],
				self.linked_results['entity'],
				self.linked_results['entity'])
			else:
				template = driver_templates[self.linked_results['linked_props']][0].format(\
				self.linked_results['entity'],
				self.linked_results['prop'],
				self.linked_results['linked_entity'])


		print(self.linked_results)
		print(template)
		#return template
	def send_out(self,link):
		template = []
		self.linked_results = self.result.get_linked_entity(link)
		if  ('character_role' and 'linked_character_role') in self.linked_results.keys():
			temp = driver_templates[self.linked_results['linked_props']][1][0]
			vals = [self.linked_results['character_role'],
			self.linked_results['prop'],
			self.linked_results['linked_entity'],
			self.linked_results['linked_character_role']]
			template.append(temp)
			template.append(vals)

		elif ('linked_entity') in self.linked_results.keys():
			temp = driver_templates[self.linked_results['linked_props']][0]
			vals = [self.linked_results['entity'],
			self.linked_results['prop'],
			self.linked_results['linked_entity']]
			template.append(temp)
			template.append(vals)
		elif self.type == 'human':
			if  ('character_role') in self.linked_results.keys():
				temp = driver_templates[self.linked_results['linked_props']][0][0]
				vals = [self.linked_results['prop'],
				self.linked_results['character_role'],
				self.linked_results['entity'],
				self.linked_results['entity']]
				template.append(temp)
				template.append(vals)
			else:
				temp = driver_templates[self.linked_results['linked_props']][0]
				vals = [self.linked_results['entity'],
				self.linked_results['prop'],
				self.linked_results['linked_entity']]
				template.append(temp)
				template.append(vals)


		#print(self.linked_results)
		print(template)
		return template
		




# {nb_turn :[type,identifier,occupation]}
# type='movie',id ='<http://www.wikidata.org/entity/Q184843>'
# type='human',id ='<http://www.wikidata.org/entity/Q81328>', occupation='actor'

x = Driver_temp(type='movie',id ='<http://www.wikidata.org/entity/Q184843>')
x.send_out(['actor'])