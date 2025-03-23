from typing import Dict, List
import streamlit as st
import pandas as pd
from schema import Graph, OntologyFramework, Entity
from schema import DisplayTriple, Ontology, OntologyClass
from lib.sparql_base import query
from lib.utils import ensure_uri, to_snake_case
from lib.sparql_noframework import get_noframework_ontology
from lib.sparql_shacl import get_shacl_ontology
from lib.prefixes import get_prefixes_str
import lib.state as state


@st.cache_data(show_spinner=False, ttl='1 day')
def list_graphs() -> List[Graph]:
    """List all graphs available in the SPARQL endpoint."""

    # Prepare the query
    text = """
        SELECT DISTINCT
            ?uri 
            (COALESCE(?label_, ?uri) as ?label)
            (COALESCE(?comment_, '') as ?comment)
        WHERE {
            GRAPH ?uri { ?s ?p ?o . }
            optional { ?uri rdfs:label ?label_ . }
            optional { ?uri rdfs:comment ?comment_ . }
        }
    """    

    # Execute the query
    with st.spinner("Listing all graphs..."):
        response = query(text, caller='sparql_queries.list_graphs')
    
    # Transform list of objects into list of graphs
    if response: return list(map(lambda obj: Graph.from_dict(obj), response))
    # And ensure a list is returned
    else: return []


def count_graph_triples(graph: Graph) -> int:
    """Count how much triples there is in the selected dataset/graph"""

    # Make sure the given graph is a valid URI
    graph_uri = ensure_uri(graph.uri)

    # Prepare the query
    select = "SELECT (COUNT(*) as ?count)"
    where_begin = "WHERE {"
    where_end = "}"
    graph_begin = "GRAPH " + graph_uri + "{" if graph_uri else ''
    graph_end = "}" if graph_uri else ''
    triples = "?s ?p ?o."

    # Build the query
    text = f"""
    {select}
    {where_begin}
        {graph_begin}
            {triples}
        {graph_end}
    {where_end}
    """

    # Execute the query
    with st.spinner(f'Counting triples in {graph.label}...'):
        response = query(text)

    # Make sure a number is answered
    if not response: return 0
    return int(response[0]['count'])


@st.cache_data(show_spinner=False, ttl='1 day')
def get_ontology() -> Ontology:
    """Depending on the endpoint configuration, fetch the right ontology."""

    # From state
    framework = state.get_endpoint().ontology_framework

    # For some reason, sometimes, especially on hot reload, Enums are lost.
    # Maybe its my fault, by I can't find the reason why after some clicking around, the enums are lost
    # This is the way I found to make it work every time
    if framework == OntologyFramework.SHACL or framework == OntologyFramework.SHACL.value:
        with st.spinner('Fetching SHACL ontology...'):
            ontology = get_shacl_ontology()
    else:
        with st.spinner('Fetching used ontology...'):
            ontology = get_noframework_ontology()
    
    return ontology
    

@st.cache_data(show_spinner=False, ttl='30 seconds', hash_funcs={Graph: lambda graph: graph.uri})
def find_entities(graph: Graph = None, label_filter: str = None, class_filter: str = None, limit: int = None) -> List[Entity]:
    """
    Fetch the list of entities on the endpoint with:
    Args:
        label (str): the text that should be included in entity's rdfs:label. If None, fetch all entities.
        cls (str): entity's class. Filter by the given class, if specified
        limit (int): max number of retrived entities. If None, no limit is applied
    """

    # Make sure the given class is a valid URI
    class_uri = ensure_uri(class_filter)

    # Prepare query
    text = """
        SELECT
            (?uri_ as ?uri)
            (COALESCE(?label_, '') as ?label)
            (COALESCE(?comment_, '') as ?comment)
            (COALESCE(?class_uri_, '""" + (class_uri if class_uri else "No Class URI")  + """') as ?class_uri)
        WHERE {
            """ + ("GRAPH " + ensure_uri(graph.uri) + " {" if graph.uri else "") + """
                ?uri_ a """ + (class_uri if class_uri else "?class_uri_")  + """ .
                OPTIONAL { ?uri_ rdfs:label ?label_ . }
                OPTIONAL { ?uri_ rdfs:comment ?comment_ . }
            """ + ("}" if graph.uri else "") + """
            """ + (f"FILTER(CONTAINS(LCASE(?label_), '{label_filter.lower()}')) ." if label_filter else "") + """
        }
        """ + (f"LIMIT {limit}" if limit else "") + """
    """


    # Execute query
    with st.spinner(f"Looking for entities in graph {graph.label}"):
        response = query(text)

    # If there is no result, there is no point to go forward
    if not response: 
        return []

    # For each retrieved entity, look for the class label in the ontology, 
    # then transform into instances of "Entity"
    ontology = get_ontology()
    classes = list(map(lambda cls: {**cls, 'class_label': ontology.get_class_name(cls['class_uri'])}, response))
    entities = list(map(lambda cls: Entity.from_dict(cls), classes))
    
    return entities


