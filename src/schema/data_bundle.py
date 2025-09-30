from typing import List, Tuple, Dict, Literal
import pandas as pd
from graphly.schema import Sparql, Graph, Model, Resource, Prefixes, Property, Statement, Sparql, Prefix
from graphly.tools import prepare
from lib.utils import normalize_text, to_snake_case, from_snake_case
from .sparql_technologies import get_sparql_technology
from .model_framework import get_model_framework


class DataBundle:

    # Attributes
    name: str
    key: str
    base_uri: str

    # High level attributes
    prefixes: Prefixes
    endpoint: Sparql
    model: Model

    # Graphs
    graph_data: Graph
    graph_model: Graph
    graph_metadata: Graph


    def __init__(self, 
                 name: str, 
                 base_uri: str,
                 prefixes: Prefixes, 
                 endpoint_technology: str, 
                 endpoint_url: str, 
                 username: str, 
                 password: str, 
                 model_framework: str, 
                 prop_type_uri: str, 
                 prop_label_uri: str, 
                 prop_comment_uri: str, 
                 graph_data_uri: str, 
                 graph_model_uri: str, 
                 graph_metadata_uri: str, 
        ) -> None:
        """
        Initialize a data bundle with its configuration, SPARQL endpoint, model framework, and graphs.

        Args:
            name (str): The name of the data bundle.
            base_uri (str): The base URI for the data bundle.
            prefixes (Prefixes): The set of prefixes to use, extended with the base prefix.
            endpoint_technology (str): The technology used for the SPARQL endpoint.
            endpoint_url (str): The URL of the SPARQL endpoint.
            username (str): The username for authenticating with the endpoint.
            password (str): The password for authenticating with the endpoint.
            model_framework (str): The framework used to represent the model.
            prop_type_uri (str): The URI for the property type.
            prop_label_uri (str): The URI for the property label.
            prop_comment_uri (str): The URI for the property comment.
            graph_data_uri (str): The URI of the data graph.
            graph_model_uri (str): The URI of the model graph.
            graph_metadata_uri (str): The URI of the metadata graph.
        """
        # Attributes
        self.name = name
        self.key = to_snake_case(self.name.replace(' - ', '-')) # To have a URL compatible name
        self.base_uri = base_uri
        self.prefixes = Prefixes(prefixes.prefix_list + [Prefix('base', base_uri)])
        
        # Get the right SPARQL technology class
        SparqlClass = get_sparql_technology(endpoint_technology)
        self.endpoint = SparqlClass(endpoint_url, username, password)

        # Get the right model framework class
        ModelClass = get_model_framework(model_framework)
        self.model = ModelClass(self.prefixes.shorten(prop_type_uri), self.prefixes.shorten(prop_label_uri), self.prefixes.shorten(prop_comment_uri))

        # Set all the needed graphs
        self.graph_data = Graph(self.endpoint, graph_data_uri, self.prefixes)
        self.graph_model = Graph(self.endpoint, graph_model_uri, self.prefixes)
        self.graph_metadata = Graph(self.endpoint, graph_metadata_uri, self.prefixes)


    def load_model(self) -> None:
        """
        Load and update the model for the data bundle by fetching it from the model graph.

        Updates the current model with information from `graph_model` using the defined prefixes.
        """
        self.model.update(self.graph_model, self.prefixes) # Fetch the Model


    def delete(self, graph: Literal['data', 'model', 'metadata'], triples: List[Tuple[str, str, str]]) -> None:
        """
        Delete triples from the specified graph in the data bundle.

        Args:
            graph (Literal['data', 'model', 'metadata']): The graph from which to delete triples.
            triples (List[Tuple[str, str, str]]): The list of triples to delete, each represented as (subject, predicate, object).
        """
        if graph == 'data': self.graph_data.delete(triples, self.prefixes)
        if graph == 'model': self.graph_model.delete(triples, self.prefixes)
        if graph == 'metadata': self.graph_metadata.delete(triples, self.prefixes)


    def insert(self, graph: Literal['data', 'model', 'metadata'], triples: List[Tuple[str, str, str]]) -> None:
        """
        Insert triples into the specified graph in the data bundle.

        Args:
            graph (Literal['data', 'model', 'metadata']): The graph into which to insert triples.
            triples (List[Tuple[str, str, str]]): The list of triples to insert, each represented as (subject, predicate, object).
        """
        if graph == 'data': self.graph_data.insert(triples, self.prefixes)
        if graph == 'model': self.graph_model.insert(triples, self.prefixes)
        if graph == 'metadata': self.graph_metadata.insert(triples, self.prefixes)
    

    def run(self, text: str) -> List[Dict] | None:
        """
        Execute a SPARQL query against the configured endpoint.

        Args:
            text (str): The SPARQL query string to execute.

        Returns:
            List[Dict] | None: A list of result bindings if the query succeeds,
            or None if the execution fails.
        """
        return self.endpoint.run(text, self.prefixes)


    def find_entities(self, label: str = None, class_uri: str = None, limit: int | None = 10, offset: int | None = 0) -> List[Resource]:
        """
        Find entities in the data graph, optionally filtered by label and/or class.

        Executes a SPARQL query on the data graph to retrieve entities along with
        their URI, label, comment, and class. Results can be paginated with `limit`
        and `offset`.

        Args:
            label (str, optional): A label substring to filter entities by (case-insensitive).
            class_uri (str, optional): The URI of the class to filter entities by.
            limit (int | None, optional): The maximum number of entities to return. Defaults to 10.
            offset (int | None, optional): The number of entities to skip for pagination. Defaults to 0.

        Returns:
            List[Resource]: A list of resources matching the query.
        """
        # Prepare query
        label = label.replace("'", "\\'") if label else None
        filter_clause = f"FILTER(CONTAINS(LCASE(?label_), LCASE('{label}'))) ." if label else ""
        prepared_class_uri = prepare(class_uri, self.prefixes.shorts())
        query = f"""
            # DataBundle.find_entities()
            SELECT
                (?uri_ as ?uri)
                (COALESCE(?label_, '') as ?label)
                (COALESCE(?comment_, '') as ?comment)
                (COALESCE(?class_uri_, '{class_uri if class_uri else ""}') as ?class_uri)
            WHERE {{
                {self.graph_data.sparql_begin}
                    ?uri_ {self.model.type_property} {prepared_class_uri if prepared_class_uri else "?class_uri_"} .
                    OPTIONAL {{ ?uri_ {self.model.label_property} ?label_ . }}
                    OPTIONAL {{ ?uri_ {self.model.comment_property} ?comment_ . }}
                {self.graph_data.sparql_end}
                {filter_clause}
            }}
            {f"LIMIT {limit}" if limit else ""}
            {f"OFFSET {offset}" if offset else ""}
        """

        # Execute query
        response = self.graph_data.run(query, self.prefixes)

        # If there is no result, there is no point to go forward
        if not response: 
            return []
        
        # Parse response into Resource instance list
        resources = [Resource(r['uri'], r['label'], r['comment'], r['class_uri']) for r in response]

        return resources


    def get_outgoing_properties_of(self, entity: Resource) -> List[Property]:
        """
        Retrieve the outgoing properties of a given entity from the data graph.

        Executes a SPARQL query to find properties where the entity appears as the subject,
        optionally resolving the range class of the object. The properties are then
        enriched with model information such as labels and domains.

        Args:
            entity (Resource): The entity whose outgoing properties are retrieved.

        Returns:
            List[Property]: A list of properties outgoing from the given entity.
        """
        # Prepare the query
        entity_uri = prepare(entity.uri, self.prefixes.shorts())
        query = f"""
            SELECT DISTINCT 
                ?uri 
                (COALESCE(?range_class_uri_, '') as ?range_class_uri)
            WHERE {{ 
                {self.graph_data.sparql_begin}
                    {entity_uri} ?uri ?o . 
                    OPTIONAL {{ ?o {self.model.type_property} ?range_class_uri_ . }}
                {self.graph_data.sparql_end}
            }}
        """

        # Execute query
        response = self.graph_data.run(query, self.prefixes)

        # Find properties in model (for additional informations, labels, etc)
        domain_class_uri = entity.class_uri if entity.class_uri else None
        properties = [self.model.find_properties(prop['uri'], domain_class_uri=domain_class_uri, range_class_uri=prop['range_class_uri']) for prop in response]

        # Flatten the list
        properties = [p for props in properties for p in props]

        return properties
    

    def get_incoming_properties_of(self, entity: Resource) -> List[Property]:
        """
        Retrieve the incoming properties of a given entity from the data graph.

        Executes a SPARQL query to find properties where the entity appears as the object,
        optionally resolving the domain class of the subject. The properties are then
        enriched with model information such as labels and ranges.

        Args:
            entity (Resource): The entity whose incoming properties are retrieved.

        Returns:
            List[Property]: A list of properties incoming to the given entity.
        """
        # Prepare the query
        entity_uri = prepare(entity.uri, self.prefixes.shorts())
        query = f"""
            SELECT DISTINCT 
                ?uri 
                (COALESCE(?domain_class_uri_, '') as ?domain_class_uri)
            WHERE {{ 
                {self.graph_data.sparql_begin}
                    ?s ?uri {entity_uri} . 
                    OPTIONAL {{ ?s {self.model.type_property} ?domain_class_uri_ . }}
                {self.graph_data.sparql_end}
            }}
        """

        # Execute query
        response = self.graph_data.run(query, self.prefixes)

        # Find properties in model (for additional informations, labels, etc)
        range_class_uri = entity.class_uri if entity.class_uri else None
        properties = [self.model.find_properties(prop['uri'], domain_class_uri=prop['domain_class_uri'], range_class_uri=range_class_uri) for prop in response]

        # Flatten the list
        properties = [p for props in properties for p in props]

        return properties
    
        
    def get_card_properties_of(self, class_uri: str) -> List[Property]:
        """
        Retrieve the card properties of a given class from the model.

        Filters properties defined with a `card_of` matching the given class URI,
        and sorts them by their `order` attribute (properties without an order are placed last).

        Args:
            class_uri (str): The URI of the class whose card properties are retrieved.

        Returns:
            List[Property]: A sorted list of card properties for the class.
        """
        card_properties = [p for p in self.model.properties if p.card_of != None and p.card_of.uri == class_uri]
        card_properties.sort(key=lambda p: p.order or 10**18) 
        return card_properties


    def get_objects_of(self, entity: Resource, property: Property, limit: int = 5, offset: int = 0) -> List[Statement]:
        """
        Retrieve the objects of a given entity for a specific property from the data graph.

        Executes a SPARQL query to fetch objects linked to the entity by the property,
        including their URI, label, comment, class, and resource type. Results are
        deduplicated by object URI and returned as `Statement` instances.

        Args:
            entity (Resource): The subject entity whose objects are retrieved.
            property (Property): The property whose objects are retrieved.
            limit (int, optional): The maximum number of objects to return. Defaults to 5.
            offset (int, optional): The number of objects to skip for pagination. Defaults to 0.

        Returns:
            List[Statement]: A list of statements representing the entity-property-object triples.
        """
        # Prepare the query
        entity_uri = prepare(entity.uri, self.prefixes.shorts())
        property_uri = prepare(property.uri, self.prefixes.shorts())
        object_class_uri = prepare(property.range.uri if property.range else None, self.prefixes.shorts())
        is_range_datatype = property.range.class_uri == 'rdfs:Datatype' if property.range else False
        query = f"""
            # DataBundle.get_objects_of()
            SELECT
                ?object_uri
                (COALESCE(?object_label_, '') as ?object_label)
                (COALESCE(?object_comment_, '') as ?object_comment)
                (COALESCE(?object_class_uri_, IF(isLiteral(?object_uri), DATATYPE(?object_uri), '')) as ?object_class_uri)
                (IF(isIRI(?object_uri), 'iri', IF(isBlank(?object_uri), 'blank', IF(isLiteral(?object_uri), 'literal', ''))) as ?resource_type)
            WHERE {{
                {self.graph_data.sparql_begin}
                    {entity_uri} {property_uri} ?object_uri .
                    {f"?object_uri {self.model.type_property} {object_class_uri} ." if object_class_uri and not is_range_datatype else ""}
                    OPTIONAL {{ ?object_uri {self.model.label_property} ?object_label_ . }}
                    OPTIONAL {{ ?object_uri {self.model.comment_property} ?object_comment_ . }}
                    OPTIONAL {{ ?object_uri {self.model.type_property} ?object_class_uri_ . }}
                {self.graph_data.sparql_end}
            }}
            {f"LIMIT {limit}" if limit else ""}
            {f"OFFSET {offset}" if offset else ""}
        """

        # Execute query
        response = self.graph_data.run(query, self.prefixes)

        # Make it unique based on object URI (can have duplicates because of multiple lables, comments, ...)
        response = list({d["object_uri"]: d for d in reversed(response)}.values())

        # Parse response into Statement instance list
        statements = [Statement(
            entity,
            property,
            Resource(r['object_uri'], r['object_label'], r['object_comment'], r['object_class_uri'], r['resource_type'] or None),
        ) for r in response]

        return statements
    
    def get_objects_of_count(self, entity: Resource, property: Property) -> int:
        """
        Count the number of objects linked to a given entity by a specific property.

        Executes a SPARQL query to count all triples where the entity is the subject
        and the property is the predicate.

        Args:
            entity (Resource): The subject entity.
            property (Property): The property whose objects are counted.

        Returns:
            int: The number of objects associated with the entity via the property.
        """
        # Prepare the query
        entity_uri = prepare(entity.uri, self.prefixes.shorts())
        property_uri = prepare(property.uri, self.prefixes.shorts())
        query = f"""
            # DataBundle.get_objects_of_count()
            SELECT
                (COUNT(*) as ?count)
            WHERE {{
                {self.graph_data.sparql_begin}
                    {entity_uri} {property_uri} ?object_uri .
                {self.graph_data.sparql_end}
            }}
        """

        # Execute query
        response = self.graph_data.run(query, self.prefixes)

        return response[0]['count']


    def get_subjects_of(self, entity: Resource, property: Property, limit: int = 5, offset: int = 0) -> List[Statement]:
        """
        Retrieve the subjects of a given entity for a specific property from the data graph.

        Executes a SPARQL query to fetch subjects linked to the entity by the property,
        including their URI, label, comment, class, and resource type. Results are
        deduplicated by subject URI and returned as `Statement` instances.

        Args:
            entity (Resource): The object entity whose subjects are retrieved.
            property (Property): The property whose subjects are retrieved.
            limit (int, optional): The maximum number of subjects to return. Defaults to 5.
            offset (int, optional): The number of subjects to skip for pagination. Defaults to 0.

        Returns:
            List[Statement]: A list of statements representing the subject-property-entity triples.
        """
        # Prepare the query
        entity_uri = prepare(entity.uri, self.prefixes.shorts())
        property_uri = prepare(property.uri, self.prefixes.shorts())
        subject_class_uri = prepare(property.domain.uri if property.domain else None, self.prefixes.shorts())
        query = f"""
            # DataBundle.get_subjects_of()
            SELECT
                ?subject_uri
                (COALESCE(?subject_label_, '') as ?subject_label)
                (COALESCE(?subject_comment_, '') as ?subject_comment)
                (COALESCE(?subject_class_uri_, IF(isLiteral(?subject_uri), DATATYPE(?subject_uri), '')) as ?subject_class_uri)
                (IF(isIRI(?subject_uri), 'iri', IF(isBlank(?subject_uri), 'blank', IF(isLiteral(?subject_uri), 'literal', ''))) as ?resource_type)
            WHERE {{
                {self.graph_data.sparql_begin}
                    ?subject_uri {property_uri} {entity_uri} .
                    {f"?subject_uri {self.model.type_property} {subject_class_uri} ." if subject_class_uri else ""}
                    OPTIONAL {{ ?subject_uri {self.model.label_property} ?subject_label_ . }}
                    OPTIONAL {{ ?subject_uri {self.model.comment_property} ?subject_comment_ . }}
                    OPTIONAL {{ ?subject_uri {self.model.type_property} ?subject_class_uri_ . }}
                {self.graph_data.sparql_end}
            }}
            {f"LIMIT {limit}" if limit else ""}
            {f"OFFSET {offset}" if offset else ""}
        """

        # Execute query
        response = self.graph_data.run(query, self.prefixes)

        # Make it unique based on subject URI (can have duplicates because of multiple lables, comments, ...)
        response = list({d["subject_uri"]: d for d in reversed(response)}.values())

        # Parse response into Statement instance list
        statements = [Statement(
            Resource(r['subject_uri'], r['subject_label'], r['subject_comment'], r['subject_class_uri'], r['resource_type'] or None),
            property,
            entity,
        ) for r in response]

        return statements
    

    def get_subjects_of_count(self, entity: Resource, property: Property) -> int:
        """
        Count the number of subjects linked to a given entity by a specific property.

        Executes a SPARQL query to count all triples where the property points to the entity
        as the object.

        Args:
            entity (Resource): The object entity.
            property (Property): The property whose subjects are counted.

        Returns:
            int: The number of subjects associated with the entity via the property.
        """
        # Prepare the query
        entity_uri = prepare(entity.uri, self.prefixes.shorts())
        property_uri = prepare(property.uri, self.prefixes.shorts())
        query = f"""
            # DataBundle.get_objects_of_count()
            SELECT
                (COUNT(*) as ?count)
            WHERE {{
                {self.graph_data.sparql_begin}
                    ?subject_uri {property_uri} {entity_uri} .
                {self.graph_data.sparql_end}
            }}
        """

        # Execute query
        response = self.graph_data.run(query, self.prefixes)

        return response[0]['count']
    

    def get_outgoing_statements_of(self, entity: Resource, skip_props: List[Property] = []) -> List[Statement]:
        """
        Retrieve all outgoing statements of a given entity from the data graph, optionally skipping specified properties.

        Executes a SPARQL query to fetch all triples where the entity is the subject,
        including object URI, label, class, and resource type. Skipped properties are
        excluded from the results.

        Args:
            entity (Resource): The subject entity whose outgoing statements are retrieved.
            skip_props (List[Property], optional): A list of properties to exclude from the results.

        Returns:
            List[Statement]: A list of statements representing the outgoing triples.
        """
        # Prepare the query
        entity_uri = prepare(entity.uri, self.prefixes.shorts())
        skip_prop_str = ', '.join(list(set([prepare(p.uri, self.prefixes.shorts()) for p in skip_props]))) if len(skip_props) != 0 else ''
        query = f"""
            # DataBundle.get_all_outgoing_statements()
            SELECT 
                ?p ?o (isLiteral(?o) as ?is_literal) 
                (COALESCE(?o_label_, '') as ?o_label)
                (COALESCE(?o_class_uri_, '') as ?o_class_uri)
            WHERE {{ 
                {self.graph_data.sparql_begin}
                    {entity_uri} ?p ?o  .
                    OPTIONAL {{ ?o {self.model.type_property} ?o_class_uri_ . }}
                    OPTIONAL {{ ?o {self.model.label_property} ?o_label_ . }}
                    {f"FILTER(?p NOT IN ({skip_prop_str}))" if len(skip_props) else ""}
                {self.graph_data.sparql_end}
            }}
        """

        # Execute query
        response = self.graph_data.run(query, self.prefixes)

        # Parse into Statmeents
        to_return = [Statement(entity, self.model.find_properties(r['p'])[0], Resource(r['o'], r['o_label'], class_uri=r['o_class_uri'], resource_type='literal' if r['is_literal'] == 'true' else 'iri')) for r in response]

        return to_return
    
    
    def get_incoming_statements_of(self, entity: Resource, limit: int = 5, offset: int = 0, skip_props: List[Property] = []) -> List[Statement]:
        """
        Retrieve incoming statements for a given entity from the data graph, optionally skipping specified properties.

        Executes a SPARQL query to fetch all triples where the entity is the object,
        including subject URI, label, and class. Skipped properties are excluded from the results.

        Args:
            entity (Resource): The object entity whose incoming statements are retrieved.
            limit (int, optional): The maximum number of statements to return. Defaults to 5.
            offset (int, optional): The number of statements to skip for pagination. Defaults to 0.
            skip_props (List[Property], optional): A list of properties to exclude from the results.

        Returns:
            List[Statement]: A list of statements representing the incoming triples.
        """
        # Prepare the query
        entity_uri = prepare(entity.uri, self.prefixes.shorts())
        skip_prop_str = ', '.join(list(set([prepare(p.uri, self.prefixes.shorts()) for p in skip_props]))) if len(skip_props) != 0 else ''
        query = f"""
            # DataBundle.get_all_outgoing_statements()
            SELECT 
                ?s ?p
                (COALESCE(?s_label_, '') as ?s_label)
                (COALESCE(?s_class_uri_, '') as ?s_class_uri)
            WHERE {{ 
                {self.graph_data.sparql_begin}
                    ?s ?p {entity_uri} .
                    OPTIONAL {{ ?s {self.model.type_property} ?s_class_uri_ . }}
                    OPTIONAL {{ ?s {self.model.label_property} ?s_label_ . }}
                    {f"FILTER(?p NOT IN ({skip_prop_str}))" if len(skip_props) else ""}
                {self.graph_data.sparql_end}
            }}
            LIMIT {limit}
            OFFSET {offset}
        """

        # Execute query
        response = self.graph_data.run(query, self.prefixes)

        # Parse into Statmeents
        to_return = [Statement(Resource(r['s'], r['s_label'], class_uri=r['s_class_uri']), self.model.find_properties(r['p'])[0], entity) for r in response]

        return to_return
    

    def get_incoming_statements_of_count(self, entity: Resource) -> List[Statement]:
        """
        Count the number of incoming statements for a given entity, excluding type, label, and comment properties.

        Executes a SPARQL query to count all triples where the entity is the object
        and filters out statements using the model's type, label, and comment properties.

        Args:
            entity (Resource): The object entity whose incoming statements are counted.

        Returns:
            int: The number of incoming statements for the entity.
        """
        # Prepare the query
        entity_uri = prepare(entity.uri, self.prefixes.shorts())
        query = f"""
            # DataBundle.get_all_outgoing_statements()
            SELECT (COUNT(*) as ?count)
            WHERE {{ 
                {self.graph_data.sparql_begin}
                    ?s ?p {entity_uri} .
                    FILTER(?p NOT IN ({self.model.type_property}, {self.model.label_property}, {self.model.comment_property}))
                {self.graph_data.sparql_end}
            }}
        """

        # Execute query
        response = self.graph_data.run(query, self.prefixes)

        return response[0]['count']
        

    def __data_table_prepare_sorting(self, sort_col: str, sort_way: str, needed_properties: List[Property], class_uri: str) -> Tuple[str, str]:
        """
        Prepare the SPARQL components for sorting a data table by a specified column.

        Determines the SPARQL pattern needed to sort by the given property, handling
        outgoing vs. incoming properties and whether the property is a literal or requires
        fetching a label. Also generates the ORDER BY clause based on the sorting direction.

        Args:
            sort_col (str): The column label to sort by, or None for no sorting.
            sort_way (str): The sorting direction, either 'ASC' or 'DESC'.
            needed_properties (List[Property]): The list of properties available for the class.
            class_uri (str): The URI of the class for which the data table is built.

        Returns:
            Tuple[str, str]: A tuple containing the SPARQL pattern for sorting and the ORDER BY clause.
        """
        # Prepare sorting
        if sort_col is not None:
            clean_sort_col = sort_col[:sort_col.index(' (')]
            # Find the property with the given label
            sort_prop = next(prop for prop in needed_properties if prop.label == clean_sort_col)
            if sort_prop.domain.uri == class_uri: # ie: is outgoing
                if sort_prop.range.class_uri == 'rdfs:Datatype': # ie: no need to get the label
                    sort_prop = f"?uri_ {prepare(sort_prop.uri, self.prefixes.shorts())} ?sort_on ."
                else: # ie: need extra path to the label
                    sort_prop = f"?uri_ {prepare(sort_prop.uri, self.prefixes.shorts())} ?sort_entity . ?sort_entity {self.model.label_property} ?sort_on ."
            else: # ie: is incoming
                if sort_prop.range.class_uri == 'rdfs:Datatype': # ie: no need to get the label
                    sort_prop = f"?sort_on {prepare(sort_prop.uri, self.prefixes.shorts())} ?uri_ ."
                else: # ie: need extra path to the label
                    sort_prop = f"?sort_entity {prepare(sort_prop.uri, self.prefixes.shorts())} ?uri_ . ?sort_entity {self.model.label_property} ?sort_on ."

            # Create the SPARQL appendix for the sorting
            if sort_way == 'ASC': order_by = "ORDER BY ASC(?sort_on)"
            else: order_by = "ORDER BY DESC(?sort_on)"
        else: # ie: no sorting
            sort_prop = ""
            order_by = ""
        
        return sort_prop, order_by


    def __data_table_prepare_filtering(self, filter_col: str, filter_value: str, needed_properties: List[Property], class_uri: str) -> Tuple[str, str]:
        """
        Prepare the SPARQL components for filtering a data table by a specified column and value.

        Determines the SPARQL pattern needed to filter by the given property, handling
        outgoing vs. incoming properties and whether the property is a literal or requires
        fetching a label. Generates a FILTER clause that performs a case-insensitive
        substring match on the filter value.

        Args:
            filter_col (str): The column label to filter by, or None for no filtering.
            filter_value (str): The value to filter on.
            needed_properties (List[Property]): The list of properties available for the class.
            class_uri (str): The URI of the class for which the data table is built.

        Returns:
            Tuple[str, str]: A tuple containing the SPARQL pattern for filtering and the FILTER clause.
        """
        if filter_col is not None:
            clean_filter_col = filter_col[:filter_col.index(' (')]
            # Find the property with the given label
            filter_prop = list(filter(lambda prop: prop.label == clean_filter_col, needed_properties))[0]
            if filter_prop.domain.uri == class_uri: # ie: is outgoing
                if filter_prop.range.class_uri == 'rdfs:Datatype': # ie: no need to get the label
                    filter_prop_str1 = f"?uri_ {prepare(filter_prop.uri, self.prefixes.shorts())} ?filter_on ."
                else: # ie: need extra path to the label
                    filter_prop_str1 = f"?uri_ {prepare(filter_prop.uri, self.prefixes.shorts())} ?filter_entity . ?filter_entity {self.model.label_property} ?filter_on ."
            else: # ie: is incoming
                if filter_prop.range.class_uri == 'rdfs:Datatype': # ie: no need to get the label
                    filter_prop_str1 = f"?filter_on {prepare(filter_prop.uri, self.prefixes.shorts())} ?uri_ ."
                else: # ie: need extra path to the label
                    filter_prop_str1 = f"?filter_entity {prepare(filter_prop.uri, self.prefixes.shorts())} ?uri_ . ?filter_entity {self.model.label_property} ?filter_on ."

            # Create the SPARQL appendix for the sorting
            filter_prop_str2 = f'FILTER(CONTAINS(LCASE(STR(?filter_on)), LCASE("{normalize_text(filter_value)}")))'
        else: # ie: no filter
            filter_prop_str1 = ""
            filter_prop_str2 = ""

        return filter_prop_str1, filter_prop_str2
        

    def __data_table_get_select_property(self, property: Property, index: int, class_uri: str) -> str:
        """
        Generate the SPARQL SELECT expression for a property in a data table query.

        Creates a GROUP_CONCAT expression to aggregate values for the property, handling
        outgoing and incoming properties differently. The resulting variable name is
        made unique using the property label and index.

        Args:
            property (Property): The property for which the SELECT expression is generated.
            index (int): The index to append to the variable name to ensure uniqueness.
            class_uri (str): The URI of the class for which the data table is built.

        Returns:
            str: The SPARQL SELECT expression for the property.
        """
        # Get the SPARQL label of the column (label to snake case)
        # Prepend an index, to make sure that it will work even with same labelled properties (eg "is participation of")
        property_label = f"{to_snake_case(property.label)}_{index}"
        property_label = property_label.replace('-', '_').replace("'", "_")
        if property.domain and class_uri == property.domain.uri: # i.e. is outgoing
            return f"(GROUP_CONCAT(DISTINCT COALESCE(?{property_label}_, ''); separator=\" - \") as ?{property_label})"
        else: # i.e. is incoming
            return f"(GROUP_CONCAT(DISTINCT COALESCE(?{property_label}_, ''); separator=\" - \") as ?{property_label}_inc)"


    def __data_table_get_where_property(self, property: Property, index: int, class_uri: str) -> str:
        """
        Generate the SPARQL WHERE clause for a property in a data table query.

        Creates an OPTIONAL pattern to retrieve the property's values for a given class,
        handling outgoing and incoming properties differently. For object properties,
        fetches the labels instead of URIs for display in the data table.

        Args:
            property (Property): The property for which the WHERE clause is generated.
            index (int): The index to append to variable names to ensure uniqueness.
            class_uri (str): The URI of the class for which the data table is built.

        Returns:
            str: The SPARQL WHERE clause fragment for the property.
        """
        # Get the property URI
        property_uri = prepare(property.uri, self.prefixes.shorts())
        # Get the SPARQL label of the column (label to snake case)
        # Prepend an index, to make sure that it will work even with same labelled properties (eg "is participation of")
        property_label = f"{to_snake_case(property.label)}_{index}"
        property_label = property_label.replace('-', '_').replace("'", "_")
        if property.domain and class_uri == property.domain.uri: # i.e. is outgoing
            # When the property is already a "value property" (label, comment, or other values), directly retrieve the value
            if property_uri == self.model.label_property or property_uri == self.model.comment_property or property.range.class_uri == 'rdfs:Datatype':
                return "OPTIONAL { " + f"?uri_ {property_uri} ?{property_label}_" + " . }"
            else:
                # Because we want to display labels and not URIs in the data table cells, once ranges are fetched, get the label out of them
                return "OPTIONAL { " + f"?uri_ {property_uri} ?{property_label}_uri" + " . " + \
                    "OPTIONAL { " + f"?{property_label}_uri {self.model.label_property} ?{property_label}_" + " . } }"
        else: # i.e. is incoming ("value properties" are impossible here)
            # Because we want to display labels and not URIs in the data table cells, once domains are fetched, get the label out of them
            return "OPTIONAL { " + f"?{property_label}_uri {property_uri} ?uri_" + " . " + \
                    "OPTIONAL { " + f"?{property_label}_uri {self.model.label_property} ?{property_label}_" + " . } }"


    def get_data_table_columns_names(self, cls: Resource) -> List[str]:
        """
        Get the display names of the data table columns for a given class.

        Filters properties that are associated with the class as cards, sorts them
        by their order attribute, and formats them as "label (range label)".

        Args:
            cls (Resource): The class whose data table column names are retrieved.

        Returns:
            List[str]: A list of column names for the data table.
        """
        needed_properties = [prop for prop in self.model.properties if prop.card_of and prop.card_of.uri == cls.uri]
        needed_properties.sort(key=lambda x: x.order or 10**18)
        return [f"{p.label} ({p.range.label})" for p in needed_properties]


    def get_data_table(self, cls: Resource, limit: int = None, offset: int = 0, sort_col: str = None, sort_way: str = None, filter_col: str = None, filter_value: str = None) -> pd.DataFrame:
        """
        Generate a data table for a given class, optionally supporting pagination, sorting, and filtering.

        Builds and executes a SPARQL query to fetch all instances of the class, along with
        their card properties. Supports filtering by a specific column and value, sorting
        by a column, and paginating results with limit and offset. Also computes counts
        of incoming and outgoing triples for each instance and returns a formatted DataFrame.

        Args:
            cls (Resource): The class whose data table is generated.
            limit (int, optional): Maximum number of instances to return. Defaults to None (no limit).
            offset (int, optional): Number of instances to skip for pagination. Defaults to 0.
            sort_col (str, optional): Column label to sort by. Defaults to None.
            sort_way (str, optional): Sorting direction, 'ASC' or 'DESC'. Defaults to None.
            filter_col (str, optional): Column label to filter by. Defaults to None.
            filter_value (str, optional): Value to filter the column by. Defaults to None.

        Returns:
            pd.DataFrame: A DataFrame containing the instances, their properties, and counts of incoming and outgoing triples.
        """
        # List all wanted properties for this class (according to ontology)
        needed_properties = [prop for prop in self.model.properties if prop.card_of and prop.card_of.uri == cls.uri]
        needed_properties.sort(key=lambda x: x.order or 10**18)

        # Prepare Sorting
        sort_prop_str1, order_by = self.__data_table_prepare_sorting(sort_col, sort_way, needed_properties, cls.uri)

        # Prepare filtering
        filter_prop_str1, filter_prop_str2 = self.__data_table_prepare_filtering(filter_col, filter_value, needed_properties, cls.uri)

        # Make sure the class URI is correctly formated
        class_uri = prepare(cls.uri, self.prefixes.shorts())

        # For each wanted properties, used the small private function to build SPARQL "select" text
        select_properties = "\n                ".join([self.__data_table_get_select_property(prop, i, class_uri) for i, prop in enumerate(needed_properties)])
        # For each wanted properties, used the small private function to build SPARQL "where" text
        where_properties = "\n                    ".join([self.__data_table_get_where_property(prop, i, class_uri) for i, prop in enumerate(needed_properties)])

        # Add the pagination
        limit = f"LIMIT {limit}" if limit else ""
        offset = f"OFFSET {offset}" if offset else ""

        # Build the query
        query = f"""
            # DataBundle.get_data_table()
            SELECT
                (COALESCE(?uri_, '') as ?uri)
                {select_properties}
            WHERE {{
                {self.graph_data.sparql_begin}
                    {{
                        SELECT ?uri_ 
                        WHERE {{ 
                            ?uri_ {self.model.type_property} {class_uri} . 
                            {filter_prop_str1}
                            {sort_prop_str1}
                            {filter_prop_str2}
                        }}
                        {order_by}
                        {offset}
                        {limit}
                    }}
                    {where_properties}
                {self.graph_data.sparql_end}
            }}
            GROUP BY ?uri_
        """

        # Execute the query (fetch instances with labels etc)
        instances = self.graph_data.sparql.run(query, self.prefixes)

        # For each class instance, count outgoings triples number
        uris = list(map(lambda record: prepare(record['uri'], self.prefixes.shorts()), instances))
        outgoings = self.graph_data.sparql.run(f"""
            DataBundle.get_data_table() request 2: outgoing count
            SELECT ?uri (COALESCE(COUNT(?outgoing), '0') as ?outgoing_count) 
            WHERE {{
                {self.graph_data.sparql_begin}
                    VALUES ?uri {{ {' '.join(uris)} }}
                    ?uri ?p ?outgoing .
                {self.graph_data.sparql_end}
            }} GROUP BY ?uri
        """, self.prefixes)
        outgoings = pd.DataFrame(outgoings)

        # For each class instance, count incoming triples number
        incomings = self.graph_data.sparql.run(f"""
            DataBundle.get_data_table() request 3: incoming count
            SELECT ?uri (COALESCE(COUNT(?incoming), '0') as ?incoming_count) 
            WHERE {{
                {self.graph_data.sparql_begin}
                    VALUES ?uri {{ {' '.join(uris)} }}
                    ?incoming ?p ?uri .
                {self.graph_data.sparql_end}
            }} GROUP BY ?uri
        """, self.prefixes)
        incomings = pd.DataFrame(incomings)

        # Final DataFrame
        df = pd.DataFrame(data=instances)

        # Append the outgoings counts
        if len(outgoings): 
            df = df.merge(outgoings, how='left').copy()
            df['outgoing_count'] = df['outgoing_count'].fillna(0)
        else: df['outgoing_count'] = "0"

        # Append the incoming counts
        if len(incomings): 
            df = df.merge(incomings, how='left').copy()
            df['incoming_count'] = df['incoming_count'].fillna(0)
        else: df['incoming_count'] = "0"

        # Reformat column names
        df.columns = [from_snake_case(col).replace(' Inc', ' (inc)') for col in df.columns]
        df.rename(columns={'Uri': 'URI'})

        return df
    

    def get_class_instances_count(self, cls: Resource, filter_col_name: str = None, filter_content: str = None) -> int:    
        """
        Count the number of instances of a given class, optionally applying a filter on a property.

        Builds and executes a SPARQL query to count instances of the class. If a filter
        column and value are provided, only instances matching the filter are counted.
        Supports filtering on both outgoing and incoming properties.

        Args:
            cls (Resource): The class whose instances are counted.
            filter_col_name (str, optional): The label of the property to filter on. Defaults to None.
            filter_content (str, optional): The value to filter the property by. Defaults to None.

        Returns:
            int: The number of class instances matching the criteria.
        """
        # Prepare the filter text
        filter_ = ""
        if filter_col_name and filter_content:
            # List all wanted properties for this class (according to ontology)
            needed_properties = [prop for prop in self.model.properties if prop.card_of.uri == cls.uri]
            needed_properties.sort(key=lambda x: x.order)

            # Find the property to filter on
            target_property = next(prop for prop in needed_properties if prop.label == filter_col_name.replace('(inc)', '').strip())

            if '(inc)' in filter_col_name: # i.e. property is incoming
                filter_ = f'?value {prepare(target_property.uri, self.prefixes.shorts())} ?uri . ?value {self.model.label_property} ?label . FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{filter_content}")))'
            else: # i.e. property is outgoing
                filter_ = f'?uri {prepare(target_property.uri, self.prefixes.shorts())} ?value . ?value {self.model.label_property} ?label . FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{filter_content}")))'

        # Make sure the class URI is correctly formated
        class_uri = prepare(cls.uri, self.prefixes.shorts())

        # Build the query
        query = f"""
            # DataBundle.get_class_count()
            SELECT (COUNT(?uri) AS ?count)
            WHERE {{
                {self.graph_data.sparql_begin}
                    ?uri {self.model.type_property} {class_uri} .
                    {filter_}
                {self.graph_data.sparql_end}
            }}
        """

        # Execute the query (count instances)
        counts = self.graph_data.sparql.run(query)
        
        return int(counts[0]['count'])


    def get_entity_basics(self, uri: str) -> Resource:
        """
        Retrieve basic information about an entity, including its label, comment, and class.

        Executes a SPARQL query to fetch optional details for the entity URI and returns
        them as a Resource object.

        Args:
            uri (str): The URI of the entity to retrieve.

        Returns:
            Resource: An object containing the entity's URI, label, comment, and class URI.
        """
        # Make sure the URI is correctly formated
        entity_uri = prepare(uri, self.prefixes.shorts())

        # Build the query text
        query = f"""
            # DataBundle.get_entity_basics()
            SELECT 
                (COALESCE(?label_, '') as ?label)
                (COALESCE(?comment_, '') as ?comment)
                (COALESCE(?class_uri_, '') as ?class_uri)
            WHERE {{
                {self.graph_data.sparql_begin}
                    OPTIONAL {{ {entity_uri} {self.model.label_property} ?label_ . }}
                    OPTIONAL {{ {entity_uri} {self.model.comment_property} ?comment_ . }}
                    OPTIONAL {{ {entity_uri} {self.model.type_property} ?class_uri_ . }}
                {self.graph_data.sparql_end}
            }}
        """

        # Execute the query
        infos = self.graph_data.run(query, self.prefixes)[0]

        # Build the resource
        resource = Resource(uri, infos['label'], infos['comment'], infos['class_uri'])

        return resource


    def dump_nq(self) -> str:
        """
        Export the entire data bundle in N-Quads (NQ) format as a single string.

        Combines the model, data, and metadata graphs into a single N-Quads representation,
        including graph information for each triple.

        Returns:
            str: The N-Quads representation of the data bundle.
        """
        # In nq format, triples are actually not triples, but quads.
        # It means that all information are in actually one single file, with graph information in it.
        # Therefore, everything can be return as a single string.
        content = ""
        content += self.graph_model.dump_nquad(self.prefixes) # Add the data bundle model
        content += self.graph_data.dump_nquad(self.prefixes) # Add the data bundle data
        content += self.graph_metadata.dump_nquad(self.prefixes) # Add the data bundle metadata
        return content


    def dump_ttl(self) -> Dict[str, str]:
        """
        Export the data bundle in Turtle (TTL) format, split by graph type.

        Since Turtle format does not include graph information, the data, model, and
        metadata graphs are exported separately. Returns a dictionary mapping graph
        types to their TTL string representation.

        Returns:
            Dict[str, str]: A dictionary with keys 'data', 'model', 'metadata' and their
                            corresponding Turtle content as values.
        """
        # In ttl format, graph information are not present.
        # Therefore, there is the need to split information in 3 differents extractions (data, model, metadata)
        # Hence the returned thing is a dictionary of strings (data, model, metadata)
        return {
            "data": self.graph_data.dump_turtle(self.prefixes), # Data bundle data
            "model": self.graph_model.dump_turtle(self.prefixes), # Data bundle model
            "metadata": self.graph_metadata.dump_turtle(self.prefixes), # Data bundle metadata
        }


    def dump_csv(self) -> Dict[str, pd.DataFrame]:
        """
        Export the data bundle as CSVs, organized for human readability.

        Generates a dictionary of DataFrames where each class from the model has its
        own CSV with columns representing card properties and rows representing instance
        values. Additionally, includes two CSVs describing the model itself: one for
        classes and one for properties.

        Returns:
            Dict[str, pd.DataFrame]: A dictionary mapping class and model identifiers to
                                    their corresponding CSV DataFrames.
        """
        # The CSV format dump is different than the two others:
        # Two others extract raw triples, usefull to make saving or to publish, or to import in another SPARQL endpoint
        # But the CSV dump is more for humans:
        # Basically, CSV dump will have a single CSV for each class from the model.
        # And each Class CSV will have as columns, property names that are in the card, and as cells, the values of the right triples (as URI)

        # Also, add 2 additional CSV which basically adds the model to the dump: one for classes, and one for properties (which needs to be flatten)
        to_return = {
            'model-classes': pd.DataFrame(data=[cls.to_dict() for cls in self.model.classes]),
            'model-properties': pd.DataFrame(data=[{
                **(prop.card_of.to_dict('card_of_') if prop.card_of else {}),
                **(prop.domain.to_dict('domain_') if prop.domain else {}),
                'property_uri': prop.uri,
                'property_label': prop.label,
                'property_comment': prop.comment,
                **(prop.range.to_dict() if prop.range else {}),
                'property_order': prop.order,
                'property_min_count': prop.min_count,
                'property_max_count': prop.max_count,
            } for prop in self.model.properties]),
        }

        # Build all the classes DataFrames (only for classes)
        for cls in self.model.classes:
            if cls.class_uri != "rdfs:Datatype":
                to_return[to_snake_case(cls.get_text())] = self.download_class_instances(cls)

        return to_return


    def download_class_instances(self, cls: Resource) -> pd.DataFrame:
        """
        Download all instances of a given class as a pandas DataFrame.

        Each row represents an instance of the class, with columns for the instance URI,
        its type, and values of all outgoing properties defined in the class's card.

        Args:
            cls (Resource): The class whose instances should be downloaded.

        Returns:
            pd.DataFrame: A DataFrame containing all instances of the class with their
                        outgoing property values.
        """
        # Get the ontology properties of this class (only outgoing)
        properties_outgoing = [prop for prop in self.model.properties if prop.card_of.uri == cls.uri]
        properties_outgoing.sort(key=lambda x: x.order or 10**18)

        #  Compute the property name for the query
        def get_property_name(prop: Property) -> str:
            return to_snake_case(prop.label).replace('-', '_').replace('(', '').replace(')', '').replace('\'', '_')

        # Prepare the query: make all lines from the query
        properties_outgoing_names = list(set([f"(COALESCE(?{get_property_name(prop)}_, '') as ?{get_property_name(prop)})" for prop in properties_outgoing]))
        properties_outgoing_names_str = '\n                '.join(properties_outgoing_names)
        triples_outgoings = list(set([f"OPTIONAL {{ ?instance {prepare(prop.uri, self.prefixes.shorts())} ?{get_property_name(prop)}_ . }}" for prop in properties_outgoing]))
        triples_outgoings_str = '\n                    '.join(triples_outgoings)

        # Make sure the class URI is correctly formated
        class_uri = prepare(cls.uri, self.prefixes.shorts())

        # Build the query
        query = f"""
            # DataBundle.download_class({cls.label} ({cls.uri}))
            SELECT
                ?uri
                ('{class_uri}' as ?type)
                {properties_outgoing_names_str}
            WHERE {{
                {self.graph_data.sparql_begin}
                    ?uri {self.model.type_property} {class_uri} .
                    {triples_outgoings_str}
                {self.graph_data.sparql_end}
            }}
        """

        # Execute the query
        instances = self.graph_data.sparql.run(query, self.prefixes)

        return pd.DataFrame(data=instances)


    @staticmethod
    def from_dict(obj: dict, prefixes: Prefixes) -> 'DataBundle':
        """
        Create a DataBundle instance from a dictionary.

        Converts a dictionary representation of a DataBundle into a fully initialized
        DataBundle object, using the provided prefixes for URI shortening and expansion.

        Args:
            obj (dict): Dictionary containing the DataBundle attributes.
            prefixes (Prefixes): Prefixes object used for URI handling.

        Returns:
            DataBundle: An initialized DataBundle instance.
        """
        return DataBundle(
            prefixes = prefixes,
            name = obj.get('name'),
            base_uri = obj.get('base_uri'),
            endpoint_url = obj.get('endpoint_url'),
            username = obj.get('username'),
            password = obj.get('password'),
            endpoint_technology = obj.get('endpoint_technology'),
            model_framework = obj.get('model_framework'),
            prop_type_uri = obj.get('prop_type_uri'),
            prop_label_uri = obj.get('prop_label_uri'),
            prop_comment_uri = obj.get('prop_comment_uri'),
            graph_data_uri = obj.get('graph_data_uri'),
            graph_model_uri = obj.get('graph_model_uri'),
            graph_metadata_uri = obj.get('graph_metadata_uri'),
        )


    def to_dict(self) -> dict:
        """
        Convert the DataBundle instance into a dictionary.

        This dictionary representation is suitable for serialization (e.g., YAML, JSON) 
        or for saving configuration files.

        Returns:
            dict: Dictionary containing all relevant DataBundle attributes.
        """
        return {
            'name': self.name,
            'endpoint_url': self.endpoint.url,
            'base_uri': self.base_uri,
            'username': self.endpoint.username,
            'password': self.endpoint.password,
            'endpoint_technology': self.endpoint.technology_name,
            'model_framework': self.model.framework_name,
            'prop_type_uri': self.model.type_property,
            'prop_label_uri': self.model.label_property,
            'prop_comment_uri': self.model.comment_property,
            'graph_data_uri': self.graph_data.uri,
            'graph_model_uri': self.graph_model.uri,
            'graph_metadata_uri': self.graph_metadata.uri,
        }