import streamlit as st
from typing import List
from .ontology import Ontology
from .onto_entity import OntoEntity
from .onto_property import OntoProperty
from .graph import Graph


class NoFramework(Ontology):

    def __init__(self, graph: Graph, type_property: str = "", label_property: str = "") -> None:
        super().__init__(graph)
        self.name = "No Framework"
        self.type_property = type_property
        self.label_property = label_property


    @st.cache_resource(show_spinner=False, ttl=3600, hash_funcs={"model.ontology_no_framework.NoFramework": lambda x: hash(x.name)})
    def get_classes(self) -> List[OntoEntity]:
        """Get the list of classes listed within the ontology graph."""

        # Prepare the query
        graph_begin = "GRAPH " + self.graph.uri_ + " {" if self.graph.uri else ""
        graph_end = "}" if self.graph.uri else ""
        query = f"""
            # NoFramework.get_classes()
            SELECT DISTINCT
                ?uri 
                (COALESCE(?label_, '') as ?label)
            WHERE {{
                {graph_begin}
                    ?subject {self.type_property} ?uri
                    OPTIONAL {{ ?uri {self.label_property} ?label_}}
                {graph_end}
            }}
        """

        # Execute the query
        response = self.graph.sparql.run(query)

        # Transform into a list of OntologyClass instances, or an empty list
        classes = list(map(lambda cls: OntoEntity.from_dict(cls), response)) if response else []

        return classes


        
    @st.cache_data(show_spinner=False, ttl=3600, hash_funcs={"model.ontology_no_framework.NoFramework": lambda x: hash(x.name), "model.onto_entity.OntoProperty": lambda x: hash(x.uri)})
    def get_properties(self) -> List[OntoProperty]:
        """Get the list of properties listed within the ontology graph."""

        # Prepare the query
        graph_begin = "GRAPH " + self.graph.uri_ + " {" if self.graph.uri else ""
        graph_end = "}" if self.graph.uri else ""
        query = f"""
            # NoFramework.get_properties()
            SELECT distinct 
                (COALESCE(?domain_class_uri_, '') as ?domain_class_uri)
                ?uri 
                ?range_class_uri
            WHERE {{
                {graph_begin}
                    ?s ?uri ?o .
                    optional {{ ?s {self.type_property} ?domain_class_uri_ . }}
                    optional {{ ?o {self.type_property} ?range_class_uri_ . }}
                {graph_end}
                
                FILTER (?uri != rdf:type && ?uri != rdf:label)
                BIND(IF(isLiteral(?o), "xsd:string", COALESCE(?range_class_uri_, "")) as ?range_class_uri)
            }}
        """

        # Execute the query
        response = self.graph.sparql.run(query)

        # Transform into a list of OntologyClass instances, or an empty list
        properties = list(map(lambda prop: OntoProperty.from_dict(prop), response)) if response else []

        return properties
        