@st.cache_data(show_spinner=False, ttl='30 seconds', hash_funcs={Graph: lambda graph: graph.uri, Entity: lambda ent: ent.uri})
def get_entity_card(entity: Entity, graph: Graph = None) -> List[DisplayTriple]:
    """Fetch all relevant triples (according to the ontology) from the given graph about the given entity."""

    # In case the entity is a blank node, do nothing
    if entity.is_blank:
        st.error('Can not fetch triples from a blank node')
        return []
    
    # Make sure the given entity is a valid URI
    entity_uri = ensure_uri(entity.uri)
    graph_uri = ensure_uri(graph.uri)

    # Fetch only the wanted properties (those that are listed in the SHACL file)
    ontology = get_ontology()
    classes_dict = ontology.get_classes_named_dict()
    properties_dict = ontology.get_properties_named_dict()
    wanted_properties = [ensure_uri(prop.uri) for prop in ontology.properties if prop.card_of_class_uri == entity.class_uri]

    # Prepare the query (Outgoing properties)
    text = """
        SELECT DISTINCT
            ('""" + entity_uri + """' as ?subject_uri)
            ('""" + entity.label.replace("'", "\\'") + """' as ?subject_label)
            ('""" + entity.class_uri + """' as ?subject_class_uri)
            ('""" + (entity.comment.replace("'", "\\'") or '') + """' as ?subject_comment)
            ('false' as ?subject_is_blank)
            ?predicate_uri
            ?object_uri
            (COALESCE(?object_label_, '') as ?object_label)
            (COALESCE(?object_class_uri_, '') as ?object_class_uri)
            (COALESCE(?object_comment_, '') as ?object_comment)
            (isLiteral(?object_uri) as ?object_is_literal)
            (isBlank(?object_uri) as ?object_is_blank)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                """ + entity_uri + """ ?predicate_uri ?object_uri . 
                OPTIONAL { ?object_uri rdfs:label ?object_label_ . }
                OPTIONAL { ?object_uri a ?object_class_uri_ . }
                OPTIONAL { ?object_uri rdfs:comment ?object_comment_ . }
                VALUES ?predicate_uri { """ + ' '.join(wanted_properties) + """ }
            """ + ("}" if graph_uri else "") + """
        }
    """

    # Execute the request (Outgoing properties)
    with st.spinner(f"Fetching entity card (outgoing triples) from graph {graph.label}..."):
        outgoing_props = query(text)

    # Prepare que query (Incoming properties)
    text = """
        SELECT DISTINCT
            ?subject_uri
            (COALESCE(?subject_label_, '') as ?subject_label)
            (COALESCE(?subject_class_uri_, '') as ?subject_class_uri)
            (COALESCE(?subject_comment_, '') as ?subject_comment)
            ?predicate_uri
            ('""" + entity.uri + """' as ?object_uri)
            ('""" + entity.label.replace("'", "\\'") + """' as ?object_label)
            ('""" + entity.class_uri + """' as ?object_class_uri)
            ('""" + (entity.comment.replace("'", "\\'") or '') + """' as ?object_comment)
            ('false' as ?object_is_literal)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                ?subject_uri ?predicate_uri """ + entity_uri + """ . 
                ?subject_uri rdfs:label ?subject_label_ .
                OPTIONAL { ?subject_uri a ?subject_class_uri_ . }
                OPTIONAL { ?subject_uri rdfs:comment ?subject_comment_ . }
                VALUES ?predicate_uri { """ + ' '.join(wanted_properties) + """ }
            """ + ("}" if graph_uri else "") + """
        }
    """

    # Execute the request (Incoming properties)
    with st.spinner(f"Fetching entity card (incoming triples) from graph {graph.label}..."):
        incoming_props = query(text)


    # Merge the data (left joins). We have to do it 2 times, once for the incomings, and once for the outgoings:
    # Because for the incoming we want to fetch the label of the right class vision of the property
    # For outgoing
    display_triples_list_outgoing = [{
        # Get attributes from left list
        **triple, 
        # Merge the information about the subject class from the ontology (first right list)
        **({f"subject_class_{k}": v for k, v in classes_dict.get(triple["subject_class_uri"], {}).items()} if "subject_class_uri" in triple else {}),
        # Merge the information about the object class from the ontology (second right list)
        **({f"object_class_{k}": v for k, v in classes_dict.get(triple["object_class_uri"], {}).items()} if "object_class_uri" in triple else {}),
        # Merge the information about the predicate from the ontology (third right list)
        **{f"predicate_{k}": v for k, v in properties_dict.get(f'{triple["subject_class_uri"]}-{triple["predicate_uri"]}', {}).items()},
    } for triple in outgoing_props]
    # For incoming
    display_triples_list_incoming = [{
        # Get attributes from left list
        **triple, 
        # Merge the information about the subject class from the ontology (first right list)
        **({f"subject_class_{k}": v for k, v in classes_dict.get(triple["subject_class_uri"], {}).items()} if "subject_class_uri" in triple else {}),
        # Merge the information about the object class from the ontology (second right list)
        **({f"object_class_{k}": v for k, v in classes_dict.get(triple["object_class_uri"], {}).items()} if "object_class_uri" in triple else {}),
        # Merge the information about the predicate from the ontology (third right list)
        **{f"predicate_{k}": v for k, v in properties_dict.get(f'{triple["object_class_uri"]}-{triple["predicate_uri"]}', {}).items()},
    } for triple in incoming_props]
    # Regroup both lists
    display_triples_list = display_triples_list_outgoing + display_triples_list_incoming

    # Convert into list of DisplayTriples instances
    display_triples = list(map(lambda triple: DisplayTriple.from_dict(triple), display_triples_list))

    # Sort on predicate order
    display_triples.sort(key=lambda item: item.predicate.order)

    return display_triples


