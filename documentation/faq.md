
# Logre Documentation (FAQ)


---

### What is Logre?

Logre stands for LOcal GRaph Editor, an open source tool to seemlessly interact with [RDF graphs](/documentation#what-are-rdf-graphs).
It has been developed to help researchers and data enthusiasts to work with such graphs with a simple and intuitive interface, allowing to explore, create and manage linked data.

---

### This is my first launch, what do I do now?

Now that Logre is running and working - you woud not see this page otherwise - you can know think of your data repository: Logre is just an editor, meaning that it has to connect to an existing [SPARQL endpoint](https://en.wikipedia.org/wiki/Resource_Description_Framework).

- The first next step is to think of where to store your data? Have you a server dedicated for that? Is it remote? Do you need to [install one locally](https://en.wikipedia.org/wiki/Resource_Description_Framework)?
- Then you need to add an **Endpoint** in the Configuration page so Logre knows how to reach your triple store: URL + technology + credentials (they are only local on your computer).
- Finally, create one or more **Data Bundles** inside this endpoint to describe where your data/model/metadata graphs live.
- You are now good to explore, create and edit your data!

---

### What is a Graph ?

It is a data structure made of nodes and edges used to represent relationships

---

### What is a Knowledge Graph?

It is a structured network of facts where entities are connected by relationships, making information easier to search, analyze and understand.

A Knowledge Graph is a specific Graph, used to represent information, or knowledge.

---

### What are RDF Graphs?

It is a specific Knowledge Graph, where information is strictly represented as triples: subject – predicate – object (example: “Paris – isCapitalOf – France.”) forming a web of information.

RDF stands for [Resource Data Framework](https://en.wikipedia.org/wiki/Resource_Description_Framework).

---

### What is a SPARQL endpoint?

It is a web service that lets you query a dataset stored as RDF using the SPARQL query language. But do not worry, you do not need to know SPARQL. Logre handles it for you.

See a SPARQL endpoint like a server (i.e. endpoint) having different databases (i.e. datasets) in which you can add your data. As for databases, there are many different SPARQL endpoint technologies. Just to name a few, there is [RDF4J](https://rdf4j.org/), [Fuseki](https://jena.apache.org/documentation/fuseki2/), [GraphDB](https://graphdb.ontotext.com/), [Allegrograph](https://allegrograph.cloud), [Neptune](https://docs.aws.amazon.com/neptune/), [qLever](https://github.com/ad-freiburg/qlever), ... But for now, only a few of them are supported by Logre

---

### How to install a SPARQL endpoint locally?

Here we put you two way of installing two different available technologies.

If you do not understand the next lines, we advise asking someone who does.

#### RDF4J (docker image)

```bash
docker pull eclipse/rdf4j-workbench # Pull RDF4J server + workbench image
docker run -d -p 8080:8080 eclipse/rdf4j-workbench # Run the RDF4J image (server + GUI on 8080)
docker ps # Note the container ID
docker logs [CONTAINER_ID] # Inspect logs if you need to troubleshoot the server
```

> Tip: the Docker Compose setup bundled with Logre already wires the UI to an RDF4J server and auto-creates a repository. You can build the image it if you want a ready-to-go local stack.


#### Fuseki (docker image)

```bash
docker pull stain/jena-fuseki # Pull Fuseki docker image
docker run -d -p 3030:3030 stain/jena-fuseki # Run the Fuseki docker image
docker ps # Note the container ID
docker logs [CONTAINER_ID] # In order to fetch the default admin password that has been generated for you: keep it
```

---

### What are the supported SPARQL endpoint technologies?

For now, Logre supports 4 endpoint technologies: RDF4J, Fuseki, Allegrograph and GraphDB.

We have plan to add more. If you need one specific, feel free to contact us!

---

### How do I create or edit an Endpoint?

Endpoint creation and edition happens in the **Configuration → Endpoint** section. Each endpoint stores only connection details: name, technology, URL, username/password. Once you create one, you can have as many bundles as you want linked to it.

---

### What is a Named Graph?

It is an extension of the RDF graph model. As explained, in the RDF Graph model, you only have subject, predicate and object. The Named Graph add a 4th element to triples, making them quads (3 + 1) allowing to identify the graph in which a triple belong, without having to create another dataset/endpoint. This is usefull for example to separate your model from your data, or your metadata, or simply separate your data into different parts, like when you have different informaiton sources.

---

### What is SHACL?

It stands for [SHape Constraint Language](https://www.w3.org/TR/shacl/).

If is a W3C standard to check quality and validity in [RDF Graphs](/documentation#what-are-rdf-graphs). Concretely, it is a set of rules (in RDF graph format) describing how your data should or should not be (e.g. a Person should have a mandatory name, can only have one birth date, ...). It ensures that your data is consistent, and trustworthy, something important when dealing with Linked Open Data.

Here is a small example of a SHACL file content of the following rule: "All person can have maximum 2 parents" 

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix ex: <http://www.example.org/> .


ex:person_shape a sh:NodeShape;
    sh:targetClass crm:E21;
    sh:name "Person";

    sh:property [
        sh:path crm:P152;
        sh:name "has parent";
        sh:class crm:E21;
        sh:maxCount 2;
    ];

    .
```

It is true that, written like that, it is not so simple to grasp. But no worries, we already did that for you! 

On [OntoMe](https://ontome.net/) there are a lots of different profiles on which you can download the corresponding SHACL.

You can then [import](/documentation#how-to-import-data-into-the-sparql-endpoint) them into your SPARQL endpoint.

Congratulation, you have configured your classes properties - model - , and Logre will now provide you with personalized formulars, fitting your project needs.

---

### What are the supported model framework supported?

For now we only supports SHACL as a model framework.

If you do not have a model, and only data, Logre will interpret them to be the source of truth, and display them accordingly.
You can expect lower performance if you do not have a explicit model for you data (Logre needs to scan and interpret all your triples).

---

---

### What are "Prefixes"?

Prefixes are shortcuts for long URIs. It defines an abreviation so the URI does not have to be repeated.

For example "xsd" if often used to replace the long URI "http://www.w3.org/2001/XMLSchema#", so that when setting the type of a value, "xsd:string" can be used instead of "http://www.w3.org/2001/XMLSchema#string" which makes it much more readable.

In Logre, you can [configure all your prefixes](http://www.w3.org/2001/XMLSchema#) in the Configure page, and every possible time, long URI will be replaced by its prefix.

---

### How to create or update a Prefix?

You can do that in the configuration page, inside the "Prefixes" section.

All you need to have is:
- The short version
- The long URI (do not forget the last char! Often it is a "#" or a "/")

If you use common prefixes, we advise that you also use the traditional prefix.

By Default, Logre provides you with most commonly used prefixes, so that you don't have to set them manually.

---

### What are Data Bundles?

You can understand "data bundles" as the common word "dataset". It has not been called so because the word was already taken. 

In fact, in some SPARQL technologies, the "dataset" word is used to describe what other technologies called "repository", so to avoid confusion, instead of "dataset", in Logre we work with "data bundles".

A data bundle is made of 3 majors things: data, a model, metadata. Each one of those things can either be in the same [Named Graph](/documentation#what-is-a-named-graph) (we DO NOT advise to do so) or in different ones (we DO advise to do so).

In the end, a data bundle is just a way **for you** to represent your data, it is nothing concretely materialized, it is more a way of saying something like "My dataset has data stored at this place, the model is here, and metadata are placed here".

---

### How to create or edit a Data Bundle?

First, before creating a data bundle, a [SPARQL endpoint](http://localhost:8501/documentation#what-is-a-sparql-endpoint) is needed.

In the Configuration page, locate the **Data Bundles** section. You can add or edit bundles from there: the dialog only asks for bundle-specific values (which endpoint, name, base URI, graphs, SHACL/model information).

No worries, everything is editable, even if you make a mistake in the configuration, you will be able to correct it without impact on your data: see the configuration as glasses to watch your data: changing your glasses settings does not change the scene behind, just the way you percieve it.

---

### Where do I find my SPARQL username and password?

This depends on your SPARQL endpoint:
If it is a local one (i.e. on your computer) you have to find credentials yourself. If you followed the tutorial [here](/documentation#how-to-install-a-sparql-endpoint-locally), then you already have them.

Otherwise, ask the endpoint maintainer for credentials.

Credentials now belong to the Endpoint itself (see *How do I create or edit an Endpoint?*). When you edit a bundle, you will not be asked for network parameters any more: Logre automatically injects the SPARQL client coming from the selected endpoint.

---

### In the Data Bundle creation, what does "Base URI" refers to?

In a RDF Graph, when an entity is created, it has to be given a unique URI. And that what "Base URI" is for.

Logre will generate a unique ID for each entity you create, and prepend it with the base URI you provide in the data bundle configuration. 

Additionally, the prefix "base" will also be used everywhere in Logre, and will refer to the URI you mentioned in the data bundle configuration.

Example: If you set the base URI as "http://www.example.org/entity/", and Logre generates the id: "i1234", then the entity will have "http://www.example.org/entities/i1234" as unique URI, and will be displayed as "base:i1234".

---

### In the Data Bundle creation, why should I provide 3 graphs URIs (data, model, metadata)?

As explained [here](http://localhost:8501/documentation#what-are-data-bundles), a data bundle is made of 3 cores things, the data, the model and metadata. So, in the data bundle creation form you need to tell Logre where to look for those things.
By default, data will be in the named graph "base:data", model in "base:model", and metadata in "base:metadata".

These are juste defaults, your are free to put anything there.
Having graphs here does not mean that they already exist, see it as a way for you to tell Logre where to look for things, and where put other things. if it does not yet exists, then Logre will simply find nothing. 

---

### In the Data Bundle creation, why am I given the list of existing graphs?

It is possible that you already have RDF data. If so, you might be interested to import data into another SPARQL endpoint, or even just plug Logre on an existing SPARQL endpoint. If so, you might not remember URIs of existing named graph. 

Logre displays them for you, so that you do not have to find them manually; by making a SPARQL request on your own for example.

---

### In the Data Bundle creation, why should I provide type, label and comment properties URIs?

In order to work with data, and formulars, find entities in the GUI etc, Logre needs to know entity classes, labels and comment.

This is the reason why you are provided with such fields: basically here you tell Logre "My entities classes are defined with the property "rdf:type" (example) I name my entity with the property "rdfs:label".

If you do not know those, you can let the default ones. This is usefull for example when you work from data coming from another SPARQL endpoint, for example, Wikidata defines its "type property" with "https://www.wikidata.org/wiki/Property:P31".

If you have data coming from Wikidata, this would be the place to tell Logre what the "type property" is.

---

### Where is my configuration stored?

Everything stays local, your configuration, including username, passwords, URIs etc stays on your computer, even if the SPARQL endpoint is remote. You can observe the stored configuration in your Logre folder, named "logre-config.yaml".

---

### What type of queries can I write in the SPARQL editor?

The SPARQL editor supports "SELECT", "CONSTRUCT", "INSERT", "DELETE", "CLEAR".

If some of these answer has a result, they will appear below the editor.

---

### Can I save a specific query?

Logre lets you the possibility to save a query that you executed, so that you can again have it later.

This can be useful when you do specific SPARQL requests often.

Caution! You can only save a query after clicking on "Run", the save option won't be visible otherwise.

---

### How to import data into the SPARQL endpoint?

To import data into one of your endpoint, navigate to the Import/Export page. 
You can then:

- Choose the file format: n-Quads (.nq) or Turtle (.ttl).
- Upload your file.
- If you selected Turtle, pick which graph it targets (Data, Model, or Metadata).
- Confirm the upload in the dialog.

---

### How to export my data?

You can export data from a data bundle on the Import/Export page (for full dumps) and download the current model directly from the Data Bundle dialog. Available formats are:
- n-Quad (.nq): one single files with all of your data
- Turtle (.ttl): one file for each part of your data bundle

Caution, if you have large graphs, export can be pretty long, multiple minutes, even more depending on your data, be patient.

---

### How to see my data?

When you have existing data in your data bundle, you can explore them by clicking on the "Find entity", this will open a dialog window to allow you to search in your data. 

Search is not case sentive, but words order is: you can not search Albert Einstein with "Alb Ein" or "Einstein Albert".

---

### How to create new data?

To manually create data in your SPARQL endpoint, just click on the side bar button "Create", chose a class, and you are provided by a formular which depends on the data bundle's model.

---

### What is an entity card?

The entity card is all information of your entity which validates the model. If you have more information than those in your model, you won't see them. If you want, you need to go to the Raw Triple list.

---

### What is the page "Raw triples" for?

Not as the Entity Card page, Raw triples is not customizable, there you can find raw triples: subject - predicate - object. 
For incoming triples, to avoid overload of the web page, a limited amount of triples are fetched, but you can manually increase the fetched number in order to meet needs, but be ware! If the number is too high, you risk to crash you web page (the only risk with that is that your page would need a reload, or maybe to restart Logre), no incidence on your data;

---

### What is shown on page "Visualization"?

On the visualization page, well you guessed it, you can observe your data in a graphical way, with real nodes and edges. This can help you visualize your data.

---

### How to expand the visualization?

Below the visualization tool, there is a list of displayed entities: for each node on the chart (that is not a value, i.e. has to be a class instance), a line is shown. You can choose to expand the graphical visuals through an entity by checking, for each entity, if you want to fetch incoming/outgoing triples for those entities. But be cautious, if you checkings fetch too much entities, the web page might not be able to handle it, too much node displayed can cause your browser too crash, and you might need to restart Logre

---
