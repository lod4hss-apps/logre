from typing import Any, List, Literal
import streamlit as st
import pandas as pd

# Local imports
from lib import normalize_text, to_snake_case, from_snake_case
from .errors import OntologyFrameworkNotSupported, CantGetInfoOfBlankNode
from .graph import Graph
from .onto_entity import OntoEntity
from .onto_property import OntoProperty
from .ontology import Ontology
from .ontology_shacl import SHACL
from .ontology_no_framework import NoFramework
from .sparql import SPARQL
from .statement import Statement

"""
This class wraps the use, informations, queries, and other actions around a data bundle.
It has all information needed to perform queries, retrieve and format data.
It is also the place where queries are set to fetch specific informations.
To know more about "what is a data bundle", please refer to the user documentation;
long story short, hear "Dataset" when you hear "Data Bundle".
"""


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
        """
        Initialize a DataBundle, and set defaults.

        Args:
            sparql (SPARQL): The right SPARQL wrapper to use (eg GraphDB, Fuseki, ...).
            name (sting): DataBunble name (eg "British Royal Bloodline").
            graph_data_uri (string): URI of the Named Graph where the data are.
            graph_ontology_uri (string): URI of the Named Graph where the model is.
            graph_metadata_uri (string): URI of the Named Graph where all the metadata are.
            ontology_framerwork (string): The ontology framework Logre should use to read the data.
            type_property (string): URI of the property used to assign a class to an instance, defaults to "rdf:type".
            label_property (string): URI of the property that gives an entity a label, defaults to "rdf:label".
            comment_property (string): URI of the property that set a comment for a given entity, defaults to "rdf:comment".
        """

        # Set attributes
        self.name = name
        self.sparql = sparql
        self.graph_data = Graph(sparql, f"{self.name} - data", graph_data_uri)
        self.graph_ontology = Graph(sparql, f"{self.name} - ontology", graph_ontology_uri)
        self.graph_metadata = Graph(sparql, f"{self.name} - metadata", graph_metadata_uri)
        if type_property: self.type_property = type_property
        if label_property: self.label_property = label_property
        if comment_property: self.comment_property = comment_property
    
        # Initialize the ontology instance (based on given ontology framework)
        OntologyClass = DataBundle.get_ontology_framework(ontology_framework)
        self.ontology = OntologyClass(self.graph_ontology, self.type_property, self.label_property)


    @staticmethod
    def get_ontology_framework(framework_name: str) -> Ontology:
        """
        Based on the given ontology framework name, return the right class to instanciate.

        Args:
            framework_name (string): Name of the ontology framework (eg "SHACL", "RDF")

        Returns:
            Ontology: The right class (children of Ontology)
        """

        if framework_name == 'SHACL': return SHACL
        if framework_name == 'No Framework': return NoFramework
        else: raise OntologyFrameworkNotSupported(framework_name)


    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name)})
    def count_triples(self) -> dict:
        """
        Count how much triples there is in all three named graph.

        Returns: 
            dict: dictionary of "key:number" detailing triple number in all data bundle graph.
        
        """

        # Query model to be adapted to each graph
        query = """
            # DataBundle.count_triples
            SELECT (COUNT(*) as ?count)
            WHERE {
                {graph_begin}
                    ?s ?p ?o .
                {graph_end}
            }
        """

        # Count data graph triples
        if self.graph_data.uri: query_data = query.format(graph_begin=f"GRAPH " + self.graph_data.uri_ + " {", graph_end='}')
        else: query_data = query.replace(graph_begin='', graph_end='')
        count_graph_data = self.graph_data.sparql.run(query_data)[0]['count']

        # Count ontology graph triples
        if self.graph_ontology.uri: query_ontology = query.format(graph_begin=f"GRAPH " + self.graph_ontology.uri_ + " {", graph_end='}')
        else: query_ontology = query.replace(graph_begin='', graph_end='')
        count_graph_ontology = self.graph_ontology.sparql.run(query_ontology)[0]['count']

        # Count metadata graph triples
        if self.graph_metadata.uri: query_metadata = query.format(graph_begin=f"GRAPH " + self.graph_metadata.uri_ + " {", graph_end='}')
        else: query_metadata = query.replace(graph_begin='', graph_end='')
        count_graph_metadata = self.graph_metadata.sparql.run(query_metadata)[0]['count']
        
        # Return the dictionary
        return {
            "total": count_graph_data + count_graph_ontology + count_graph_metadata,
            "data": count_graph_data,
            "ontology": count_graph_ontology, 
            "metadata": count_graph_metadata
        }


    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name)})
    def find_entities(self, label: str = None, class_uri: str = None, limit: int = None) -> List[OntoEntity]:
        """
        Given the filter on label and class, fetch the corresponding entities.

        Args:
            label (str): Text that should be included in entity's label. If None, fetch all entities.
            cls (str): Entity's class. Filter by the given class, if specified.
            limit (int): Max number of retrived entities. If None, no limit is applied.

        Returns:
            List of OntoEntities: Entities matching the filter
        """

        # Normalize filter text
        filter_text = normalize_text(label)

        # Prepare query
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""
        filter_clause = f"FILTER(CONTAINS(LCASE(?label_), LCASE('{filter_text}'))) ." if label else ""
        prepared_class_uri = self.sparql.prepare_uri(class_uri)
        query = """
            # DataBundle.find_entities()
            SELECT
                (?uri_ as ?uri)
                (COALESCE(?label_, '') as ?label)
                (COALESCE(?comment_, '') as ?comment)
                (COALESCE(?class_uri_, '""" + (class_uri if class_uri else "No Class URI")  + """') as ?class_uri)
            WHERE {
                """ + graph_begin + """
                    ?uri_ """ + self.type_property + """ """ + (prepared_class_uri if prepared_class_uri else "?class_uri_")  + """ .
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


    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name), "model.onto_entity.OntoEntity": lambda x: hash(x.uri), "model.onto_entity.OntoProperty": lambda x: hash(x.uri), "builtins.list": lambda x: hash(';'.join(list(map(lambda y: y.uri, x))))})
    def get_outgoing_statements(self, entity: OntoEntity, only_wanted_properties: List[OntoProperty] = None) -> List[Statement]:
        """
        For the given entity, fetch all outgoing triples (from data graph).
        Join the triples to ontology information to return instances of Statements.

        Args:
            entity (OntoEntity): Information about the entity to retrive triples from.
            only_wanted_properties (list of OntoProperty): Optional. White list of properties to retrieve. If not set, retrieve all.

        Returns:
            list of Statements: The list of formated Statements.
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
                ('""" + entity.uri + """' as ?subject_uri)
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

        # Add ontology informations and get Statement instances
        result = self.__merge_ontology(result)

        return result


    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name), "model.onto_entity.OntoEntity": lambda x: hash(x.uri), "model.onto_entity.OntoProperty": lambda x: hash(x.uri), "builtins.list": lambda x: hash(';'.join(list(map(lambda y: y.uri, x))))})
    def get_incoming_statements(self, entity: OntoEntity, limit: int = None, only_wanted_properties: List[OntoProperty] = None) -> List[Statement]:
        """
        For the given entity, fetch all incoming triples (from data graph).
        Join the triples to ontology information to return instances of Statements.
        Also support a property white list. Doing so allows to increase performance when fetching.

        Args:
            entity (OntoEntity): Information about the entity to retrive triples from.
            only_wanted_properties (list of OntoProperty): Optional. White list of properties to retrieve. If not set, retrieve all.

        Returns:
            list of Statements: The list of formated Statements.
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
                (COALESCE(?subject_label_, '') as ?subject_label)
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
                """ + graph_begin + """
                    ?subject_uri ?predicate_uri """ + entity_uri + """ . 
                    OPTIONAL { ?subject_uri """ + self.label_property + """ ?subject_label_ . }
                    OPTIONAL { ?subject_uri """ + self.type_property + """ ?subject_class_uri_ . }
                    OPTIONAL { ?subject_uri """+ self.comment_property + """ ?subject_comment_ . }
                    """ + wanted_properties + """
                """ + graph_end + """
            }
            """ + limit + """
        """

        # Execute query
        result = self.graph_data.sparql.run(query)

        # Add ontology informations and get Statement instances
        result = self.__merge_ontology(result)

        return result


    def get_card(self, entity: OntoEntity) -> List[Statement]:
        """
        Fetch all triples of interest (according to the ontology) for the entity class, from the data graph.

        Args:
            entity (OntoEntity): The entity to fetch triples from.

        Returns:
            List of Statements: All Statements of the entity, filtered by interest by the ontology.
        """

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
        """
        For a given class, fetch all wanted columns of the Data Table view in Logre.

        Args:
            cls (OntoEntity): The class to get column to display.
        
        Returns:
            List of string: columns names of the Data Table.
        """

        # List all wanted properties
        ontology_properties = self.ontology.get_properties()
        wanted_properties = [prop for prop in ontology_properties if prop.card_of_class_uri == cls.uri]
        wanted_properties.sort(key=lambda x: x.order)
        props = [(f"{prop.label}" if prop.domain_class_uri == cls.uri else prop.label + ' (inc)') for prop in wanted_properties]

        # Create the specific function
        def make_unique(lst: List[str]) -> list[str]:
            """
            Specific functions that append a counter each time the same element of the given list appears.
            (eg "Col Name", "Col Name (2)", "Col Name (3)")

            Args:
                lst (list of string): The list with potentially duplicates

            Returns:
                List of string: The list with no more duplicates (because of number appending).
            """
            counts = {}
            result = []
            for item in lst:
                if item not in counts:
                    counts[item] = 0
                    result.append(item)
                else:
                    counts[item] += 1
                    result.append(f"{item} ({counts[item] + 1})")
            return result

        return make_unique(['URI'] + props + ['Outgoing Count', 'Incoming Count'])


    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name), "model.onto_entity.OntoEntity": lambda x: hash(x.uri)})
    def get_data_table(self, cls: OntoEntity, limit: int = None, offset: int = 0, sort_col: str = None, sort_way: str = None, filter_col: str = None, filter_value: str = None) -> pd.DataFrame:
        """
        From the data named graph, fetch information about instances of the given glass,
        and format data accordingly as a DataFrame.
        DataFrame columns are those defined in the Ontology, appended with the number of statements, incoming and outgoings.

        Args:
            cls (OntoEntity): The class of instances to retrieve.
            limit (int): Number of instances to retrieve.
            offset (int): offset of instances (paginated table).
            sort_col (string): Optional. The name of the column to sort on.
            sort_way (string): Optional. ASC or DESC.
            filter_col (string): Optional. The name of the column to filter on.
            filter_value (string) : Optional. The value to find in the column.

        Returns:
            DataFrame: The data table. Columns are properties (formated), cells are class labels or values.
        """


        ### Preparations ###

        # List all wanted properties for this class (according to ontology)
        ontology_properties = self.ontology.get_properties()
        wanted_properties = [prop for prop in ontology_properties if prop.card_of_class_uri == cls.uri]
        wanted_properties.sort(key=lambda x: x.order)

        # Prepare sorting
        if sort_col is not None:
            # Find the property with the given label
            sort_prop = list(filter(lambda prop: prop.label == sort_col, wanted_properties))[0]
            if sort_prop.domain_class_uri == cls.uri:
                # ie: is outgoing
                if sort_prop.range_is_value():
                    # ie: no need to get the label
                    sort_prop_str1 = f"?uri_ {self.sparql.prepare_uri(sort_prop.uri)} ?sort_on ."
                else:
                    # ie: need extra path to the label
                    sort_prop_str1 = f"?uri_ {self.sparql.prepare_uri(sort_prop.uri)} ?sort_entity . ?sort_entity {self.label_property} ?sort_on ."
            else:
                # ie: is incoming
                if sort_prop.range_is_value():
                    # ie: no need to get the label
                    sort_prop_str1 = f"?sort_on {self.sparql.prepare_uri(sort_prop.uri)} ?uri_ ."
                else:
                    # ie: need extra path to the label
                    sort_prop_str1 = f"?sort_entity {self.sparql.prepare_uri(sort_prop.uri)} ?uri_ . ?sort_entity {self.label_property} ?sort_on ."

            # Create the SPARQL appendix for the sorting
            if sort_way == 'ASC': order_by = "ORDER BY ASC(?sort_on)"
            else: order_by = "ORDER BY DESC(?sort_on)"
        else:
            sort_prop_str1 = ""
            order_by = ""

        # Prepare filtering
        if filter_col is not None:
            # Find the property with the given label
            filter_prop = list(filter(lambda prop: prop.label == filter_col, wanted_properties))[0]
            if filter_prop.domain_class_uri == cls.uri:
                # ie: is outgoing
                if filter_prop.range_is_value():
                    # ie: no need to get the label
                    filter_prop_str1 = f"?uri_ {self.sparql.prepare_uri(filter_prop.uri)} ?filter_on ."
                else:
                    # ie: need extra path to the label
                    filter_prop_str1 = f"?uri_ {self.sparql.prepare_uri(filter_prop.uri)} ?filter_entity . ?filter_entity {self.label_property} ?filter_on ."
            else:
                # ie: is incoming
                if filter_prop.range_is_value():
                    # ie: no need to get the label
                    filter_prop_str1 = f"?filter_on {self.sparql.prepare_uri(filter_prop.uri)} ?uri_ ."
                else:
                    # ie: need extra path to the label
                    filter_prop_str1 = f"?filter_entity {self.sparql.prepare_uri(filter_prop.uri)} ?uri_ . ?filter_entity {self.label_property} ?filter_on ."

            # Create the SPARQL appendix for the sorting
            filter_prop_str2 = f'FILTER(CONTAINS(LCASE(STR(?filter_on)), LCASE("{normalize_text(filter_value)}")))'
        else:
            # ie: no filter
            filter_prop_str1 = ""
            filter_prop_str2 = ""

        # Small inner function to build the SPARQL "select" text for a given property
        def get_select_property(property: OntoProperty, index: int) -> str:
            # Get the SPARQL label of the column (label to snake case)
            property_label = f"{to_snake_case(property.label).replace('-', '_')}_{index}"
            if cls.uri == property.domain_class_uri: # i.e. is outgoing
                return f"(GROUP_CONCAT(DISTINCT COALESCE(?{property_label}_, ''); separator=\" - \") as ?{property_label})"
            else: # i.e. is incoming
                return f"(GROUP_CONCAT(DISTINCT COALESCE(?{property_label}_, ''); separator=\" - \") as ?{property_label}_inc)"
            
        # Small inner function to build the SPARQL "where" text for a given property
        def get_where_property(property: OntoProperty, index: int) -> str:
            # Get the property URI
            property_uri = self.sparql.prepare_uri(property.uri)
            # Get the SPARQL label of the column (label to snake case)
            property_label = f"{to_snake_case(property.label).replace('-', '_')}_{index}"
            if cls.uri == property.domain_class_uri: # i.e. is outgoing
                # When the property is already a "value property" (label, comment, or other values),
                # directly retrieve it
                if property_uri == self.label_property or property_uri == self.comment_property or property.range_is_value():
                    return "OPTIONAL { " + f"?uri_ {property_uri} ?{property_label}_" + " . }"
                else:
                    # Because we want to display labels and not URIs in the data table cells, once ranges are fetched, 
                    # get the label out of ranges
                    return "OPTIONAL { " + f"?uri_ {property_uri} ?{property_label}_uri" + " . " + \
                        "OPTIONAL { " + f"?{property_label}_uri {self.label_property} ?{property_label}_" + " . } }"
            else: # i.e. is incoming ("value properties" is impossible here)
                # Because we want to display labels and not URIs in the data table cells, once domains are fetched, 
                # get the label out of domains
                return "OPTIONAL { " + f"?{property_label}_uri {property_uri} ?uri_" + " . " + \
                        "OPTIONAL { " + f"?{property_label}_uri {self.label_property} ?{property_label}_" + " . } }"


        ### Prepare the query ###

        # Make sure the class URI is correctly formated
        class_uri = self.sparql.prepare_uri(cls.uri)
        
        # Add information about the graph
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""

        # For each wanted properties, used the small inner function to build SPARQL "select" text
        select_properties = "\n                ".join([get_select_property(prop, i) for i, prop in enumerate(wanted_properties)])
        # For each wanted properties, used the small inner function to build SPARQL "where" text
        where_properties = "\n                    ".join([get_where_property(prop, i) for i, prop in enumerate(wanted_properties)])

        # Add the pagination
        limit = f"LIMIT {limit}" if limit else ""
        offset = f"OFFSET {offset}" if offset else ""

        # And finally build the query text
        query = """
            # DataBundle.get_data_table()
            SELECT
                (COALESCE(?uri_, '') as ?uri)
                """ + select_properties + """
            WHERE {
                """ + graph_begin + """
                    { 
                        SELECT ?uri_ 
                        WHERE { 
                            ?uri_ """ + self.type_property + """ """ + class_uri + """ . 
                            """ + filter_prop_str1 + """
                            """  + sort_prop_str1 + """
                            """ + filter_prop_str2 + """
                        } 
                        """ + order_by + """
                        """ + offset + """
                        """ + limit + """
                    }
                    """ + where_properties + """
                """ + graph_end + """
            }
            GROUP BY ?uri_
        """


        ### Execution ###

        # Execute the query (fetch instances with labels etc)
        instances = self.graph_data.sparql.run(query)

        # For each class instance, count outgoings triples number
        uris = list(map(lambda record: self.sparql.prepare_uri(record['uri']), instances))
        outgoings = self.graph_data.sparql.run(f"""
            SELECT ?uri (COALESCE(COUNT(?outgoing), '0') as ?outgoing_count) 
            WHERE {{
                {graph_begin}
                    VALUES ?uri {{ {' '.join(uris)} }}
                    ?uri ?p ?outgoing .
                {graph_end}
            }} GROUP BY ?uri
        """)
        outgoings = pd.DataFrame(outgoings)

        # For each class instance, count incoming triples number
        incomings = self.graph_data.sparql.run(f"""
            SELECT ?uri (COALESCE(COUNT(?incoming), '0') as ?incoming_count) 
            WHERE {{
                {graph_begin}
                    VALUES ?uri {{ {' '.join(uris)} }}
                    ?incoming ?p ?uri .
                {graph_end}
            }} GROUP BY ?uri
        """)
        incomings = pd.DataFrame(incomings)


        ### Create the final DataFrame ###

        df = pd.DataFrame(data=instances)

        # Append the outgoings counts
        if len(outgoings): 
            df = df.merge(outgoings, how='left')
            df['outgoing_count'].fillna(0, inplace=True)
        else: df['outgoing_count'] = "0"

        # Append the incoming counts
        if len(incomings): 
            df = df.merge(incomings, how='left')
            df['incoming_count'].fillna(0, inplace=True)
        else: df['incoming_count'] = "0"

        # Reformat column names
        df.columns = [from_snake_case(col).replace(' Inc', ' (inc)') for col in df.columns]
        df.rename(columns={'Uri': 'URI'}, inplace=True)

        return df
    

    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name), "model.onto_entity.OntoEntity": lambda x: hash(x.uri)})
    def get_class_count(self, cls: OntoEntity, filter_col_name: str = None, filter_content: str = None) -> int:    
        """
        Look in the given graph how much instances of given class there is.
        Filter on a property can be added.
        
        Args:
            cls (OntoEntity): Class to count instances.
            filter_col_name (str): Column (property) name to add a filter to count. Should be present in the data table columns.
            filter_content (str): Value to filter filter_col_name on.

        Returns:
            int: the number of instances validating the filter if present.
        """

        # Prepare the filter text
        filter_ = ""
        if filter_col_name and filter_content:

            # Find the property to filter on
            properties = self.ontology.get_properties()
            wanted_properties = [prop for prop in properties if prop.card_of_class_uri == cls.uri]
            target_property = [prop for prop in wanted_properties if prop.label == filter_col_name.replace('(inc)', '').strip()][0]

            if '(inc)' in filter_col_name: # i.e. property is incoming
                filter_ = f'?value {self.sparql.prepare_uri(target_property.uri)} ?uri . ?value {self.label_property} ?label . FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{filter_content}")))'
            else: # i.e. property is outgoing
                filter_ = f'?uri {self.sparql.prepare_uri(target_property.uri)} ?value . ?value {self.label_property} ?label . FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{filter_content}")))'

        ### Prepare the query ###

        # Make sure the class URI is correctly formated
        class_uri = self.sparql.prepare_uri(cls.uri)

        # Add information about the graph
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""

        # And finally build the query text
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
    def get_entity_infos(self, uri: str) -> OntoEntity:
        """
        Find the basic info needed for a given entity.

        Args:
            uri (str): The URI of the entity to fetch basic information from.

        Retuns:
            OntoEntity: Instance of OntoEntity filled with basic informations (label, comment, class URI, class label)
        """

        # Make sure the URI is correctly formated
        entity_uri = self.sparql.prepare_uri(uri)

        # Add information about the graph
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""

        # Build the query text
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
        # The error catching is done to prevent to have a "normal error"
        # If the given URI is actually a string like "hello world", the request will fail, but because of ontological reason, 
        # we do not want an error, so we returns None.
        # Up to the caller to handle this case
        try: infos = self.graph_data.sparql.run(query)[0]
        except: return None

        # Add the class information (label):
        classes = self.ontology.get_classes()
        class_label = list(filter(lambda c: c.uri == infos.get('class_uri'), classes))[0].label

        # Return a filled instance
        return OntoEntity(
            uri=uri,
            label=infos.get('label'),
            comment=infos.get('comment'),
            class_uri=infos.get('class_uri'),
            class_label=class_label
        )


    def dump(self, format: Literal['nq', 'ttl', 'csv']) -> str | dict[str, str | pd.DataFrame]:
        """
        Create a dump of the Data Bundle.
        Parameter allows to chose the dump format.

        Args:
            format ('nq', 'ttl', 'csv'): The format of the dump.

        Retuns:
            str, or dict of key - string values, or dict of key - DataFrame values.

        """

        # n-Quads
        if format == 'nq': 
            # In nq format, triples are actually not triples, but quads.
            # It means that all information are in actually one single file, with graph information in it.
            # Therefore, everything can be return as a single string.
            content = ""
            content += self.graph_data.dump_nquad() # Add the data bundle data
            content += self.graph_ontology.dump_nquad() # Add the data bundle model
            content += self.graph_metadata.dump_nquad() # Add the data bundle metadata
            return content

        # Turtle
        if format == 'ttl':
            # In ttl format, graph information are not present.
            # Therefore, there is the need to split information in 3 differents extractions (data, model, metadata)
            # Hence the returned thing is a dictionary of strings (data, model, metadata)
            return {
                "data": self.graph_data.dump_turtle(), # Data bundle data
                "ontology": self.graph_ontology.dump_turtle(), # Data bundle model
                "metadata": self.graph_metadata.dump_turtle(), # Data bundle metadata
            }

        # CSV extractions
        if format == 'csv':
            # The CSV format dump is different than the two other format:
            # Two others extract raw triples, usefull to make saving or to publish, or to import in another SPARQL endpoint
            # But the CSV dump is more for humans:
            # Basically, CSV dump will have a single CSV for each class present in the data bunlde data named graph.
            # And each Class CSV will have as columns, outgoings property names of properties, and as cells, the values of the right triples (as URI)

            # Also, add 2 additional CSV which basically adds the model to the dump: one for classes, and one for properties
            to_return = {
                'ontology-classes': pd.DataFrame(data=[cls.to_dict() for cls in self.ontology.get_classes()]),
                'ontology-properties': pd.DataFrame(data=[prop.to_dict() for prop in self.ontology.get_properties()]),
            }

            # Build all the classes DataFrames
            for cls in self.ontology.get_classes():
                to_return[to_snake_case(cls.display_label)] = self.__download_class(cls)

            return to_return
        

    @st.cache_data(show_spinner=False, ttl=10, hash_funcs={"model.data_bundle.DataBundle": lambda x: hash(x.name), "model.onto_entity.OntoEntity": lambda x: hash(x.uri)})
    def __download_class(self, cls: OntoEntity) -> pd.DataFrame:
        """
        List all instances with all properties (only those from the ontology) of a given class.
        
        Args:
            cls (OntoEntity): the class to get instances.

        Returns:
            DataFrame: Formated instances information.
        """
        
        # Get the ontology properties of this class (only outgoing)
        ontology_properties = self.ontology.get_properties()
        properties_outgoing = [prop for prop in ontology_properties if prop.domain_class_uri == cls.uri]
        properties_outgoing.sort(key=lambda x: x.order)

        # Prepare the query: make all lines from the query
        properties_outgoing_names = [f"(COALESCE(?{to_snake_case(prop.label).replace('-', '_')}_, '') as ?{to_snake_case(prop.label).replace('-', '_')})" for prop in properties_outgoing]
        properties_outgoing_names_str = '\n                '.join(properties_outgoing_names)
        triples_outgoings = [f"OPTIONAL {{ ?instance {prop.uri} ?{to_snake_case(prop.label).replace('-', '_')}_ . }}" for prop in properties_outgoing]
        triples_outgoings_str = '\n                    '.join(triples_outgoings)

        # Make sure the class URI is correctly formated
        class_uri = self.sparql.prepare_uri(cls.uri)

        # Add information about the graph
        graph_begin = "GRAPH " + self.graph_data.uri_ + " {" if self.graph_data.uri else ""
        graph_end = "}" if self.graph_data.uri else ""

        # Build the query text
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
        """
        Static method to convert an dictionary into a DataBundle instance.
        
        Args:
            obj (dict): the raw dictionary.
            sparql (SPARQL): the SPARQl instance to use for queries.

        Returns:
            DataBundle: Instance of the DataBundle.
        """

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


    def to_dict(self) -> dict:
        """
        Convert the Class instance into a dictionary.
        
        Returns:
            dict: dictionary representing all information needed to create the same instance (expect the SPARQL instance).
        """

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
    


    def __merge_ontology(self, query_result: list[dict]) -> List[Statement]:
        """
        From a list of statements (in form of dictionaries), merge the ontology information.
        This function is designed to work only in the class (private), but could also be used outside.

        Args: 
            query_result (list of dictionary): tThe list of raw statements (as fetched by queries). Despite raw, they need to have specific attributes (dict).

        Returns:
            list of Statement: List of formated statement, with additional information linked to the data bundle ontology.
        """

        # Fetch needed ontology informations
        classes_dict = self.ontology.get_classes_dict()
        properties_dict = self.ontology.get_properties_dict()

        # Merge the ontology information
        statements_raw = [{
            # Get attributes from left list (raw statement)
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