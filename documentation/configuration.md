
## 1. Endpoints

Now that you have a SPARQL endpoint running, and to work with Logre, you must first tell Logre where this endpoint is.

The role of the "Endpoints" section in the configuration page is to link Logre with your endpoint.

At this place you can add important information for Logre, like what and where is your ontology.

Endpoint configuration is made of some fields, much of them are self explaining or contains relevant information in the help near the field. But some others might have additional information:

**Technology**

This field is to tell Logre the technology of the SPARQL endpoint. Some of them have specificities and require specific tweaks, therefore it is necessary to specify it. Only those from the select box are supported by Logre.

**Base URI** 

Setting a base URI allows you to give a proper URI to entities you create in your endpoint






## 2. Graphs

In this section, you can create, delete and download [named graphs](https://en.wikipedia.org/wiki/Named_graph) in your endpoint. The list of graph is the same that the one appearing on the left menu.

Keep in mind, that displaying those graphs can be pretty long if your data is huge: it also make a request to count how much triples there is on the endpoint.

You always will be displayed by at least 3 graphs: the default one, the ontology one (set in the endpoint configuration), and the metadata one (set in the endpoint configuration).

Information about additional graphs you may create or edit will then be saved into the Metadata graph

One other important feature is the possibility of downloading graphs, or even all of them at once. Upon downloading a graph, you can then choose the download format: Turtle or CSV.
In case you chose CSV, the downloaded file will be a zip file containing all CSVs of all classes listed in your ontology. 


## 3. Data tables

Data tables are a specific feature, directly available in the left menu. Its goal is to give an overview (and information) of your entities, in a bulk way, less dedicated to a single entity, but more dedicated to many of them together.

In this configuration section, you can edit the data tables columns of a particular class. This configuration is then saved in the Metadata graph.


## 4. Save your configuration

If your run Logre locally, your configuration is automatically saved in your logre folder. The file is named `logre-config.toml`

If your are on the online version, be carefull! Closing or reloading the page will result in clearing your configuration. 

To save it, hit the Download button at the top of the configuration page. Next time you visit you will be able to load it again directly by uploading this file. This is done so to assure that we do not keep any of your endpoint credentials.