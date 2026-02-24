from typing import List
from graphly.schema.graph import Graph
from graphly.schema.property import Property
from graphly.schema.prefix import Prefix
from graphly.schema.prefixes import Prefixes
from graphly.schema.resource import Resource


class Model:
    """
    Represents an RDF/ontology model that allows querying classes and properties from a graph.

    Attributes:
        framework_name (str): Name of the framework used, defaults to "No Framework".
        type_property (str): The property used to define entity types.
        label_property (str): The property used to define entity labels.
        comment_property (str): The property used to define entity comments.
        classes (List[Resource]): List of classes discovered in the model.
        properties (List[Property]): List of properties discovered in the model.

    Methods:
        __init__: Initializes the model with optional custom type, label, and comment properties.
        update: Refreshes the model's classes and properties from the graph.
        get_classes: Retrieves all distinct classes from the RDF graph.
        find_class: Finds a class in the model by its URI.
        get_properties: Retrieves all distinct properties from the RDF graph with correct domain and range.
        find_properties: Finds a list property in the model by their URI.
        is_prop_mandatory: Checks whether a property is mandatory, optionally filtered by card.
    """

    framework_name: str

    type_property: str
    label_property: str
    comment_property: str

    classes: List[Resource]
    properties: List[Property]


    def __init__(self, type_property: str = 'rdf:type', label_property: str = "rdfs:label", comment_property: str = "rdfs:comment") -> None:
        """
        Initialize a Model instance with default or custom property identifiers.

        Args:
            type_property (str, optional): The property used to define entity types. Defaults to 'rdf:type'.
            label_property (str, optional): The property used to define entity labels. Defaults to 'rdfs:label'.
            comment_property (str, optional): The property used to define entity comments or descriptions. Defaults to 'rdfs:comment'.
        """
        # Set attributes
        self.framework_name = "No Framework" if not hasattr(self, 'framework_name') else self.framework_name
        self.type_property = type_property
        self.label_property = label_property
        self.comment_property = comment_property

        # Initialization
        self.classes = []
        self.properties = []


    def update(self, graph: Graph, prefixes: Prefixes) -> None:
        """
        Update the Model by refreshing its classes and properties.

        This method retrieves the latest classes and properties using
        `get_classes()` and `get_properties()`, and updates the corresponding
        attributes of the Model.
        """
        self.classes = self.get_classes(graph, prefixes)
        self.properties = self.get_properties(graph, prefixes)


    def get_classes(self, graph: Graph, prefixes: Prefixes) -> List[Resource]:
        """
        Retrieve all distinct classes from the given RDF graph.

        Constructs and executes a SPARQL query to identify unique class URIs 
        based on the Model's `type_property`. Optionally retrieves class labels 
        using the `label_property`. The results are returned as a list of 
        `Resource` instances, each enriched with a `class_uri` of "owl:Class".

        Args:
            graph (Graph): The RDF graph to query for classes.

        Returns:
            List[Resource]: A list of `Resource` objects representing the classes 
            found in the graph. Returns an empty list if no classes are found.
        """
        # Prepare the query
        query = f"""
            # model.get_classes
            SELECT DISTINCT
                ?uri 
                (COALESCE(?label_, '') as ?label)
            WHERE {{
                {graph.sparql_begin}
                    ?subject {self.type_property} ?uri .
                    OPTIONAL {{ ?uri {self.label_property} ?label_ }}
                {graph.sparql_end}
            }}
        """

        # Execute the query
        response = graph.run(query, prefixes)

        # Transform into a list of Resource instances, or an empty list
        classes = [Resource.from_dict({**obj, "class_uri": "owl:Class"}) for obj in response] if response else []

        # Add Value classes
        classes += self.get_value_classes()

        return classes
    

    def get_properties(self, graph: Graph, prefixes: Prefixes) -> List[Property]:
        """
        Retrieve all distinct properties from the given RDF graph with accurate range types.

        Constructs and executes a SPARQL query to identify property URIs used in the graph,
        excluding the Model's `type_property`, `label_property`, and `comment_property`. 
        For each property, the method retrieves its label, domain class, and range class. 
        If the object of a triple is an IRI, the range is set to the corresponding class URI;
        if it is a literal, the range is set to the literal's datatype.

        Args:
            graph (Graph): The RDF graph to query for properties.

        Returns:
            List[Property]: A list of `Property` objects, each containing the property 
            resource, its domain class (if any), and its range class (if any). 
            Returns an empty list if no properties are found.
        """
        # Prepare the query
        query = f"""
            # model.get_properties
            SELECT distinct 
                (COALESCE(?domain_class_uri_, '') as ?domain_class_uri)
                ?uri 
                (COALESCE(?label_, '') as ?label)
                ?range_class_uri
            WHERE {{
                {graph.sparql_begin}
                    ?s ?uri ?o .
                    OPTIONAL {{ ?uri {self.label_property} ?label_}}
                    OPTIONAL {{ ?s {self.type_property} ?domain_class_uri_ . }}
                    OPTIONAL {{ ?o {self.type_property} ?range_class_uri_ . }}
                {graph.sparql_end}
                
                FILTER (?uri != {self.type_property} && ?uri != {self.label_property} && ?uri != {self.comment_property})
                BIND(IF(isIRI(?o), COALESCE(?range_class_uri_, ""), DATATYPE(?o)) as ?range_class_uri)
            }}
        """

        if not prefixes.has('xsd'):
            prefixes.add(Prefix('xsd', 'http://www.w3.org/2001/XMLSchema#'))

        # Execute the query
        response = graph.run(query, prefixes)

        # Transform into a list of Property instances, or an empty list
        properties = []
        for resp in response:
            domain = self.find_class(resp['domain_class_uri'])
            range = self.find_class(resp['range_class_uri'])
            properties.append(Property(resp['uri'], resp['label'], "", domain, range))

        return properties
    

    def find_class(self, class_uri: str) -> Resource | None:
        """
        Find a class in the Model by its URI.

        Searches through the Model's `classes` attribute for a class whose 
        `uri` matches the given `class_uri`.

        Args:
            class_uri (str): The URI of the class to find.

        Returns:
            Resource | None: The matching `Resource` object if found, otherwise None.
        """
        return next((klass for klass in self.classes if klass.uri == class_uri), Resource(class_uri))


    def find_properties(self, prop_uri: str, domain_class_uri: str = None, range_class_uri: str = None) -> List[Property]:
        """
        Find properties matching the given URI, optionally filtered by domain and/or range.

        Args:
            prop_uri (str): The URI of the property to search for.
            domain_class_uri (str, optional): The URI of the domain class to filter by. Defaults to None.
            range_class_uri (str, optional): The URI of the range class to filter by. Defaults to None.

        Returns:
            List[Property]: A list of matching properties. If none are found, 
            a new Property with the given URI is returned in a list.
        """
        # Narrow down the properties if domain and/or range is provided
        filtered = self.properties
        if domain_class_uri:
            filtered = [prop for prop in filtered if prop.domain and prop.domain.uri == domain_class_uri]
        if range_class_uri:
            filtered = [prop for prop in filtered if prop.range and prop.range.uri == range_class_uri]
        
        # Find all properties satisfying the conditions
        # They can be multiple because some times a class has mutiple times the same property
        # but with different ranges
        target = [prop for prop in filtered if prop.uri == prop_uri]

        if len(target) == 0: 
            return [Property(prop_uri)]
        else: 
            return target


    def is_prop_mandatory(self, prop_uri: str, card_of_uri: str = None) -> Property | None:
        """
        Check if a property is mandatory in the Model.

        Searches the Model's `properties` for a property matching the given URI.
        If `card_of_uri` is provided, only considers properties associated with 
        that specific card. Raises an exception if multiple matching properties 
        are found (should not).

        Args:
            prop_uri (str): The URI of the property to check.
            card_of_uri (str, optional): The URI of the associated card to filter by. Defaults to None.

        Returns:
            Property | None: The matching `Property` object if found, otherwise None.
        """
        # Select only right properties, and if case of a card_of, select only the one with the right card
        selection = [p for p in self.properties if p.uri == prop_uri and (card_of_uri is not None or p.card_of.uri ==card_of_uri)]

        if len(selection) > 1: 
            raise Exception(f'Too much properties retrieved for prop_uri = {prop_uri}, and card_or_uri = {card_of_uri}')
        
        return selection[0] if len(selection) > 0 else None


    @staticmethod
    def get_value_classes() -> List[Resource]:
        """
        Return a predefined list of common XSD and RDF datatype resources.

        This static method provides `Resource` instances representing standard 
        value types, including strings, numbers, booleans, dates, durations, 
        and binary or language types, with their corresponding URIs and labels.

        Returns:
            List[Resource]: A list of `Resource` objects for common RDF/XSD datatypes.
        """
        return [
            Resource('xsd:string', 'String', '', 'rdfs:Datatype'),
            Resource('xsd:integer', 'Integer', '', 'rdfs:Datatype'),
            Resource('xsd:decimal', 'Decimal', '', 'rdfs:Datatype'),
            Resource('xsd:float', 'Float', '', 'rdfs:Datatype'),
            Resource('xsd:double', 'Double', '', 'rdfs:Datatype'),
            Resource('xsd:boolean', 'Boolean', '', 'rdfs:Datatype'),
            Resource('xsd:dateTime', 'dateTime', '', 'rdfs:Datatype'),
            Resource('xsd:date', 'Date', '', 'rdfs:Datatype'),
            Resource('xsd:time', 'Time', '', 'rdfs:Datatype'),
            Resource('xsd:gYear', 'G Year', '', 'rdfs:Datatype'),
            Resource('xsd:gMonth', 'G Month', '', 'rdfs:Datatype'),
            Resource('xsd:gDay', 'G Day', '', 'rdfs:Datatype'),
            Resource('xsd:gYearMonth', 'G Year Month', '', 'rdfs:Datatype'),
            Resource('xsd:gMonthDay', 'G Month Day', '', 'rdfs:Datatype'),
            Resource('xsd:duration', 'Duration', '', 'rdfs:Datatype'),
            Resource('xsd:dayTimeDuration', 'Day Time Duration', '', 'rdfs:Datatype'),
            Resource('xsd:yearMonthDuration', 'Year Month Duration', '', 'rdfs:Datatype'),
            Resource('xsd:hexBinary', 'Hexadecimal Binary', '', 'rdfs:Datatype'),
            Resource('xsd:base64Binary', 'Base64 Binary', '', 'rdfs:Datatype'),
            Resource('xsd:anyURI', '', 'Any URI', 'rdfs:Datatype'),
            Resource('xsd:language', 'Language', '', 'rdfs:Datatype'),
            Resource('xsd:langString', 'Language String', '', 'rdfs:Datatype'),
            Resource('rdf:HTML', 'HTML', '', 'rdfs:Datatype'),
        ]