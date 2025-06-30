import streamlit as st
from typing import List
from .graph import Graph
from .onto_entity import OntoEntity
from .onto_property import OntoProperty
from .ontology import Ontology


class SHACL(Ontology):
    
    def __init__(self, graph: Graph, type_property: str = None, label_property: str = None) -> None:
        super().__init__(graph)
        self.name = "SHACL"


    @st.cache_resource(show_spinner=False, ttl=3600, hash_funcs={"model.ontology_shacl.SHACL": lambda x: hash(x.name)})
    def get_classes(self) -> List[OntoEntity]:
        """Get the list of classes listed within the ontology graph."""
        
        graph_begin = "GRAPH " + self.graph.uri_ + " {" if self.graph.uri else ""
        graph_end = "}" if self.graph.uri else ""
        query = """
            # SHACL.get_classes()
            SELECT 
                ?uri 
                (COALESCE(?label_, '') as ?label)
            WHERE {
                """ + graph_begin + """
                    ?node a sh:NodeShape .
                    ?node sh:name ?label_ .
                    ?node sh:targetClass ?uri .
                """ + graph_end + """
            }
        """

        # Execute the query
        response = self.graph.sparql.run(query)

        # Transform into a list of OntologyClass instances, or an empty list
        classes = list(map(lambda cls: OntoEntity.from_dict(cls), response)) if response else []

        return classes
    

    @st.cache_data(show_spinner=False, ttl=3600, hash_funcs={"model.ontology_shacl.SHACL": lambda x: hash(x.name), "model.onto_entity.OntoProperty": lambda x: hash(x.uri)})
    def get_properties(self) -> List[OntoProperty]:
        """Get the list of properties listed with the SHACL framework."""

        graph_begin = "GRAPH " + self.graph.uri_ + " {" if self.graph.uri else ""
        graph_end = "}" if self.graph.uri else ""
        query = """
            # SHACL.get_properties()
            SELECT DISTINCT
                (COALESCE(?target_class_, '') as ?card_of_class_uri)
                (COALESCE(?label_, ?uri) as ?label)
                (COALESCE(?order_, '') as ?order)
                (COALESCE(?min_count_, '') as ?min_count)
                (COALESCE(?max_count_, '') as ?max_count)
                (COALESCE(?domain_class_uri_, '') as ?domain_class_uri)
                ?uri
                (COALESCE(?range_class_uri_, ?datatype_, '') as ?range_class_uri)
            WHERE {
                """ + graph_begin + """               
                    ?shape sh:property ?node .
                    ?node sh:path ?supposed_uri .  
                    OPTIONAL { ?shape sh:targetClass ?target_class_ . }
                    OPTIONAL { ?supposed_uri sh:inversePath ?inverse_property_uri . }
                    OPTIONAL { ?node sh:name ?label_ . }
                    OPTIONAL { ?node sh:order ?order_ . }
                    OPTIONAL { ?node sh:minCount ?min_count_ . }
                    OPTIONAL { ?node sh:maxCount ?max_count_ . }
                    OPTIONAL { ?node sh:datatype ?datatype_ . }
                    OPTIONAL { ?node sh:class ?class . }

                    BIND(IF(isBlank(?supposed_uri), '', ?target_class_) as ?domain_class_uri_)
                    BIND(IF(isBlank(?supposed_uri), ?target_class_, ?class) as ?range_class_uri_)
                    BIND(IF(isBlank(?supposed_uri), ?inverse_property_uri, ?supposed_uri) as ?uri)
                """ + graph_end + """
            }
        """

        # Execute the query
        response = self.graph.sparql.run(query)

        # Transform into a list of OntologyClass instances, or an empty list
        properties = list(map(lambda prop: OntoProperty.from_dict(prop), response)) if response else []

        return properties
        