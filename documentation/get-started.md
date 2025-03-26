
# Getting Started with Logre

Logre is a graph editor that connects to an existing SPARQL endpoint. Follow these steps to set up and use Logre efficiently.

---

## 1. Set Up a SPARQL Endpoint

Logre requires a running SPARQL endpoint, as it does not store data itself. You can choose from various triple store providers, including:
- Local solutions (self-hosted)
- Online paid services
- Free online options (e.g., limited by dataset size)

Recommended: We use [AllegroGraph](https://allegrograph.com/) internally at Geovistory.org, which offers a free plan.

**Configure Your Endpoint**

Some triple stores require additional setup:
- AllegroGraph: Create a “repository”
- Fuseki: Set up a “dataset”

For project organization, we recommend separating named graphs—this can be configured in AllegroGraph.

---

## 2. Configure Logre

Set up Logre by:
- Connecting your SPARQL endpoint
- Defining prefixes, graphs, and data tables

For detailed configuration steps, refer to the Configuration section in the documentation.

---

## 3. Import Ontologies and Data

Once your endpoint is connected, you can import data:

**Ontology Import**

Logre integrates with [Semantic-Data-for-Humanities](https://github.com/Semantic-Data-for-Humanities), offering SHACL profiles. To import them:
- Run: make get-sdhss-shacls in the Logre folder.
- Go to the Import page → Ontologies tab.
- Select and import ontologies.

They will be stored in the ontology graph configured in your endpoint.

**Import Existing Data**

- From another SPARQL endpoint → Import n-Quads, Turtle, or CSV files.
- CSV files → Must follow a specific format (see Import page for details).

If you need help modeling your project, contact us—we have expertise in data modeling.

---

## 4. Create Data Manually

You can add data manually via:
- The SPARQL editor
- The Create Data button in the menu

### 4.1 Create an Entity

When creating an entity, the form fields are auto-generated based on your ontology. For example, if “Person” has a birth date and gender, only those fields will appear.

### 4.2 Add a Custom Predicate

If a required predicate isn’t in your ontology, you can:
- Use the SPARQL editor
- Click Create Triple → Set Use Ontology to No


---

## 5. View and Analyze Data

Once data is added, you can explore it in two ways:

### 5.1 Entity Details

Use Find an Entity to view its details. The entity page has:
	•	Card → Displays ontology-defined predicates
	•	Triples → Shows all linked triples (some incoming links may be hidden by default)
	•	Visualization → Graph view of entity connections

### 5.2 Data Tables

This page provides an overview of entities by class. Columns are configurable in the Configuration section.

Useful for:
- ✔ Reviewing data
- ✔ Generating reports
- ✔ Tracking project progress

---

## 6. Publish Your Results

Once your data is finalized, you can:
- Generate reports (with or without Logre)
- Publish data online

At Geovistory, we can also create a project website for you (e.g., *geovistory.org/your-project*) with dynamic visuals and charts. Contact us for details!