@st.cache_data(show_spinner=False, ttl='30 seconds', hash_funcs={Graph: lambda graph: graph.uri, Entity: lambda ent: ent.uri})
def get_entity_outgoing_triples(entity: Entity, graph: Graph = None) -> List[DisplayTriple]:
    """Fetch all outgoing triples from the given graph about the given entity."""

    # In case the entity is a blank node, do nothing
    if entity.is_blank:
        st.error('Can not fetch triples from a blank node')
        return []
    
    # Make sure the given entity is a valid URI
    entity_uri = ensure_uri(entity.uri)
    graph_uri = ensure_uri(graph.uri)

    # Fetch the ontology
    ontology = get_ontology()
    classes_dict = ontology.get_classes_named_dict()
    properties_dict = ontology.get_properties_named_dict()

    # Prepare the query (Outgoing properties)
    text = """
        SELECT DISTINCT
            ('""" + entity_uri + """' as ?subject_uri)
            ('""" + entity.label.replace("'", "\\'") + """' as ?subject_label)
            ('""" + entity.class_uri + """' as ?subject_class_uri)
            ('""" + (entity.comment.replace("'", "\\'") or '') + """' as ?subject_comment)
            (isBlank(""" + entity_uri + """) as ?subject_is_blank)
            ?predicate_uri
            ?object_uri
            (COALESCE(?object_label_, '') as ?object_label)
            (COALESCE(?object_class_uri_, '') as ?object_class_uri)
            (COALESCE(?object_comment_, '') as ?object_comment)
            (isLiteral(?object_uri) as ?object_is_literal)
            (isBlank(?object_uri) as ?object_is_blank)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                """ + entity_uri + """ ?predicate_uri ?object_uri . 
                OPTIONAL { ?object_uri rdfs:label ?object_label_ . }
                OPTIONAL { ?object_uri a ?object_class_uri_ . }
                OPTIONAL { ?object_uri rdfs:comment ?object_comment_ . }
            """ + ("}" if graph_uri else "") + """
        }
    """

    # Execute the request (Outgoing properties)
    with st.spinner(f"Fetching outgoing triples from graph {graph.label}..."):
        outgoing_props = query(text)

    # Merge the data (left joins)
    display_triples_list = [{
        # Get attributes from left list
        **triple, 
        # Merge the information about the subject class from the ontology (first right list)
        **({f"subject_class_{k}": v for k, v in classes_dict.get(triple["subject_class_uri"], {}).items()} if "subject_class_uri" in triple else {}),
        # Merge the information about the object class from the ontology (second right list)
        **({f"object_class_{k}": v for k, v in classes_dict.get(triple["object_class_uri"], {}).items()} if "object_class_uri" in triple else {}),
        # Merge the information about the predicate from the ontology (third right list)
        **{f"predicate_{k}": v for k, v in properties_dict.get(f'{triple["subject_class_uri"]}-{triple["predicate_uri"]}', {}).items()},
    } for triple in outgoing_props]

    # Here, since we are making a left join, some of the triples are not in the onotlogy, so we need to make sure that some information are set
    display_triples_list = [{
        **triple, 
        "predicate_order": triple["predicate_order"] if "predicate_order" in triple and triple["predicate_order"] is not None else 1000000000000000000
    } for triple in display_triples_list]

    # Convert into list of DisplayTriples instances
    display_triples = list(map(lambda triple: DisplayTriple.from_dict(triple), display_triples_list))

    # Sort on predicate order
    display_triples.sort(key=lambda item: item.predicate.order)

    return display_triples


