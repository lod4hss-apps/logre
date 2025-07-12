# Get started

This page is to help you set up your Logre application, from connecting it to a SPARQL endpoint to configure your Knowledge Graph

## Configure the connection with a SPARQL Endpoint

Logre is designed to interact with a SPARQL Endpoint and thus does not integrate a triplestore. It can, however, help you to create new entries, import data and explore your Knowledge Graph with a simple graphical interface.
To get started, you need to configure two things:
- Configure your Endpoint
- Configure your Data Bundle (see it as a dataset)

### Configure your Endpoint

You first need to go to the Configuration page (menu on the left) and then click on "+ Add a new Endpoint".

In the new windows, you can enter the information needed. You can then fill the pop-up with needed information (attention, fields with an ! Exclamation mark are mandatory):

- **Name:** This is the label of this Endpoint as it is displayed in Logre.
- **Server technology:** Here you have to specify what the technology is of your Endpoint. For the moment, only Fuseki, Allegrograph and GraphDB are available.
- **URL:** Here you have to specify the URL of your SPARQL Endpoint (should we mention something about / at the end?)
Base URI: This will be the base URI of your entities that you will create in the Logre application (e.g. if you leave the default value, your entities will be, for example, "http://example.org/1234").
- **Username:** If your Endpoint is behind a login service, you can enter the username to access it.
- **Password:** If your Endpoint is behind a login service, you can enter the password to access it.

Once the information has been entered, you can click on the "Create" button to create the connection with the SPARQL Endpoint. Information is saved locally on your computer so that you won’t need to do that again next time you work on your endpoint.

### Edit your Endpoint

You can always edit your endpoint once created: the configuration is only local, so no consequences for your endpoint. To do so, go back to the "Configuration" page and click on the Endpoint you would like to edit.

A drop-down window unfolds, where you can see the information you have entered. You can modify any elements (beware of the consequences if you change anything after already creating triples with Logre: even though nothing will change on the Endpoint, it might change how things are displayed in Logre); for that, you simply have to click on one of the fields, edit it, press Enter to validate your changes, and then on the small save icon on the right to save your changes.


## Configure your Data Bundles

### What are Data Bundles?

In Logre, information from the SPARQL Endpoint are displayed according to locally stored specification which are called Data Bundles. A Data Bundle is like a working dataset (actual data, an ontology and some metadata). They need to be configured to tell Logre how to look at information. In simpler terms, it specifies "I have data here, which uses the ontology located here, and some metadata at this place, and everything work together".

Data Bundles are composed of three elements, each of them being a named graph:
- The Data named graph, which contains the information gathered by the researcher
- The Ontology named graph, which contains the information of the data model in the form of SHACL triples used in the Data named graph
- The Metadata named graph, which contains information about the data bundle itself (e.g. creation date, creator identity, …)

When using Logre, it is important to create and configure those data bundles in order to be able to display and create information in accordance with a specific data model. Doing so you will see only information you are interested in/relevant, and have the core value of your data at hand.

### Configure your Data Bundle

In the "Configuration" page, once you have created a connection with a SPARQL Endpoint, you can configure a new Data Bundle.
By clicking on the Endpoint in the "Configuration" page, then under the Endpoint information, you can create one by clicking on "+ Add a new Data Bundle".

In the new popup, you can enter the information needed (attention, fields with an ! Exclamation mark are mandatory):
- **Name:** This is the label of this Data Bundle as it is displayed in Logre.
- **Ontological framework:** For the moment, only SHACL is available as a framework.
- **Type property:** You can specify how you link your instances to your classes. `rdf:type` is recommended.
- **Label property:** You can specify how you link your instances to their labels. `rdfs:label` is recommended.
- **Comment property:** You can specify what property should be used to add string comments to instances. rdsf:comment is recommended.
- **Data Named Graph URI:** The Named graph on your endpoint where the data is/will be. If you do not yet have data, you can basically choose a name for your named graph.
- **Ontology Named Graph URI:** The Named graph on your endpoint where the ontology is/will be. If you do not have one yet, you can choose a name.
- **Metadata Named Graph URI:** The Named graph on your endpoint where metadata are. If you do not have one yet, you can choose a name.

Once all of the information has been entered, you can click on "Create" to create your data bundle.