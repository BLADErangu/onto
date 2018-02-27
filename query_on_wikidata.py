from SPARQLWrapper import SPARQLWrapper, JSON
import pickle
import random
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

class Linked_entity:
    def __init__(self,ltype,loccupation,Id):
        self._Id=Id
        self._occupation = loccupation
        #print('occupation',self._occupation)
        self._type = ltype
        self._dict_path = "data/"
        self._user_props_ids=[]
        self._prop_ids={}
        self._results={}
        self._interest='movie'
        
    def load_dict(self):
        with open(self._dict_path+self._interest+'.txt','rb') as g:
            self._prop_ids = pickle.loads(g.read())

    def get_identity(self,Id):
        Id = Id.split('/')[-1]
        return Id
    def get_literal(self,Id):
        query2=("""
        SELECT ?label WHERE{
        ?work rdfs:label ?label.
        FILTER(LANG(?label) = "en").
        VALUES ?work {wd:"""+Id+"""}}
        """)
        sparql.setQuery(query2)
        sparql.setReturnFormat(JSON)
        result1 = sparql.query().convert()
        return result1['results']['bindings'][0]['label']['value']       
    def get_linked_entity(self,prop):
        #print(self._prop_ids)
        if self._type == 'human':
            self._user_props_ids.append(self._prop_ids[self._occupation])
            query=("""
                PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                SELECT ?entity ?linked_props ?prop ?character_role ?linked_entity WHERE{
                ?entity ?linked_props ?prop.
                ?linked_entity ?linked_props ?prop
                OPTIONAL {?entity p:P161 ?prp.
                            ?prp ps:P161 ?prop.
                            ?prp pq:P453 ?character_role.}
                VALUES ?linked_props {"""+self._user_props_ids[0]+"""}
                VALUES ?prop {"""+str(self._Id)+"""}} ORDER BY DESC(?prop) LIMIT 5""")
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            #print(results)
            with open('data/movie_sol.txt','wb')as s:
                pickle.dump(results,s)

            t = random.randint(0,4)
            self._results['prop'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['prop']['value'])))
            self._results['linked_props'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['linked_props']['value'])))
            self._results['entity'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['entity']['value'])))
            if ('linked_entity') in results['results']['bindings'][t].keys():
                self._results['linked_entity'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['linked_entity']['value'])))
            if ('character_role') in results['results']['bindings'][t].keys():
                self._results['character_role'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['character_role']['value'])))
            return self._results

        elif self._type == 'movie':
            randomly_gen = 0
            if not prop:
                prop.append (random.choice(self._prop_ids.keys()))
                randomly_gen =1
            self._user_props_ids.extend(list(self._prop_ids[i] for i in prop))
            
            query = ("""
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            SELECT ?entity ?linked_props ?prop ?character_role ?linked_entity ?linked_character_role WHERE{
            ?entity ?linked_props ?prop.
            ?linked_entity ?linked_props ?prop
            OPTIONAL {?entity p:P161 ?prp.
                      ?prp ps:P161 ?prop.
                      ?prp pq:P453 ?character_role.
                      ?linked_entity p:P161 ?prp1.
                      ?prp1 ps:P161 ?prop.
                      ?prp1 pq:P453 ?linked_character_role.}
            VALUES ?linked_props{"""+' '.join(self._user_props_ids)+"""}
            VALUES ?entity {"""+str(self._Id)+"""}} ORDER BY DESC(?prop) LIMIT 5""")
                  
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            with open('data/movie_sol.txt','wb')as s:
                pickle.dump(results,s)

            t = random.randint(0,4)
            self._results['linked_entity'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['linked_entity']['value'])))
            self._results['prop'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['prop']['value'])))
            self._results['linked_props'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['linked_props']['value'])))
            self._results['entity'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['entity']['value'])))
            if ('character_role' and 'linked_character_role') in results['results']['bindings'][t].keys():
                self._results['character_role'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['character_role']['value'])))
                self._results['linked_character_role'] = str(self.get_literal(self.get_identity(results['results']['bindings'][t]['linked_character_role']['value'])))
            
            if randomly_gen ==1 :
            	del self._user_props_ids[:]
            	randomly_gen = 0
            
            #print(self._results)
            return self._results
            
        