@st.cache_data(show_spinner=False, ttl='30 seconds', hash_funcs={Graph: lambda graph: graph.uri, Entity: lambda ent: ent.uri})
def get_entity_incoming_triples(entity: Entity, graph: Graph = None, limit=None) -> List[DisplayTriple]:
    """Fetch all incoming triples from the given graph about the given entity."""

    # In case the entity is a blank node, do nothing
    if entity.is_blank:
        st.error('Can not fetch triples from a blank node')
        return []

    # Make sure the given entity is a valid URI
    entity_uri = ensure_uri(entity.uri)
    graph_uri = ensure_uri(graph.uri)

    # Fetch the ontology
    ontology = get_ontology()
    classes_dict = ontology.get_classes_named_dict()
    properties_dict = ontology.get_properties_named_dict()

    # Prepare the query (Outgoing properties)
    text = """
        SELECT DISTINCT
            ?subject_uri
            (COALESCE(?subject_label_, 'No label') as ?subject_label)
            (COALESCE(?subject_class_uri_, '') as ?subject_class_uri)
            (COALESCE(?subject_comment_, '') as ?subject_comment)
            (isBlank(?subject_uri) as ?subject_is_blank)
            ?predicate_uri
            ('""" + entity.uri + """' as ?object_uri)
            ('""" + entity.label.replace("'", "\\'") + """' as ?object_label)
            ('""" + entity.class_uri + """' as ?object_class_uri)
            ('""" + (entity.comment.replace("'", "\\'") or '') + """' as ?object_comment)
            ('false' as ?object_is_literal)
            (isBlank(?object_uri) as ?object_is_blank)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                ?subject_uri ?predicate_uri """ + entity_uri + """ . 
                ?subject_uri rdfs:label ?subject_label_ .
                OPTIONAL { ?subject_uri a ?subject_class_uri_ . }
                OPTIONAL { ?subject_uri rdfs:comment ?subject_comment_ . }
            """ + ("}" if graph_uri else "") + """
        }
        """ + (f"LIMIT {limit}" if limit else "") + """
    """

    # Execute the request (Incoming properties)
    with st.spinner(f"Fetching incoming triples from graph {graph.label}..."):
        incoming_props = query(text)

    # Merge the data (left joins)
    display_triples_list = [{
        # Get attributes from left list
        **triple, 
        # Merge the information about the subject class from the ontology (first right list)
        **({f"subject_class_{k}": v for k, v in classes_dict.get(triple["subject_class_uri"], {}).items()} if "subject_class_uri" in triple else {}),
        # Merge the information about the object class from the ontology (second right list)
        **({f"object_class_{k}": v for k, v in classes_dict.get(triple["object_class_uri"], {}).items()} if "object_class_uri" in triple else {}),
        # Merge the information about the predicate from the ontology (third right list)
        **{f"predicate_{k}": v for k, v in properties_dict.get(f'{triple["subject_class_uri"]}-{triple["predicate_uri"]}', {}).items()},
    } for triple in incoming_props]

    # Here, since we are making a left join, some of the triples are not in the onotlogy, so we need to make sure that some information are set
    display_triples_list = [{
        **triple, 
        "predicate_order": triple["predicate_order"] if "predicate_order" in triple and triple["predicate_order"] is not None else 1000000000000000000
    } for triple in display_triples_list]

    # Convert into list of DisplayTriples instances
    display_triples = list(map(lambda triple: DisplayTriple.from_dict(triple), display_triples_list))

    # Sort on predicate order
    display_triples.sort(key=lambda item: item.predicate.order)

    return display_triples


