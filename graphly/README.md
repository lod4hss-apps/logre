# Graphly

Python code library to communicate with different graph technologies, graphs and ontologies.

Supported graph technologies are:
    - Fuseki
    - Allegrograph
    - GraphDB

All ontologies come from an export of every classes and properties listed in [OntoMe](https://ontome.net/).

Also, Graphly has the capacity to analyze RDF graph models, by either looking at the data (lists classes and properties), but also to read SHACL constraints.
This can be useful for example to know what data there is on a Named Graph, or get all possible properties (outgoing or incoming) of a class.


## How to install

For now, Graphly is not published on *Pypi*, *Conda* or any other package provider, so you can not install it with those tools.

But the way to install it is still easy:

```bash
cd [DIRECTORY_OF_YOUR_CHOICE]
git clone https://github.com/lod4hss-apps/graphly.git
cd graphly
pip install .
```

After doing that, `graphly` package will be available in your Python scripts


## Example usage

### Connect to a SPARQL endpoint

```python
from graphly.sparql import Allegrogaph # Fuseki, GraphDB
from graphly.schema import Prefix, Prefixes

# Needed information to connect to the endpoint
endpoint_url = "https://abc123.allegrograph.cloud/repositories/test"
endpoint_username = "user"
endpoint_password = "pass"

# Connect to the endpoint
endpoint = Allegrograph(endpoint_url, endpoint_username, endpoint_password)

# Prepare some prefixes, for readability
prefixes = Prefixes([
    Prefix('test', 'http://example.com/')
])

# Make a query
result = endpoint.run('SELECT * WHERE { ?s ?p ?o . } LIMIT 10')

print(result) # outputs (eg): [{'o': 'test:1', 'p': 'test:2', 's': 'test:3'}]
```

### Load an endpoint Model

Suppose that you have a named graph "http://example.com/shacl" that contains SHACL contraints of your model.
The goal here is to retrieve information about those constraints so that they are useable in Python code.
Again, for readability, we are going to add other needed prefixes

```python
# Follows previous code cells

from graphly.schema import Graph

# Needed prefixes
prefixes.add(Prefix('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'))
prefixes.add(Prefix('xsd', 'http://www.w3.org/2001/XMLSchema#'))
prefixes.add(Prefix('sh', 'http://www.w3.org/ns/shacl#'))
prefixes.add(Prefix('crm', 'http://www.cidoc-crm.org/cidoc-crm/'))
prefixes.add(Prefix('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'))
prefixes.add(Prefix('rdfs', 'http://www.w3.org/2000/01/rdf-schema#'))
prefixes.add(Prefix('sdh', 'https://sdhss.org/ontology/core/'))

# Create the graph variable (represents your Named Graph "http://example.com/shacl")
graph = Graph(endpoint, 'test:shacl', prefixes)

# Extract the SHACL model out of the Named Graph
model = SHACL()
model.update(graph, prefixes)

# Example: List all the classes of the model:
for c in model.classes:
    print(f"{c.label} ({c.uri})") # outputs: "Person (crm:E21)"

# Example: List all the properties of the model:
for p in model.properties:
    print(f"{p.label} ({p.uri})") # outputs: "has label (rdfs:label)"

# Example: Get a class label
print(model.find('crm:E21').label) # outputs: "Person"

# Example: See if a property is mandatory for a class
print(model.is_prop_mandatory('rdfs:label', 'crm:E21')) # outputs: True

# Example: Extract all outgoing properties for a class
outgoings = [p.domain.uri == 'crm:E21' for p in model.properties]
```

### Import data

Also, one of the main reason why this library has been built, is to help developers to import data (triples) in an endpoint.

Also, to not have to manually check every time, this library has a lot of known URIs and label of different classes coming from different namespaces (all extracted from [OntoMe](https://ontome.net/)), let's see how to use them:

```python
# Follows previous code cells

import pandas as pd
from graphly.schema import Resource, Property
from graphly.ontologies import CRM

# Triples to be stored along the script, and inserted at the end
triples = []

# Some needed properties (might be defined in the model Named Graph, or not)
prop_type = Property('rdf:type', 'has type')
prop_label = Property('rdfs:label', 'has label')
prop_comment = Property('rdfs:comment', 'has comment')

# Create a tool function to easily have basic triples, based on needed properties above
def create_resource_triples(resource: Resource):
    triples = []
    if resource.class_uri:
        triples.append((resource, prop_type, resource.class_uri))
    if resource.label:
        triples.append((resource, prop_label, resource.label))
    if resource.comment:
        triples.append((resource, prop_comment, resource.comment))
    return triples

# The Named Graph where to import data into
graph_data = Graph(endpoint, 'test:data', prefixes)

# Say you have a CSV filled with persons.
# Columns are: name, description, birth_date, birth_place
df_persons = pd.read_csv('my-persons.csv')
df_persons['birth_date'] = pd.to_datetime(df_persons['birth_date'])

# Create Geographical Places
geographical_places = []
geoplaces_names = df_persons['birth_place'].dropna().unique().tolist()
for geoplace in geoplaces_names:
    # Create the resource
    geographical_place = Resource(f"test:i{geoplace}", geoplace, class_uri=SDH.C13_Geographical_Place)
    # Save it for later usage (in the script)
    geographical_places.append(geographical_place)
    # Add basic triples to be inserted
    triples += create_resource_triples(geographical_place)

# Create Persons
persons = []
for i, person in df_persons.iterrows():
    # Create the needed resources
    person = Resource(f"test:r{i}", person['name'], person['description'], class_uri=CRM.E21_Person.uri)
    birth = Resource(f"tests:r{2*i}", f"Birth of {person['name']}", class_uri=CRM.E67_Birth.uri)
    geoplace = next(geoplace for geoplace in geographical_places if geoplace.label == person['birth_place'])
    birth_date = person['birth_date'].strftime("YYYY-MM-DD")

    # Save it for later usage (in the script, not shown here)
    persons.append(person)

    # Add basic triples to be inserted
    triples += create_resource_triples(person) 
    triples += create_resource_triples(birth) 

    # Add additional triples
    triples += [
        (birth, CRM.P98_Brought_Into_Life, person),
        (birth, SDH.P6_Took_Place_At, geoplace),
        (birth, CRM.P82_At_Some_Time_Within, birth_date)
    ]


# When all triples are gathered, insert them
graph_data.insert(triples, prefixes)
```

---

*In the library code, docstings have been Generated by ChatGPT, proof read and corrected if judged necessary.*