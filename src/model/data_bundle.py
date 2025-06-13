import pandas as pd, streamlit as st
from typing import Any, List, Literal
from lib import normalize_text, to_snake_case, from_snake_case
from .errors import OntologyFrameworkNotSupported, CantGetInfoOfBlankNode
from .graph import Graph
from .onto_entity import OntoEntity
from .onto_property import OntoProperty
from .ontology import Ontology
from .ontology_shacl import SHACL
from .sparql import SPARQL
from .statement import Statement

class DataBundle:
    
    name: str
    graph_data: Graph
    graph_ontology: Graph
    graph_metadata: Graph
    ontology: Ontology
    type_property: str = "rdf:type"
    label_property: str = "rdfs:label"
    comment_property: str = "rdfs:comment"


    def __init__(self, sparql: SPARQL, name: str, graph_data_uri: str, graph_ontology_uri: str, graph_metadata_uri: str, ontology_framework: str, type_property: str = None, label_property: str = None, comment_property: str = None) -> None:

        self.name = name.title()
        self.sparql = sparql
        self.graph_data = Graph(sparql, f"{self.name} - data", graph_data_uri)
        self.graph_ontology = Graph(sparql, f"{self.name} - ontology", graph_ontology_uri)
        self.graph_metadata = Graph(sparql, f"{self.name} - metadata", graph_metadata_uri)
        if type_property: self.type_property = type_property
        if label_property: self.label_property = label_property
        if comment_property: self.comment_property = comment_property

        OntologyClass = DataBundle.get_ontology_framework(ontology_framework)
        self.ontology = OntologyClass(self.graph_ontology)


    @staticmethod
    def get_ontology_framework(framework_name: str) -> Ontology:
        if framework_name == 'SHACL': return SHACL
        else: raise OntologyFrameworkNotSupported(framework_name)


    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name)})
    def count_triples(self) -> dict:
        """Count how much triples there is in the selected data-bundle/graph"""
        
        query = """
            # DataBundle.count_triples
            SELECT (COUNT(*) as ?count)
            WHERE {
                /graph_begin/
                    ?s ?p ?o .
                /graph_end/
            }
        """

        # Count in data graph
        if self.graph_data.uri: query_data = query.replace('/graph_begin/', 'GRAPH ' + self.graph_data.uri_ + ' {').replace('/graph_end/', '}')
        else: query_data = query.replace('/graph_begin/', '').replace('/graph_end/', '')
        count_graph_data = self.graph_data.sparql.run(query_data)[0]['count']

        # Count in ontology graph
        if self.graph_ontology.uri: query_ontology = query.replace('/graph_begin/', 'GRAPH ' + self.graph_ontology.uri_ + ' {').replace('/graph_end/', '}')
        else: query_ontology = query.replace('/graph_begin/', '').replace('/graph_end/', '')
        count_graph_ontology = self.graph_ontology.sparql.run(query_ontology)[0]['count']

        # Count in metadata graph
        if self.graph_metadata.uri: query_metadata = query.replace('/graph_begin/', 'GRAPH ' + self.graph_metadata.uri_ + ' {').replace('/graph_end/', '}')
        else: query_metadata = query.replace('/graph_begin/', '').replace('/graph_end/', '')
        count_graph_metadata = self.graph_metadata.sparql.run(query_metadata)[0]['count']
        
        return {
            "total": count_graph_data + count_graph_ontology + count_graph_metadata,
            "data": count_graph_data,
            "ontology": count_graph_ontology, 
            "metadata": count_graph_metadata
        }


    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name)})
    def find_entities(self, label: str = None, class_uri: str = None, limit: int = None) -> List[OntoEntity]:
        """
        Fetch the list of entities on the endpoint with:
        Args:
            label (str): the text that should be included in entity's rdfs:label. If None, fetch all entities.
            cls (str): entity's class. Filter by the given class, if specified
            limit (int): max number of retrived entities. If None, no limit is applied
        """

        # Normalize filter text
        filter_text = normalize_text(label)

        # Prepare query
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""
        filter_clause = f"FILTER(CONTAINS(LCASE(?label_), LCASE('{filter_text}'))) ." if label else ""
        class_uri = self.sparql.prepare_uri(class_uri)
        query = """
            # DataBundle.find_entities()
            SELECT
                (?uri_ as ?uri)
                (COALESCE(?label_, '') as ?label)
                (COALESCE(?comment_, '') as ?comment)
                (COALESCE(?class_uri_, '""" + (class_uri[1:-1] if class_uri else "No Class URI")  + """') as ?class_uri)
            WHERE {
                """ + graph_begin + """
                    ?uri_ """ + self.type_property + """ """ + (class_uri if class_uri else "?class_uri_")  + """ .
                    OPTIONAL { ?uri_ """ + self.label_property + """ ?label_ . }
                    OPTIONAL { ?uri_ """ + self.comment_property + """ ?comment_ . }
                """ + graph_end + """
                """ + filter_clause + """
            }
            """ + (f"LIMIT {limit}" if limit else "") + """
        """

        # Execute query
        response = self.graph_data.sparql.run(query)

        # If there is no result, there is no point to go forward
        if not response: return []

        # For each retrieved entity, look for the class label in the ontology, 
        # then transform into instances of "Entity"
        classes = list(map(lambda cls: {**cls, 'class_label': self.ontology.get_class_name(cls['class_uri'])}, response))
        entities = list(map(lambda cls: OntoEntity.from_dict(cls), classes))
        
        return entities
    

    def __merge_ontology(self, query_result: list[dict]) -> List[Statement]:
        """
        From a list of statements (in form of dictionaries), merge the ontology information.
        This function is designed to work only internally, but could also be used outside.
        """

        # Merge the ontology information
        classes_dict = self.ontology.get_classes_dict()
        properties_dict = self.ontology.get_properties_dict()
        statements_raw = [{
            # Get attributes from left list
            **statement_raw, 
            # Merge the information about the subject class from the ontology (first right list)
            **({f"subject_class_{k}": v for k, v in classes_dict.get(statement_raw["subject_class_uri"], {}).items()} if "subject_class_uri" in statement_raw else {}),
            # Merge the information about the object class from the ontology (second right list)
            **({f"object_class_{k}": v for k, v in classes_dict.get(statement_raw["object_class_uri"], {}).items()} if "object_class_uri" in statement_raw else {}),
            # Merge the information about the predicate from the ontology (third right list)
            **{f"predicate_{k}": v for k, v in properties_dict.get(f'{statement_raw["subject_class_uri"]}-{statement_raw["predicate_uri"]}', {}).items()},
        } for statement_raw in query_result]

        # Convert into a list of Statement instances
        statements = list(map(lambda stmt_raw: Statement.from_dict(stmt_raw), statements_raw))

        # Sort on predicate order
        statements.sort(key=lambda x: x.predicate.order)

        return statements


    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name), "model.onto_entity.OntoEntity": lambda x: hash(x.uri), "model.onto_entity.OntoProperty": lambda x: hash(x.uri), "builtins.list": lambda x: hash(';'.join(list(map(lambda y: y.uri, x))))})
    def get_outgoing_statements(self, entity: OntoEntity, only_wanted_properties: List[OntoProperty] = None) -> List[Statement]:
        """
        Fetch all outgoing triples from the data graph about the given entity.
        Join the triples to ontology information to return Statements
        """

        # Can not fetch statements of blank node
        if entity.is_blank: raise CantGetInfoOfBlankNode()
        
        # Prepare the query (Outgoing properties)
        entity_uri = self.sparql.prepare_uri(entity.uri)
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""
        wanted_properties = [self.sparql.prepare_uri(prop.uri) for prop in only_wanted_properties] if only_wanted_properties else ""
        wanted_properties = 'VALUES ?predicate_uri { ' + ' '.join(wanted_properties) + ' }' if only_wanted_properties else ""
        query = """
            # DataBundle.get_outgoing_statements()
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
                """ + graph_begin + """
                    """ + entity_uri + """ ?predicate_uri ?object_uri . 
                    OPTIONAL { ?object_uri """ + self.label_property + """ ?object_label_ . }
                    OPTIONAL { ?object_uri """ + self.type_property + """ ?object_class_uri_ . }
                    OPTIONAL { ?object_uri """ + self.comment_property + """ ?object_comment_ . }
                    """ + wanted_properties + """
                """ + graph_end + """
            }
        """

        # Execute query
        result = self.graph_data.sparql.run(query)

        return self.__merge_ontology(result)


    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name), "model.onto_entity.OntoEntity": lambda x: hash(x.uri), "model.onto_entity.OntoProperty": lambda x: hash(x.uri), "builtins.list": lambda x: hash(';'.join(list(map(lambda y: y.uri, x))))})
    def get_incoming_statements(self, entity: OntoEntity, limit: int = None, only_wanted_properties: List[OntoProperty] = None) -> List[Statement]:
        """
        Fetch incoming triples from the data graph about the given entity.
        Join the triples to ontology information to return Statements
        """

        # Can not fetch statements of blank node
        if entity.is_blank: raise CantGetInfoOfBlankNode()

        # Prepare the query (Incoming properties)
        entity_uri = self.sparql.prepare_uri(entity.uri)
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""
        limit = f"LIMIT {limit}" if limit else ""
        wanted_properties = [self.sparql.prepare_uri(prop.uri) for prop in only_wanted_properties] if only_wanted_properties else ""
        wanted_properties = 'VALUES ?predicate_uri { ' + ' '.join(wanted_properties) + ' }' if only_wanted_properties else ""
        query = """
            # DataBundle.get_incoming_statements()
            SELECT DISTINCT
                ?subject_uri
                (COALESCE(?subject_label_, 'No label') as ?subject_label)
                (COALESCE(?subject_class_uri_, '') as ?subject_class_uri)
                (COALESCE(?subject_comment_, '') as ?subject_comment)
                (isBlank(?subject_uri) as ?subject_is_blank)
                ?predicate_uri
                ('""" + entity_uri + """' as ?object_uri)
                ('""" + entity.label.replace("'", "\\'") + """' as ?object_label)
                ('""" + entity.class_uri + """' as ?object_class_uri)
                ('""" + (entity.comment.replace("'", "\\'") or '') + """' as ?object_comment)
                ('false' as ?object_is_literal)
                (isBlank(?object_uri) as ?object_is_blank)
            WHERE {
                """ + graph_begin + """
                    ?subject_uri ?predicate_uri """ + entity_uri + """ . 
                    ?subject_uri """ + self.label_property + """ ?subject_label_ .
                    OPTIONAL { ?subject_uri """ + self.type_property + """ ?subject_class_uri_ . }
                    OPTIONAL { ?subject_uri """+ self.comment_property + """ ?subject_comment_ . }
                    """ + wanted_properties + """
                """ + graph_end + """
            }
            """ + limit + """
        """

        # Execute query
        result = self.graph_data.sparql.run(query)

        return self.__merge_ontology(result)


    def get_card(self, entity: OntoEntity) -> List[Statement]:
        """Fetch all relevant triples (according to the ontology) from the data graph about the given entity."""

        # List all wanted properties
        ontology_properties = self.ontology.get_properties()
        wanted_properties = [prop for prop in ontology_properties if prop.card_of_class_uri == entity.class_uri]

        if len(wanted_properties) != 0:
            # Fetch all statements
            outgoings = self.get_outgoing_statements(entity, only_wanted_properties=wanted_properties)
            incomings = self.get_incoming_statements(entity, only_wanted_properties=wanted_properties)
            statements = outgoings + incomings
            
            # Sort on predicate order
            statements.sort(key=lambda x: x.predicate.order)
        else:
            statements = []

        return statements
        
    

    def get_data_table_columns(self,  cls: OntoEntity) -> list[str]:
        # List all wanted properties
        ontology_properties = self.ontology.get_properties()
        wanted_properties = [prop for prop in ontology_properties if prop.card_of_class_uri == cls.uri]
        wanted_properties.sort(key=lambda x: x.order)
        props = [(prop.label if prop.domain_class_uri == cls.uri else prop.label + ' (inc)') for prop in wanted_properties]

        return ['URI'] + props + ['Outgoing Count', 'Incoming Count']



    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name), "model.onto_entity.OntoEntity": lambda x: hash(x.uri)})
    def get_data_table(self, cls: OntoEntity, limit: int = None, offset: int = None, sort_col: str = None, sort_way: str = None, filter_col: str = None, filter_value: str = None) -> pd.DataFrame:
        """
        Fetch in the data graph all instances if given class, and format them in a DataFrame.
        DataFrame columns are those defined in the Ontology, added with the number of statements, incoming and outgoings.
        """

        # List all wanted properties
        ontology_properties = self.ontology.get_properties()
        wanted_properties = [prop for prop in ontology_properties if prop.card_of_class_uri == cls.uri]
        wanted_properties.sort(key=lambda x: x.order)

        # Small inner function to build the select statement for a given property
        def get_select_property(property: OntoProperty) -> str:
            property_label = to_snake_case(property.label).replace('-', '_')
            if cls.uri == property.domain_class_uri:
                return f"(GROUP_CONCAT(DISTINCT COALESCE(?{property_label}_, ''); separator=\" - \") as ?{property_label})"
            else:
                return f"(GROUP_CONCAT(DISTINCT COALESCE(?{property_label}_, ''); separator=\" - \") as ?{property_label}_inc)"
        # Small inner function to build the where statement for a given property
        def get_where_property(property: OntoProperty) -> str:
            property_uri = self.sparql.prepare_uri(property.uri)
            property_label = to_snake_case(property.label).replace('-', '_')
            if cls.uri == property.domain_class_uri:
                if property_uri == self.label_property or property_uri == self.comment_property:
                    return "optional { " + f"?uri_ {property_uri} ?{property_label}_" + " . }"
                else:
                    return "optional { " + f"?uri_ {property_uri} ?{property_label}_uri" + " . " + \
                        "optional { " + f"?{property_label}_uri {self.label_property} ?{property_label}_" + " . } }"
            else:
                if property_uri == self.label_property or property_uri == self.comment_property:
                    return "optional { " + f"?{property_label}_ {property_uri} ?uri_" + " . }"
                else:
                    return "optional { " + f"?{property_label}_uri {property_uri} ?uri_" + " . " + \
                           "optional { " + f"?{property_label}_uri {self.label_property} ?{property_label}_" + " . } }"

        # Prepare the query
        class_uri = self.sparql.prepare_uri(cls.uri)
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""
        select_properties = "\n                ".join([get_select_property(prop) for prop in wanted_properties])
        where_properties = "\n                    ".join([get_where_property(prop) for prop in wanted_properties])
        if sort_col: sort = f"ASC(?{to_snake_case(sort_col).replace('-', '_')})" if sort_way == 'ASC' else f"DESC(?{to_snake_case(sort_col).replace('-', '_')})"
        else: sort = "DESC(?uri)"
        sort = 'ORDER BY ' + sort
        filter = f"FILTER(CONTAINS(LCASE(STR(?{to_snake_case(filter_col).replace('-', '_')}_)), LCASE(\"{normalize_text(filter_value)}\")))" if filter_value else ""
        limit = f"LIMIT {limit}" if limit else ""
        offset = f"OFFSET {offset}" if offset else ""
        query = """
            # DataBundle.get_data_table()
            SELECT
                (COALESCE(?uri_, '') as ?uri)
                """ + select_properties + """
                (MIN(COALESCE(?outgoing_count_, 0)) AS ?outgoing_count)
                (MIN(COALESCE(?incoming_count_, 0)) AS ?incoming_count) 
            WHERE {
                """ + graph_begin + """
                    { 
                        SELECT ?uri_ 
                        WHERE { 
                            ?uri_ """ + self.type_property + """ """ + class_uri + """ . 
                        } 
                        """ + limit + """
                        """ + offset + """
                    }
                    """ + where_properties + """
                    """ + filter + """
                    
                    OPTIONAL {
                        SELECT ?uri_ (COUNT(?outgoing) as ?outgoing_count_) WHERE {
                            """ + graph_begin + """
                                ?uri_ """ + self.type_property + """ """ + class_uri + """ .
                                ?uri_ ?p ?outgoing .
                            """ + graph_end + """
                           } GROUP BY ?uri_
                    }

                    OPTIONAL {
                        SELECT ?uri_ (COUNT(?incoming) as ?incoming_count_) WHERE {
                            """ + graph_begin + """
                                ?uri_ """ + self.type_property + """ """ + class_uri + """ .
                                ?incoming ?p ?uri_ .
                            """ + graph_end + """
                        } GROUP BY ?uri_
                    }
                """ + graph_end + """
            }
            GROUP BY ?uri_
            """ + sort + """
        """

        # Execute the query (fetch instances)
        instances = self.graph_data.sparql.run(query)

        # Create the Dataframe
        df = pd.DataFrame(data=instances)
        df.columns = [from_snake_case(col).replace(' Inc', ' (inc)') for col in df.columns]
        df.rename(columns={'Uri': 'URI'}, inplace=True)

        # return df.groupby('URI').agg(lambda x: '; '.join(map(str, sorted(set(x))))).reset_index()
        return df
    

    # @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name), "model.onto_entity.OntoEntity": lambda x: hash(x.uri)})
    def get_class_count(self, cls: OntoEntity, filter_col_name: str = None, filter_content: str = None) -> int:    
        """Look in the given graph how much instances of given class there is."""

        filter_ = ""
        if filter_col_name and filter_content:
            properties = self.ontology.get_properties()
            wanted_properties = [prop for prop in properties if prop.card_of_class_uri == cls.uri]
            target_property = [prop for prop in wanted_properties if prop.label == filter_col_name.replace('(inc)', '').strip()][0]
            if '(inc)' in filter_col_name:
                filter_ = f'?value {target_property.uri} ?uri . ?value {self.label_property} ?label . FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{filter_content}")))'
            else: 
                filter_ = f'?uri {target_property.uri} ?value . ?value {self.label_property} ?label . FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{filter_content}")))'

        # Prepare the query (count instances)
        class_uri = self.sparql.prepare_uri(cls.uri)
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""
        query = """
            # DataBundle.get_class_count()
            SELECT (COUNT(?uri) AS ?count)
            WHERE { 
                """ + graph_begin + """
                    ?uri """ + self.type_property + """ """ + class_uri + """ .
                    """ + filter_ + """
                """ + graph_end + """
            }
        """

        # Execute the query (count instances)
        counts = self.graph_data.sparql.run(query)
        
        return int(counts[0]['count'])


    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name)})
    def get_entity_infos(self, uri) -> OntoEntity:
        """Find the basic info needed for a given entity."""

        # Make sure the given elements are valid URIs
        entity_uri = self.sparql.prepare_uri(uri)

        # Prepare the query
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""
        query = """
            # DataBundle.get_entity_basics()
            SELECT 
                (COALESCE(?label_, '') as ?label)
                (COALESCE(?comment_, '') as ?comment)
                (COALESCE(?class_uri_, '') as ?class_uri)
            WHERE {
                """ + graph_begin + """
                    OPTIONAL {""" + entity_uri + """ """ + self.label_property + """ ?label_ . }
                    OPTIONAL {""" + entity_uri + """ """ + self.comment_property + """ ?comment_ . }
                    OPTIONAL {""" + entity_uri + """ """ + self.type_property + """ ?class_uri_ . }
                """ + graph_end + """
            }
        """

        # Execute the query
        infos = self.graph_data.sparql.run(query)[0]

        # Add the class information:
        classes = self.ontology.get_classes()
        class_label = list(filter(lambda c: c.uri == infos.get('class_uri'), classes))[0].label

        return OntoEntity(
            uri=uri,
            label=infos.get('label'),
            comment=infos.get('comment'),
            class_uri=infos.get('class_uri'),
            class_label=class_label
        )


    def dump(self, format: Literal['nq', 'ttl', 'csv']) -> str | dict[str, str | pd.DataFrame]:

        if format == 'nq': 
            content = ""
            content += self.graph_data.dump_nquad()
            content += self.graph_ontology.dump_nquad()
            content += self.graph_metadata.dump_nquad()
            return content

        if format == 'ttl':
            return {
                "data": self.graph_data.dump_turtle(),
                "ontology": self.graph_ontology.dump_turtle(),
                "metadata": self.graph_metadata.dump_turtle(),
            }

        if format == 'csv':
            to_return = {
                'ontology-properties': pd.DataFrame(data=[prop.to_dict() for prop in self.ontology.get_properties()]),
                'ontology-classes': pd.DataFrame(data=[cls.to_dict() for cls in self.ontology.get_classes()])
            }

            for cls in self.ontology.get_classes():
                to_return[to_snake_case(cls.display_label)] = self.__download_class(cls)

            return to_return
        

    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name), "model.onto_entity.OntoEntity": lambda x: hash(x.uri)})
    def __download_class(self, cls: OntoEntity) -> pd.DataFrame:
        """List all instances with all properties (from the ontology) of a given class."""
        
        # Get the ontology properties of this class (only outgoing)
        ontology_properties = self.ontology.get_properties()
        properties_outgoing = [prop for prop in ontology_properties if prop.domain_class_uri == cls.uri]
        properties_outgoing.sort(key=lambda x: x.order)

        # Prepare the query: make all lines from the query
        properties_outgoing_names = [f"(COALESCE(?{to_snake_case(prop.label).replace('-', '_')}_, '') as ?{to_snake_case(prop.label).replace('-', '_')})" for prop in properties_outgoing]
        properties_outgoing_names_str = '\n                '.join(properties_outgoing_names)
        triples_outgoings = [f"optional {{ ?instance {prop.uri} ?{to_snake_case(prop.label).replace('-', '_')}_ . }}" for prop in properties_outgoing]
        triples_outgoings_str = '\n                    '.join(triples_outgoings)


        # Prepare the query
        class_uri = self.sparql.prepare_uri(cls.uri)
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""
        query = """
            # DataBundle.download_class(""" + f"{cls.label} ({cls.uri})" + """)
            SELECT
                (?instance as ?uri)
                ('""" + class_uri + """' as ?type)
                """ + properties_outgoing_names_str + """
            WHERE {
                """ + graph_begin + """
                    ?instance """ + self.type_property + """ """ + class_uri + """ .
                    """ + triples_outgoings_str + """
                """ + graph_end + """
            }
        """

        # Execute the query
        instances = self.graph_data.sparql.run(query)

        return pd.DataFrame(data=instances)


    @staticmethod
    def from_dict(obj: dict, sparql: SPARQL) -> 'DataBundle':
        """Convert an object into a Class instance."""

        return DataBundle(
            sparql=sparql,
            name=obj.get('name'),
            ontology_framework=obj.get('ontology_framework'),
            graph_data_uri=obj.get('graph_data_uri'),
            graph_ontology_uri=obj.get('graph_ontology_uri'),
            graph_metadata_uri=obj.get('graph_metadata_uri'),
            type_property=obj.get('type_property'),
            label_property=obj.get('label_property'),
            comment_property=obj.get('comment_property')
        )


    def to_dict(self) -> Any:
        """Convert the Class instance into a serializable object."""
        return {
            'name': self.name,
            'ontology_framework': self.ontology.name,
            'type_property': self.type_property,
            'label_property': self.label_property,
            'comment_property': self.comment_property,
            'graph_data_uri': self.graph_data.uri,
            'graph_ontology_uri': self.graph_ontology.uri,
            'graph_metadata_uri': self.graph_metadata.uri,
        }