@st.cache_data(show_spinner=False, ttl='30 seconds', hash_funcs={Graph: lambda graph: graph.uri, Entity: lambda ent: ent.uri, OntologyClass: lambda cls: cls.uri})
def get_all_instances_of_class(cls: OntologyClass, graph: Graph) -> List[Dict[str, str]] | bool: 
    """List all instances with all properties (from the ontology) of a given class."""

    graph_uri = ensure_uri(graph.uri)

    # Get the ontology properties of this class
    ontology = get_ontology()
    properties_outgoing = [prop for prop in ontology.properties if prop.domain_class_uri == cls.uri]
    
    # Prepare the query: make all lines from the query
    properties_outgoing_names = [f"(COALESCE(?{to_snake_case(prop.label)}_, '') as ?{to_snake_case(prop.label)})" for prop in properties_outgoing]
    properties_outgoing_names_str = '\n            '.join(properties_outgoing_names)
    triples_outgoings = [f"optional {{ ?instance {prop.uri} ?{to_snake_case(prop.label)}_ . }}" for prop in properties_outgoing]
    triples_outgoings_str = '\n                '.join(triples_outgoings)

    # Build the query
    text = f"""
        SELECT
            (?instance as ?uri)
            ('{cls.uri}' as ?type)
            {properties_outgoing_names_str}
        WHERE {{
            {'GRAPH ' + graph_uri + '{' if graph_uri else ''}
                ?instance rdf:type {cls.uri} .
                {triples_outgoings_str}
            {'}' if graph_uri else ''}
        }}
    """

    # Execute the query
    with st.spinner(f"Fetching all instances of class {cls.display_label} from graph {graph.label}..."):
        instances = query(text)

    return instances


