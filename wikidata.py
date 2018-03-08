import datetime
import random

import requests
from SPARQLWrapper import JSON
from SPARQLWrapper import SPARQLWrapper
from nltk import defaultdict
from rdflib import ConjunctiveGraph
from rdflib import Literal
from rdflib import URIRef
from requests import ConnectionError

from ontologies import conf

# tagme.GCUBE_TOKEN = conf.wiki_linker_conf["tagme_token"]
# RHO_PARAM = 0.4

movie_type = "wd:Q11424"

movie_domain_properties = {
    "instance of": "wdt:P31",
    "director": "wdt:P57",
    "screenwriter": "wdt:P58",
    "producer": "wdt:P162",  # producer
    "cast member": "wdt:P161",  # cast member
    "director of photography": "wdt:P344",  # director of photography
    "production company": "wdt:P272",  # production company
    "genre": "wdt:P136",  # genre
    "main subject": "wdt:P921",  # main subject
    "narrative location": "wdt:P840",  # narrative location
    "pubblication date": "wdt:P577",  # publication date
    "contry of origin": "wdt:P495",  # country of origin
    "original language of work": "wdt:P364",  # original language of work
    "award received": "wdt:P166",  # award received
    "film editor": "wdt:P1040",  # film editor
    "composer": "wdt:P86",  # composer
    "nominated for": "wdt:P1411",  # nominated for
    "color": "wdt:P462",  # color
    "duration": "wdt:P2047",  # duration
    "based on": "wdt:P144",  # based on
    "filming location": "wdt:P915",  # filming location
    "set in period": "wdt:P2408",  # set in period
    "distributor": "wdt:P750",  # distributor
    "inspired by": "wdt:P941",  # inspired by
    "series": "wdt:P179",  # series,
    "occupation": "wdt:P106"
}

movie_domain_types = {
    "film actor": "wd:Q10800557",
    "film director": "wd:Q2526255",
    "screenwriter": "wd:Q28389",
    "actor": "wd:Q33999",
    "movie": "wd:Q11424"
}

human_type = "wd:Q5"

movie_properties = [
    "wdt:P31",  # instance of
    "wdt:P57",  # director
    "wdt:P58",  # screenwriter
    "wdt:P162",  # producer
    "wdt:P161",  # cast member
    "wdt:P344",  # director of photography
    "wdt:P272",  # production company
    "wdt:P136",  # genre
    "wdt:P921",  # main subject
    "wdt:P840",  # narrative location
    "wdt:P577",  # publication date
    "wdt:P495",  # country of origin
    "wdt:P364",  # original language of work
    "wdt:P166",  # award received
    "wdt:P1040",  # film editor
    "wdt:P86",  # composer
    "wdt:P1411",  # nominated for
    "wdt:P462",  # color
    "wdt:P2047",  # duration
    "wdt:P144",  # based on
    "wdt:P915",  # filming location
    "wdt:P2408",  # set in period
    "wdt:P750",  # distributor
    "wdt:P941",  # inspired by
    "wdt:P179",  # series
]
prefixes = {
    "http://www.wikidata.org/entity/": "wd",
    "http://www.wikidata.org/prop/direct/": "wdt",
}

