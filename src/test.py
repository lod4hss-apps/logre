from model import Endpoint, OntoEntity

import json, yaml

# ENDPOINT set up
name = "gm_allegrograph"
url = "https://ag1k3x48w8r6fq56.allegrograph.cloud/repositories/gaetanmuck"
technology = "Allegrograph"
username = "admin"
password = "vIZnRN5xGbAHD98XaVfD1t"
base_uri = "http://geovistory.org/information/"


endpoint = Endpoint(technology, name, url, username, password, base_uri)
graph_data_uri = "base:british_royal_family"
graph_ontology_uri = "base:shacl"
graph_metadata_uri = "base:british_royal_bloodline_metadata"
endpoint.add_data_set("British Royal Bloodline", graph_data_uri, graph_ontology_uri, graph_metadata_uri, 'SHACL')
endpoint.sparql.add_prefix('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
endpoint.sparql.add_prefix('rdfs', 'http://www.w3.org/2000/01/rdf-schema#')
endpoint.sparql.add_prefix('sh', 'http://www.w3.org/ns/shacl#')
endpoint.sparql.add_prefix('xsd', 'http://www.w3.org/2001/XMLSchema#')
endpoint.sparql.add_prefix('owl', 'http://www.w3.org/2002/07/owl#')
endpoint.sparql.add_prefix('crm', 'http://www.cidoc-crm.org/cidoc-crm/')
endpoint.sparql.add_prefix('sdh', 'https://sdhss.org/ontology/core/')
endpoint.sparql.add_prefix('sdh-shortcut', 'https://sdhss.org/ontology/shortcuts/')
endpoint.sparql.add_prefix('sdh', 'https://sdhss.org/ontology/core/')
endpoint.sparql.add_prefix('sdh-shacl', 'https://sdhss.org/shacl/profiles/')
endpoint.sparql.add_prefix('ontome', 'https://ontome.net/ontology/')


endpoint_dict = endpoint.to_dict()
file = open('./logre-config.yaml', 'w')
file.write(yaml.dump(endpoint_dict, sort_keys=False))
file.close()
# print(yaml.dump(endpoint_dict, sort_keys=False))
# print(json.dumps(endpoint_dict, indent=4))
# endpoint = Endpoint.from_dict(endpoint_dict)

# data_set = endpoint.data_sets[0]

# # Basic query
# answer = endpoint.sparql.run("""
#     # Test script                             
#     select 
#         distinct ?g
#     where {  
#         graph ?g {
#         ?s ?p ?o . 
#     } }
#     limit 5                         
# """)
# print(answer)


# # Explore data_sets
# for data_set in endpoint.data_sets:

#     print(f'DataSet {data_set.name} counts: ')
#     print(data_set.count_triples())
    
#     print(f'DataSet {data_set.name} classes: ')
#     [print(obj.to_dict()) for obj in data_set.ontology.get_classes()]

#     print(f'DataSet {data_set.name} properties: ')
#     [print(obj.to_dict()) for obj in data_set.ontology.get_properties()]


# research_answer = endpoint.data_sets[0].find_entities('alb', 'crm:E21')
# [print(answer.to_dict()) for answer in research_answer]


# entity = data_set.find_entities('elis', 'crm:E21')[0]
# print(json.dumps(entity.to_dict(), indent=4))

# outgoings = data_set.get_outgoing_statements(entity)
# for outgoing in outgoings:
#     print(f"SUBJECT: {json.dumps(outgoing.subject.to_dict(), indent=4)}")
#     print(f"PREDICATE: {json.dumps(outgoing.predicate.to_dict(), indent=4)}")
#     print(f"OBJECT: {json.dumps(outgoing.object.to_dict(), indent=4)}")
#     print('------')


# incomings = data_set.get_incoming_statements(entity)
# for incoming in incomings:
#     print(f"SUBJECT: {json.dumps(incoming.subject.to_dict(), indent=4)}")
#     print(f"PREDICATE: {json.dumps(incoming.predicate.to_dict(), indent=4)}")
#     print(f"OBJECT: {json.dumps(incoming.object.to_dict(), indent=4)}")
#     print('------')


# card = data_set.get_card(entity)
# [print(json.dumps(stmt.to_dict(), indent=4)) for stmt in card]

# CRM_E21 = OntoEntity('crm:E21', 'Person')
# df = data_set.download_class(CRM_E21)
# print(df)

# content = data_set.download_graph_turtle('data')
# print(content)

# # CRM_E21 = OntoEntity('crm:E21', 'Person')
# data_table = data_set.get_data_table(CRM_E21, limit=10)
# count = data_set.get_class_count(CRM_E21)
# print(data_table)
# print('COUNT:', count)


# print(json.dumps(data_set.get_entity_infos('base:inS0qxne').to_dict(), indent=4))
