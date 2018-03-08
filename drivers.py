import sys

from ontologies import wikidata

sys.path.append('..')

# current version supporting individual links based on movie
# each parent list is a list of type of returns and child list has various templates for each type
_driver_templates = {'released': {
    'cast member': [['Oh I really like {}. I really love the performance as {} in the {} movie {}. What do you think about {}.'],
                    ['I agree, that\'s a nice movie. {} was played by {}. He was also starred in the {} {} as {}.']],
    'director': [
        'I agree, that\'s a nice movie. Did you know {} was directed by {} who also directed {}. What do you think about the other movie?'],
    'producer': [
        'I agree, that\'s a nice movie. Did you know {} was produced by {} who also produced {}. What do you think about the other movie?'],
    'genre': [
        'I agree, that\'s a nice movie. Did you know {} was of genre {}. {} is of the same genre. What do you think about the other movie?'],
    'main subject': [
        'I agree, that\'s a nice movie. Did you know {}\'s main subject is {}. {} is also on the sae subject. What do you think about the other movie?'],
    },

                     'not_released': {'cast member': [[
                                                          'Oh I really like {}. I really love the performance as {}  in {}. What do you think about {}?'],
                                                      [
                                                          'I agree, that\'s a nice movie. {} was played by {}. He is also starring in {} as {}.']],
                                      'director': [
                                          'I agree, that\'s a nice movie. Did you know {} was directed by {} who also directed {}. What do you think about the other movie?'],
    'producer': [
        'I agree, that\'s a nice movie. Did you know {} was produced by {} who also produced {}. What do you think about the other movie?'],
    'genre': [
        'I agree, that\'s a nice movie. Did you know {} was of genre {}. {} is of the same genre. What do you think about the other movie?'],
    'main subject': [
        'I agree, that\'s a nice movie. Did you know {}\'s main subject is {}. {} is also on the same subject. What do you think about the other movie?']}
                     }


# hbuman entity prop linked entity

# oh i really like this {actor}. i really love the performance of the actor in the movie {}

class DriversGenerator:
    def fill_template(self, results):
        template = None

        if 'ent_rel_date' in results.keys():
            driver_templates = _driver_templates['released']
            time1 = results['ent_rel_date'][-1]
            if 'l_ent_rel_date' in results.keys():
                time2 = results['l_ent_rel_date'][-1]
        else:
            driver_templates = _driver_templates['not_released']

        if results["type"] == wikidata.human_type:

            if 'character_role' in results.keys():
                template = driver_templates[results['linked_props']['label']][0][0].format(
                    results['prop']['label'],
                    results['character_role']['label'],
                    time1,
                    results['entity']['label'],
                    results['entity']['label'])
            else:
                template = driver_templates[results['linked_props']['label']][1][0].format(
                    results['entity']['label'],
                    results['prop']['label'],
                    results['linked_entity']['label'])
        elif ('character_role' and 'linked_character_role') in results.keys():
            template = driver_templates[results['linked_props']['label']][0][0].format(
                results['character_role']['label'],
                results['prop']['label'],
                time2,
                results['linked_entity']['label'],
                results['linked_character_role']['label'])
        elif 'linked_entity' in results.keys():
            template = driver_templates[results['linked_props']['label']][1][0].format(
                results['entity']['label'],
                results['prop']['label'],
                results['linked_entity']['label'])
        return template
