
## 1. Endpoints

Now that you have a SPARQL endpoint running, in order to work with Logre, you must first tell Logre this endpoint location.

The role of the *Endpoints* section in the *Configuration* page is made to link Logre with your endpoint.

At this place you can add important information for Logre, like what and where is your ontology.

Endpoint configuration is made of some fields, much of them are self explaining or contains relevant information in the help near the field. 
But some others might have additiona information, that what this page is made for.

**Technology**

This field is to tell Logre the technology of the SPARQL endpoint. 
Some of them have specificities and require specific tweaks. 
Therefore it is necessary to specify it. 
Only those from the select box are supported by Logre.

**Base URI** 

Setting a base URI allows you to give a proper URI to entities you create in your endpoint. 
Each new entities created with Logre (unless specified otherwise) will have this base URI. 
Anywhere in Logre, you can refer to this URI with the "base" prefix (e.g. `base:i1234`).


**Ontological Framework**

We, at Geovistory.org, we highly recommend using SHACL to describe an ontology.
Therefore, we recommend letting this option to "SHACL" and chose from the SDHSS ontologies, 
or to create your own SHACL files and import them (see *Get Started* section for more details).

*Why SHACL?*

SHACL ontologies allows to define nice rules about classes, properties and how they interact together, see more on the [W3C page](https://www.w3.org/TR/shacl/).
Also, SHACL is also used in Logre to configure the fields that are displayed. 
For instance, if you see the *Birth date* field in a Person formular, it is because it is mentioned in the ontology (i.e. the SHACL).
It is also why you have just the information you wants in your entity card, it is not poluted with other technical triples that your entities have.

*But I do not have a SHACL file*

No problem, it is not necessary to have a SHACL file in order to use Logre. 

First of all, you can use the existing ones from SDHSS project (see *Get Started* section).

Secondly, if you do not find your needs in the existing profiles, contact-us, we can offer services where we do the ontological modeling for you.

Lastly, if you do not wish to use SHACL (because you use another specification for example), just select "None" in the field. In this case Logre will understand that the ontology he has to assume is the one used; so no need for configuration.

**Ontology location**

This fields goes hands in hands with the previous ones.
In order to use any ontology, Logre needs to know where it is stored, where to look for. 
We recommend to have your ontology in a specific graph, and that is the field you specify where it is.

**Credentials**

If your SPARQL endpoint needs credentials, this is the place to put them. 
Your credentials are not stored by Logre at all, do not just trust us on that point, verify in the open source code.

## 2. Graphs

In the *Graph* section, you can create, delete and download [named graphs](https://en.wikipedia.org/wiki/Named_graph) in/from your endpoint. The list of graphs is the same that the one appearing on the left menu.

Keep in mind, that displaying those graphs can be pretty long if your data is huge: it also make a request to count how much triples there are on the endpoint.

You will be displayed with at least 3 graphs: the default one, the ontology one (set in the *Endpoint Configuration*), and the metadata one (set in the *Endpoint Configuration*).

Information about additional graphs you may create or edit will then be saved into the Metadata graph

One other important feature is the possibility of downloading graphs, or even all of them at once. Upon downloading a graph, you can then choose the download format: Turtle or CSV.
In case you chose CSV, the downloaded file will be a zip file containing all CSVs of all classes listed in your ontology, with columns being properties listed for the class (configured in initial SHACL file). 


## 3. Data tables

Data tables are a specific feature, directly available in the left menu. 
Its goal is to give an overview (and information) of your entities, in a bulk way, less dedicated to a single entity, but more to the many of them.

In this configuration section, you can edit the data tables columns of a particular class. This configuration is then saved in the Metadata graph.
By default, classes have a Data table configuration: *URI*, *label*, *comment*, *outgoing triples number*, *incoming triples number*


## 4. Save your configuration

If your run Logre locally, your configuration is automatically saved in your logre folder. The file is named `logre-config.toml`

If your are on the online version, be carefull! Closing or reloading the page will result in clearing your configuration (because we do not store anything). 

To save it, hit the Download button at the top of the configuration page. Next time you visit you will be able to load it again directly by uploading this file. This is done so to assure that we do not keep any of your endpoint credentials.