def download_graph(graph: Graph) -> str:
    """Fetches the named graph and returns its content."""

    # Force the right format
    graph_uri = ensure_uri(graph.uri)
    
    # Prepare the query
    text = """
        SELECT 
            (COALESCE(?subject , '') as ?s)
            (COALESCE(?predicate , '') as ?p)
            (COALESCE(?object, '') as ?o)
            (isLiteral(?object) as ?literal)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else '') + """
                ?subject ?predicate ?object 
            """ + ("}" if graph_uri else '') + """
        }
    """

    # Execute the query
    with st.spinner(f"Fetching all triples from graph {graph.label}..."):
        triples = query(text)   
    
    # Add all prefixes
    content = get_prefixes_str(format='turtle') + '\n\n'

    # Add all triples
    for triple in triples:
        subject = ensure_uri(triple['s'])
        predicate = ensure_uri(triple['p'])
        if triple['literal'] == 'true': object = f"'{triple['o']}'"
        else: object = ensure_uri(triple['o'])

        content += f"{subject} {predicate} {object} .\n"

    return content


@st.cache_data(show_spinner=False, ttl='30 seconds', hash_funcs={Graph: lambda graph: graph.uri, Entity: lambda ent: ent.uri})
def get_graph_of_entities(entity_uris: List[str]) -> List[DisplayTriple]:


    # In case the entity is a blank node, do nothing
    if any([uri.startswith('_:') for uri in entity_uris]):
        st.error('Can not fetch triples from a blank node')
        return []

    # From state
    graph = state.get_graph()
    
    # Fetch the ontology
    ontology = get_ontology()
    classes_dict = ontology.get_classes_named_dict()
    properties_dict = ontology.get_properties_named_dict()

    entity_uris = list(map(lambda uri: ensure_uri(uri), entity_uris))

    # Prepare the query
    text = """            
        SELECT DISTINCT
            (COALESCE(?s2, '') as ?sub2_uri)
            (COALESCE(?s2_label, '') as ?sub2_label)
            (COALESCE(?s2_class_uri, '') as ?sub2_class_uri)
            (COALESCE(?s2_comment, '') as ?sub2_comment)
            (COALESCE(isBlank(?s2), 'false') as ?sub2_is_blank)
            (COALESCE(?p2, '') as ?pred2)
            (COALESCE(?target, '') as ?initial_uri)
            (COALESCE(?target_label, '') as ?initial_label)
            (COALESCE(?target_class_uri, '') as ?initial_class_uri)
            (COALESCE(?target_comment, '') as ?initial_comment)
            (COALESCE(isBlank(?target), 'false') as ?initial_is_blank)
            (COALESCE(?p1, '') as ?pred1)
            (COALESCE(?o1, '') as ?obj1_uri)
            (COALESCE(?o1_label, '') as ?obj1_label)
            (COALESCE(?o1_class_uri, '') as ?obj1_class_uri)
            (COALESCE(?o1_comment, '') as ?obj1_comment)
            (COALESCE(isLiteral(?o1), 'false') as ?is_literal)
            (COALESCE(isBlank(?o1), 'false') as ?obj1_is_blank)
        WHERE {
            """ + ("GRAPH " + ensure_uri(graph.uri) + " {" if graph.uri else "") + """
                    {    
                        optional { 
                            ?target ?p1 ?o1 . 
                            optional { ?o1 rdfs:label ?o1_label . }
                            optional { ?o1 rdf:type ?o1_class_uri . }
                            optional { ?o1 rdfs:comment ?o1_comment . }
                            FILTER (?p1 NOT IN (rdf:type, rdfs:label, rdfs:comment) )
                        }
                    } UNION {
                        optional { 
                            ?s2 ?p2 ?target . 
                            optional { ?s2 rdfs:label ?s2_label . }
                            optional { ?s2 rdf:type ?s2_class_uri . }
                            optional { ?s2 rdfs:comment ?s2_comment . }
                        }
                    }
                    optional { ?target rdfs:label ?target_label . }
                    optional { ?target rdf:type ?target_class_uri . }
                    optional { ?target rdfs:comment ?target_comment . }
                
                VALUES ?target { """ + ' '.join(entity_uris) + """ }

            """ + ("}" if graph.uri else "") + """
        }
    """

    # Execute the query
    with st.spinner(f"Fetching all triples of {len(entity_uris)} entities from graph {graph.label}..."):
        response = query(text)

    # Build triples
    triples = []
    for line in response:
        triples.append({
            'subject_uri': line['sub2_uri'] if line['pred2'] else line['initial_uri'],
            'subject_label': line['sub2_label'] if line['pred2'] else line['initial_label'],
            'subject_comment': line['sub2_comment'] if line['pred2'] else line['initial_comment'],
            'subject_class_uri': line['sub2_class_uri'] if line['pred2'] else line['initial_class_uri'],
            'subject_is_blank': line['sub2_is_blank'] if line['pred2'] else line['initial_is_blank'],
            'predicate_uri': line['pred2'] if line['pred2'] else line['pred1'],
            'object_uri': line['initial_uri'] if line['pred2'] else line['obj1_uri'],
            'object_label': line['initial_label'] if line['pred2'] else line['obj1_label'],
            'object_comment': line['initial_comment'] if line['pred2'] else line['obj1_comment'],
            'object_class_uri': line['initial_class_uri'] if line['pred2'] else line['obj1_class_uri'],
            'object_is_literal': 'false' if line['pred2'] else line['is_literal'],
            'object_is_blank': line['initial_is_blank'] if line['pred2'] else line['obj1_is_blank'],
        })

    # Merge the ontology (left joins)
    display_triples_list = [{
        # Get attributes from left list
        **triple, 
        # Merge the information about the subject class from the ontology (first right list)
        **({f"subject_class_{k}": v for k, v in classes_dict.get(triple["subject_class_uri"], {}).items()} if "subject_class_uri" in triple else {}),
        # Merge the information about the object class from the ontology (second right list)
        **({f"object_class_{k}": v for k, v in classes_dict.get(triple["object_class_uri"], {}).items()} if "object_class_uri" in triple else {}),
        # Merge the information about the predicate from the ontology (third right list)
        **{f"predicate_{k}": v for k, v in properties_dict.get(f'{triple["subject_class_uri"]}-{triple["predicate_uri"]}', {}).items()},
    } for triple in triples]

    # Here, since we are making a left join, some of the triples are not in the onotlogy, so we need to make sure that some information are set
    display_triples_list = [{
        **triple, 
        "predicate_order": triple["predicate_order"] if "predicate_order" in triple and triple["predicate_order"] is not None else 1000000000000000000
    } for triple in display_triples_list]

    # Convert into list of DisplayTriples instances
    display_triples = list(map(lambda triple: DisplayTriple.from_dict(triple), display_triples_list))

    return display_triples


def get_class_tables(graph: Graph, class_uri: str, limit: int, offset: int) -> pd.DataFrame:
    """
    Fetch, in the given graph, all instances of given class, and format them in a Dataframe.
    Dataframe columns are: uri, label, comment, number of incoming triples, number of outgoing triples.
    """

    # Make sure the given elements are valid URIs
    class_uri = ensure_uri(class_uri)
    graph_uri = ensure_uri(graph.uri)

    # Prepare the query (fetch instances)
    text = """
        SELECT 
            ?uri 
            (COALESCE(?label_, ?uri) as ?label)
            (COALESCE(?comment_, '') as ?comment)
            (COALESCE(?inc_count, 0) AS ?incoming_count) 
            (COALESCE(?out_count, 0) AS ?outgoing_ount)
        WHERE {
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                ?uri a """ + class_uri + """ .
                OPTIONAL { ?uri rdfs:label ?label_ . }
                OPTIONAL { ?uri rdfs:comment ?comment_ . }
                
                {
                    SELECT ?uri (COUNT(?incoming) as ?inc_count) WHERE {
                        ?uri a """ + class_uri + """ .
                        ?incoming ?p ?uri .
                    } GROUP BY ?uri
                }
                
                {
                    SELECT ?uri (COUNT(?outgoing) as ?out_count) WHERE {
                        ?uri a """ + class_uri + """ .
                        ?uri ?p ?outgoing .
                    } GROUP BY ?uri
                }
            """ + ("}" if graph_uri else "") + """
        }
        ORDER BY ?uri
        LIMIT """ + str(limit) + """
        OFFSET """ + str(offset) + """
    """

    # Execute the query (fetch instances)
    instances = query(text)
    
    # Create the Dataframe
    df = pd.DataFrame(data=instances)
    
    # Clean column names
    if len(df) > 0:
        df.columns = ['URI', 'Label', 'Comment', 'Incoming number', 'Outgoing number']

    return df

    

@st.cache_data(show_spinner=False, ttl='30 seconds', hash_funcs={Graph: lambda graph: graph.uri})
def get_class_number(graph: Graph, class_uri: str) -> int:
    """Look in the given graph how much instances of given class there is."""

    # Make sure the given elements are valid URIs
    class_uri = ensure_uri(class_uri)
    graph_uri = ensure_uri(graph.uri)

    # Prepare the query (count instances)
    text = """
        SELECT (COUNT(?uri) AS ?count)
        WHERE { 
            """ + ("GRAPH " + graph_uri + " {" if graph_uri else "") + """
                ?uri a """ + class_uri + """ 
            """ + ("}" if graph_uri else "") + """
        }
    """

    # Execute the query (count instances)
    counts = query(text)
    
    return int(counts[0]['count'])