RETRIEVE_WIKIDATA_URI_QUERY = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?wikidata_uri WHERE {
?s foaf:isPrimaryTopicOf <%s>;
   owl:sameAs ?wikidata_uri
   FILTER(REGEX(?wikidata_uri, "^http://www.wikidata.org"))
}
"""

RETRIEVE_ITEM_PROPERTIES_QUERY = """
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wd: <http://www.wikidata.org/entity/>

        SELECT ?s ?p ?o WHERE {
            {
                ?s wdt:P31 ?type.
                ?type wdt:P279 ?t1.
                ?t1 wdt:P279 ?t2.
                ?t2 wdt:P279 ?t3.
                ?t3 wdt:P279 %s.
            }
            UNION
            {
                ?s wdt:P31 ?type.
                ?type wdt:P279 ?t1.
                ?t1 wdt:P279 ?t2.
                ?t2 wdt:P279 %s.
            }
            UNION
            {
                ?s wdt:P31 ?type.
                ?type wdt:P279 ?t.
                ?t wdt:P279 %s.
            }
            UNION
            {
                ?s wdt:P31 ?type.
                ?type wdt:P279 %s.
            }
            UNION
            {
                ?s wdt:P31 %s.
            }
            VALUES ?p {%s}
            ?s ?p ?o.
        }
        """


def build_item_data_graph(item_type, item_properties, item_data_graph_path, endpoint_url, max_num_objects, create=True):
    item_data_graph = ConjunctiveGraph("Sleepycat")

    item_data_graph.open(item_data_graph_path, create=create)

    for item_property in item_properties:
        item_data_query = RETRIEVE_ITEM_PROPERTIES_QUERY % (
            item_type, item_type, item_type, item_type, item_type, item_property)
        sparql_client = SPARQLWrapper(endpoint_url, returnFormat=JSON)
        sparql_client.setTimeout(604800)
        sparql_client.setQuery(item_data_query)
        results = sparql_client.queryAndConvert()
        num_bindings = len(results["results"]["bindings"])
        added_triples = defaultdict(lambda: defaultdict(lambda: 0))
        for i, binding in enumerate(results["results"]["bindings"]):
            print("[{}/{}]".format(i + 1, num_bindings))
            subject = URIRef(binding["s"]["value"])
            predicate = URIRef(binding["p"]["value"])
            if binding["o"]["type"] == "literal":
                object = Literal(binding["o"]["value"], datatype=binding["o"]["datatype"])
            else:
                object = URIRef(binding["o"]["value"])
            if max_num_objects is not None:
                if added_triples[subject][predicate] < max_num_objects:
                    triple = (subject, predicate, object)
                    added_triples[subject][predicate] += 1
                    item_data_graph.add(triple)
            else:
                triple = (subject, predicate, object)
                item_data_graph.add(triple)

    item_data_graph.close()


class EntityLinker:
    def get_entity_mentions(self, utterance, context):
        try:
            annotations = requests.post(
                conf.wiki_linker_conf["linker_endpoint"],
                json={
                    "text": utterance,
                    "properties": conf.wiki_linker_conf["properties_filter"]
                })

            if annotations.status_code != 200:
                raise ValueError(
                    "[Entity Linker]: Status code %d\n"
                    "Something wrong happened. Check the status of the entity linking server and its endpoint." %
                    annotations.status_code)
            annotations = annotations.json()
        except ConnectionError:
            return {}

        return self._refine_annotations(annotations)

    def _replace_with_prefixes(self, span_annotations):
        rep_span_annotations = []

        for annotation in span_annotations:
            annotation["entityLink"].update({
                "identifier": get_prefixed_identifier(annotation["entityLink"]["identifier"]),
                "types": [get_prefixed_identifier(t) for t in annotation["entityLink"]["types"]],
                "properties": {get_prefixed_identifier(p):
                                   [get_prefixed_identifier(pi) for pi in annotation["entityLink"]["properties"][p]] for
                               p
                               in annotation["entityLink"]["properties"]}
            })

            rep_span_annotations.append(annotation)

        return rep_span_annotations

    # TODO: apply profanity filter on entity mentions
    def _refine_annotations(self, annotations):
        refined_annotations = {}

        for span_text in annotations:
            span_annotations = filter(lambda a: a["score"] > conf.wiki_linker_conf["annotation_threshold"],
                                      annotations[span_text])

            if span_annotations:
                refined_annotations[span_text] = self._replace_with_prefixes(span_annotations)

        return refined_annotations


def get_prefixed_identifier(input_str):
    index = input_str.rfind("/") + 1
    prefix_str = input_str[:index]
    prefix = prefixes[prefix_str]
    identifier = input_str[index:]

    return "{}:{}".format(prefix, identifier)


class OntologyManager:
    def __init__(self):
        self._sparql_client = SPARQLWrapper(conf.ontology_conf["endpoint"], returnFormat=JSON)

    @staticmethod
    def get_entity_type_query():
        return """
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX wd: <http://www.wikidata.org/entity/>

            SELECT ?type WHERE {
                %s wdt:P31 ?type
            }
        """

    @staticmethod
    def get_entity_prop_values():
        return """
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?obj_label WHERE {
            %s %s ?obj.
            ?obj rdfs:label ?obj_label
            FILTER (LANG(?obj_label) = "en")
        }
        """

    @staticmethod
    def get_entity_description():
        return """
            PREFIX schema: <http://schema.org/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX wd: <http://www.wikidata.org/entity/>

            SELECT ?description WHERE {
                %s schema:description ?description
                FILTER (LANG(?description) = "en")
            }
            """

    def get_literal(self, entity):
        if "http://" in entity:
            entity = get_prefixed_identifier(entity)
        # property identifier
        # we need to reference the corresponding entity associated to the property
        # in order to get the label
        if "wdt" in entity:
            entity = entity.replace("wdt", "wd")

        query = ("""
        SELECT ?label WHERE{
        %s rdfs:label ?label.
        FILTER(LANG(?label) = "en").
        }
        """ % entity)
        self._sparql_client.setQuery(query)
        self._sparql_client.setReturnFormat(JSON)
        result = self._sparql_client.query().convert()
        return result['results']['bindings'][0]['label']['value']

    def is_released(self, Id):
        now = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d"), '%Y-%m-%d')
        Y_m_d_Id = datetime.datetime.strptime(Id, '%Y-%m-%d')
        Y_m_d_Id.strftime("%Y-%m-%d")
        s = int(str(now - Y_m_d_Id).split('days')[0])
        if s>=0:
            r = 'released'
            if s>=1500:i='old'
            if (s<1500)and(s>=300): i='recent'
            if s<300: i ='new'
        else:
            r,i = 'not_released', 'upcoming'           
        return [Id,r,i]

    def get_linked_entity(self, entity):
        entity_types = entity["entityLink"]["types"]
        entity_uri = entity["entityLink"]["identifier"]
        # Human type
        if human_type in entity_types:

            query = ("""
                PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                PREFIX wd: <http://www.wikidata.org/entity/>
                
                SELECT ?entity ?linked_props ?prop ?character_role ?linked_entity ?ent_rel_date WHERE{
                ?entity ?linked_props ?prop.
                ?linked_entity ?linked_props ?prop.
                OPTIONAL {?entity p:P161 ?prp.
                            ?prp ps:P161 ?prop.
                            ?prp pq:P453 ?character_role.
                }
                OPTIONAL { ?entity wdt:P577 ?ent_rel_date}
                VALUES ?linked_props { %s }
                VALUES ?prop { %s }} ORDER BY DESC(?ent_rel_date) LIMIT 5"""
                     % (" ".join(movie_properties), entity_uri))
            self._sparql_client.setQuery(query)
            self._sparql_client.setReturnFormat(JSON)
            results = self._sparql_client.query().convert()

            t = random.randint(0, 4)
            linked_entity_data = {}
            linked_entity_data['prop'],linked_entity_data['linked_props'],linked_entity_data['entity']={},{},{}
            linked_entity_data['prop']['label'] = str(self.get_literal(results['results']['bindings'][t]['prop']['value']))
            linked_entity_data['prop']['identifier'] = results['results']['bindings'][t]['prop']['value']
            linked_entity_data['linked_props']['label'] = str(self.get_literal(results['results']['bindings'][t]['linked_props']['value']))
            linked_entity_data['linked_props']['identifier'] = results['results']['bindings'][t]['linked_props']['value']
            linked_entity_data['entity']['label'] = str(self.get_literal(results['results']['bindings'][t]['entity']['value']))
            linked_entity_data['entity']['identifier'] = results['results']['bindings'][t]['entity']['value']
            if ('linked_entity') in results['results']['bindings'][t].keys():
                linked_entity_data['linked_entity']={}
                linked_entity_data['linked_entity']['label'] = str(self.get_literal(results['results']['bindings'][t]['linked_entity']['value']))
                linked_entity_data['linked_entity']['identifier'] = results['results']['bindings'][t]['linked_entity']['value']
            if ('character_role') in results['results']['bindings'][t].keys():
                linked_entity_data['character_role']={}
                linked_entity_data['character_role']['label'] = str(self.get_literal(results['results']['bindings'][t]['character_role']['value']))
                linked_entity_data['character_role']['identifier'] = results['results']['bindings'][t]['character_role']['value']
            if ('ent_rel_date') in results['results']['bindings'][t].keys():
                linked_entity_data['ent_rel_date'] = self.is_released(str(results['results']['bindings'][t]['ent_rel_date']['value']).split('T')[0])
            return linked_entity_data

        # Movie type
        elif movie_type in entity_types:
            query = ("""
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            SELECT ?entity ?linked_props ?prop ?character_role ?linked_entity ?linked_character_role ?ent_rel_date ?l_ent_rel_date WHERE{
            ?entity ?linked_props ?prop.
            ?linked_entity ?linked_props ?prop
            OPTIONAL {?entity p:P161 ?prp.
                      ?prp ps:P161 ?prop.
                      ?prp pq:P453 ?character_role.
                      ?linked_entity p:P161 ?prp1.
                      ?prp1 ps:P161 ?prop.
                      ?prp1 pq:P453 ?linked_character_role.}
            OPTIONAL { ?entity wdt:P577 ?ent_rel_date.}
            OPTIONAL {?linked_entity wdt:P577 ?l_ent_rel_date.}
            VALUES ?linked_props{ %s }
            VALUES ?entity { %s }} ORDER BY DESC(?l_ent_rel_date) LIMIT 5""" %
                     (" ".join(movie_properties), entity_uri))

            self._sparql_client.setQuery(query)
            self._sparql_client.setReturnFormat(JSON)
            results = self._sparql_client.query().convert()

            t = random.randint(0, 4)
            linked_entity_data = {}
            linked_entity_data['prop'],linked_entity_data['linked_props'],linked_entity_data['entity'],linked_entity_data['linked_entity']={},{},{},{}
            linked_entity_data['linked_entity']['label'] = str(self.get_literal(results['results']['bindings'][t]['linked_entity']['value']))
            linked_entity_data['linked_entity']['identifier'] = results['results']['bindings'][t]['linked_entity']['value']
            linked_entity_data['prop']['label'] = str(self.get_literal(results['results']['bindings'][t]['prop']['value']))
            linked_entity_data['prop']['identifier'] = results['results']['bindings'][t]['prop']['value']
            linked_entity_data['linked_props']['label'] = str(self.get_literal(results['results']['bindings'][t]['linked_props']['value']))
            linked_entity_data['linked_props']['identifier'] = results['results']['bindings'][t]['linked_props']['value']
            linked_entity_data['entity']['label'] = str(self.get_literal(results['results']['bindings'][t]['entity']['value']))
            linked_entity_data['entity']['identifier'] = results['results']['bindings'][t]['entity']['value']
            if ('character_role' and 'linked_character_role') in results['results']['bindings'][t].keys():
                linked_entity_data['character_role'],linked_entity_data['linked_character_role']={},{}
                linked_entity_data['character_role']['label'] = str(self.get_literal(results['results']['bindings'][t]['character_role']['value']))
                linked_entity_data['character_role']['identifier'] = results['results']['bindings'][t]['character_role']['value']
                linked_entity_data['linked_character_role']['label'] = str(self.get_literal(results['results']['bindings'][t]['linked_character_role']['value']))
                linked_entity_data['linked_character_role']['identifier'] = results['results']['bindings'][t]['linked_character_role']['value']
            if 'ent_rel_date' in results['results']['bindings'][t].keys():
                linked_entity_data['ent_rel_date'] = self.is_released(str(results['results']['bindings'][t]['ent_rel_date']['value']).split('T')[0])
            if 'l_ent_rel_date' in results['results']['bindings'][t].keys():
                linked_entity_data['l_ent_rel_date'] = self.is_released(str(results['results']['bindings'][t]['l_ent_rel_date']['value']).split('T')[0])

            return linked_entity_data

    def query(self, query):
        self._sparql_client.setQuery(query)

        results = self._sparql_client.queryAndConvert()

        if "bindings" in results["results"]:
            return results["results"]["bindings"]
        return None
