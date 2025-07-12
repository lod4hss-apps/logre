# FAQ

> ***Why do I have the hand on the type, label and comment properties?***

Having the possibility to put something else that classic RDF allows you to import other data coming from other data silos that use other properties and still work with their data without friction. For example if you have data coming from Wikidata, you might want to put “wd:P31” instead of “rdf:type” for the type property.

> ***Do my Named Graphs (data, ontology, metadata) have to be distinct?***

Despite recommending to separate your graphs accordingly, this is not a requirement, you can have the same Named Graph for your data and your ontology. You just need to tell it to Logre in order for the application to display things correctly. 
