from typing import List
from graphly.schema.model import Model
from graphly.schema.graph import Graph
from graphly.schema.resource import Resource
from graphly.schema.property import Property
from graphly.schema.prefixes import Prefixes


class SHACL(Model):
    """
    Represents a SHACL-based ontology model that extends the generic Model.

    Attributes:
        Inherits all attributes from Model:
            framework_name (str): Set to "SHACL".
            type_property (str)
            label_property (str)
            comment_property (str)
            classes (List[Resource])
            properties (List[Property])

    Methods:
        __init__: Initializes the SHACL model and sets the framework name.
        get_classes: Retrieves SHACL-defined classes from a given RDF graph.
        get_properties: Retrieves SHACL-defined properties from a given RDF graph.
    """
    

    def __init__(self, type_property: str = 'rdf:type', label_property: str = "rdfs:label", comment_property: str = "rdfs:comment") -> None:
        """
        Initialize a SHACL-based Model instance with default or custom property identifiers.

        This constructor sets the framework name to "SHACL" and delegates the 
        initialization of type, label, and comment properties to the base Model class.

        Args:
            type_property (str, optional): The property used to define entity types. Defaults to 'rdf:type'.
            label_property (str, optional): The property used to define entity labels. Defaults to 'rdfs:label'.
            comment_property (str, optional): The property used to define entity comments or descriptions. Defaults to 'rdfs:comment'.
        """
        self.framework_name = "SHACL"
        super().__init__(type_property, label_property, comment_property)

    
    def get_classes(self, graph: Graph, prefixes: Prefixes) -> List[Resource]:
        """
        Retrieve SHACL-defined classes from the given RDF graph.

        Constructs and executes a SPARQL query to find all `sh:NodeShape` nodes 
        and their associated target classes, extracting both the class URI and 
        optional label. The results are returned as a list of `Resource` instances.

        Args:
            graph (Graph): The RDF graph to query for SHACL classes.
            prefixes (Prefixes): Prefixes to use in the SPARQL query.

        Returns:
            List[Resource]: A list of `Resource` objects representing the SHACL-defined 
            classes, each with a `class_uri` of "owl:Class". Returns an empty list if 
            no classes are found.
        """
        # Prepare the query
        query = f"""
            # SHACL.get_classes()
            SELECT DISTINCT
                ?uri 
                (COALESCE(?label_, '') as ?label)
            WHERE {{
                {graph.sparql_begin}
                    ?node a sh:NodeShape .
                    ?node sh:name ?label_ .
                    ?node sh:targetClass ?uri .
                {graph.sparql_end}
            }}
        """

        # Execute the query
        response = graph.run(query, prefixes)

        # Transform into a list of Resource instances, or an empty list
        classes = [Resource.from_dict({**obj, "class_uri": "owl:Class"}) for obj in response] if response else []

        # Add Value classes
        classes += super().get_value_classes()

        return classes


    def get_properties(self, graph: Graph, prefixes: Prefixes) -> List[Property]:
        """
        Retrieve SHACL-defined properties from the given RDF graph.

        Constructs and executes a SPARQL query to extract properties defined 
        via SHACL shapes, including their target classes, labels, order, 
        minimum and maximum counts, domain, and range. The results are returned 
        as a list of `Property` instances.

        Args:
            graph (Graph): The RDF graph to query for SHACL properties.
            prefixes (Prefixes): Prefixes to use in the SPARQL query.

        Returns:
            List[Property]: A list of `Property` objects representing the SHACL-defined 
            properties, including domain and range class information. Returns an empty 
            list if no properties are found.
        """
        # Prepare the query
        query = f"""
            # SHACL.get_properties()
            SELECT DISTINCT
                (COALESCE(?target_class_, '') as ?card_of_class_uri)
                (COALESCE(?label_, ?uri) as ?label)
                (COALESCE(?order_, '') as ?order)
                (COALESCE(?min_count_, '') as ?min_count)
                (COALESCE(?max_count_, '') as ?max_count)
                (COALESCE(?domain_class_uri_, '') as ?domain_class_uri)
                ?uri
                (COALESCE(?range_class_uri_, '') as ?range_class_uri)
                (COALESCE(?datatype_, '') as ?range_datatype)
            WHERE {{
                {graph.sparql_begin}               
                    ?shape sh:property ?node .
                    ?node sh:path ?supposed_uri .  
                    OPTIONAL {{ ?shape sh:targetClass ?target_class_ . }}
                    OPTIONAL {{ ?supposed_uri sh:inversePath ?inverse_property_uri . }}
                    OPTIONAL {{ ?node sh:name ?label_ . }}
                    OPTIONAL {{ ?node sh:order ?order_ . }}
                    OPTIONAL {{ ?node sh:minCount ?min_count_ . }}
                    OPTIONAL {{ ?node sh:maxCount ?max_count_ . }}
                    OPTIONAL {{ ?node sh:datatype ?datatype_ . }}
                    OPTIONAL {{ ?node sh:class ?class . }}

                    BIND(IF(isBlank(?supposed_uri), '', ?target_class_) as ?domain_class_uri_)
                    BIND(IF(isBlank(?supposed_uri), ?target_class_, ?class) as ?range_class_uri_)
                    BIND(IF(isBlank(?supposed_uri), ?inverse_property_uri, ?supposed_uri) as ?uri)
                {graph.sparql_end}
            }}
        """

        # Execute the query
        response = graph.run(query, prefixes) or []
        
        # Transform into a list of Property instances, or an empty list
        properties = []
        for resp in response:
            domain_uri = resp.get('domain_class_uri')
            range_uri = resp.get('range_class_uri')
            range_datatype = resp.get('range_datatype')
            card_of_uri = resp.get('card_of_class_uri')

            domain = self.find_class(domain_uri) if domain_uri else None
            range_target = range_uri or range_datatype
            range = self.find_class(range_target) if range_target else None
            card_of = self.find_class(card_of_uri) if card_of_uri else None

            properties.append(
                Property(
                    resp['uri'],
                    resp.get('label', resp['uri']),
                    "",
                    domain,
                    range,
                    card_of,
                    order=resp.get('order'),
                    min_count=resp.get('min_count'),
                    max_count=resp.get('max_count')
                )
            )

        return properties
