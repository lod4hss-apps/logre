from typing import List
import streamlit as st
import hashlib, os, shutil
from pyvis.network import Network
from requests.exceptions import HTTPError
from graphly.schema.statement import Statement
from lib import state
from lib.errors import get_HTTP_ERROR_message
from components.init import init
from components.menu import menu

# Page parameters
INCOMING_LIMIT = 50
MAX_STRING_LENGTH = 80

# Initialize
init(layout='wide', query_param_keys=['db', 'uri'])
menu()

try:

    # From state
    data_bundle = state.get_data_bundle()
    entity_uri = state.get_entity_uri()

    # Make verifications
    if not data_bundle:
        st.warning('No Data Bundle selected')
    if not entity_uri:
        st.warning('No Entity URI provided')
    else:
        
        # Gather minimal information about the entity
        # i.e. Fill Resource instance
        entity = data_bundle.get_entity_basics(entity_uri)
        entity_class = data_bundle.model.find_class(entity.class_uri)

        # Init Entity to fetch
        state.entity_chart_inc_list_init(entity)
        state.entity_chart_out_list_init(entity)

        # Header: entity name, additional info and description
        col_title, col_actions = st.columns([20, 10], vertical_alignment='bottom')
        uri_text = f'<small style="font-size: 16px; color: gray; text-decoration: none;">{entity.uri}</small>'
        col_title.markdown(f"# {entity.get_text()} ({entity_class.get_text()}) {uri_text}", unsafe_allow_html=True)
        st.markdown(entity.comment or '')

        # Header options
        with col_actions.container(horizontal=True, horizontal_alignment="right"):
            if st.button('Entity Card', help="[What is an entity card?](/documentation#what-is-an-entity-card)"):    
                st.switch_page('pages/entity-card.py')
            if st.button('Raw triples', help="[What are raw triples?](/documentation#what-is-the-page-raw-triples-for)"):
                st.switch_page('pages/entity-triples.py')

        st.write('')
        
        # User input to avoid some chosen properties
        all_properties = list(set([f"{p.get_text()} ({p.uri})" for p in data_bundle.model.properties]))
        # all_properties += [Property(data_bundle.model.type_property, "Has Type"), Property(data_bundle.model.label_property, "Has Label"), Property(data_bundle.model.comment_property, "Has Comment")]
        skip_prop_labels = st.multiselect("Skip properties", options=all_properties)
        skip_props = list(set([p for p in data_bundle.model.properties if f"{p.get_text()} ({p.uri})" in skip_prop_labels]))

        # Fetch all data (for selected entities)
        statements: List[Statement] = []
        for ent in state.entity_chart_inc_get_list():
            statements += data_bundle.get_incoming_statements_of(ent, INCOMING_LIMIT, skip_props=skip_props)
        for ent in state.entity_chart_out_get_list():
            statements += data_bundle.get_outgoing_statements_of(ent, skip_props=skip_props)

        # Construct 2 lists of objects built for the Network X API
        have_uri = set()
        nodes_dict = []
        edges_dict = []
        for statement in statements:

            # Construct Subject label
            subject_class_text = data_bundle.model.find_class(statement.subject.class_uri).get_text()
            subject_label = f"{statement.subject.get_text()}\n({subject_class_text})"

            # Construct Object Label
            if statement.object.resource_type == 'iri':
                object_class_text = data_bundle.model.find_class(statement.object.class_uri).get_text()
                object_class_text_2 = f"\n({object_class_text})"
                object_label = f"{statement.object.get_text()}{object_class_text_2}"
            else:
                object_label = f"{statement.object.get_text()}\n(Literal)"


            def __get_hex_color(label: str) -> str:
                """
                From a given label, determine an associated color.
                Usefull to set a color to a class.
                """
                if label is None or label == '': 
                    return "#000"
                hash_val = hashlib.md5(label.encode()).hexdigest()  # Hash the subject name
                return f"#{hash_val[:6]}"  # Take the first 6 characters for a hex color

            # Add the subject to nodes if not yet done
            if statement.subject.uri not in have_uri:
                nodes_dict.append({
                    "label": subject_label,
                    "title": f"<a href=\"/entity?db={data_bundle.key}&uri={statement.subject.uri}\">Open</a>",
                    "color": __get_hex_color(subject_class_text), 
                    "resource": statement.subject
                })
                have_uri.add(statement.subject.uri)

            # Add the object to nodes if not yet done
            if (statement.object.resource_type == 'iri' and statement.object.uri not in have_uri) or (statement.object.resource_type == 'literal' and statement.object.literal not in have_uri):
                nodes_dict.append({
                    "label": object_label,
                    "title": f"<a href=\"/entity?db={data_bundle.key}&uri={statement.object.uri}\">Open</a>" if statement.object.resource_type == 'iri' else None,
                    "color": __get_hex_color(object_class_text if statement.object.resource_type == 'iri' else None),
                    "resource": statement.object
                })
                have_uri.add(statement.object.uri if statement.object.resource_type == 'iri' else statement.object.literal)

            # Add the edge (triple) to the list
            edges_dict.append({
                "source": statement.subject.uri,
                "to": statement.object.uri if statement.object.resource_type == 'iri' else statement.object.literal,
                "label": statement.predicate.get_text()
            })


        # Network object: the one that will be displayed
        network = Network(width="100%", neighborhood_highlight=True)
        network.add_nodes([n['resource'].uri if n['resource'].resource_type == 'iri' else n['resource'].literal for n in nodes_dict], label=[n['label'] for n in nodes_dict], color=[n['color'] for n in nodes_dict], title=[n['title'] for n in nodes_dict])
        for edge in edges_dict:
            network.add_edge(source=edge['source'], to=edge['to'], label=edge['label'])

        # Set the options
        network.set_options("""
            const options = {
                "nodes": {"font": {"face": "tahoma"}},
                "edges": {
                    "length": 150,
                    "arrows": {"to": {"enabled": true}},
                    "font": {"size": 10,"face": "tahoma","align": "top"}
                }
            }
        """)

        # Generate the graph
        network.save_graph('network.html')
        
        # Read from disk
        with open("network.html", 'r', encoding='utf-8') as file:
            source_code = file.read()

        # Delete the file from disk
        os.remove('network.html')
        shutil.rmtree('./lib/')

        # Display the read HTML
        # Here we have to use "with" because it appears that it is the only way with streamlit to display HTML
        with st.container():
            # 617 as height because it makes the network look centered
            st.components.v1.html(source_code, height=617)


        # Expand graph options
        st.markdown('#### Expand graph with:')

        # List all triples targets
        fetched_out_uris = set([ent.uri for ent in state.entity_chart_out_get_list()])
        fetched_inc_uris = set([ent.uri for ent in state.entity_chart_inc_get_list()])
        
        # One raw for each node (because click on a node is unavailable)
        for node in nodes_dict:
            if node['resource'].resource_type != 'iri':
                continue
            
            # The entity (node) title
            col_name, col_outgoing, col_incoming = st.columns([3, 1, 1], vertical_alignment='center')
            with col_name.container(horizontal=True, horizontal_alignment="right"):
                    st.link_button(f"**{node['resource'].get_text(comment=True)}**", type='tertiary', url=f"/entity?db={data_bundle.key}&uri={node['resource'].uri}")

            key = f"checkbox-{node['resource'].uri}"

            # Note if the node is already checked as expanded 
            have_inc = node['resource'].uri in fetched_inc_uris
            have_out = node['resource'].uri in fetched_out_uris

            # Checkbox to expand graph on the OUTGOING path for this node
            with col_outgoing.container(horizontal=True, horizontal_alignment="right"):
                outgoings = st.checkbox("Fetch outgoing properties", key=f"{key}-outgoing", value=have_out)
                if outgoings and not have_out: 
                    state.entity_chart_out_list_add(node['resource'])
                    st.rerun()
                if not outgoings and have_out: 
                    state.entity_chart_out_list_remove(node['resource'])
                    st.rerun()

            # Checkbox to expand graph on the INCOMING path for this node
            with col_incoming.container(horizontal=True, horizontal_alignment="right"):
                incomings = st.checkbox("Fetch incoming properties", key=f"{key}-incoming", value=have_inc)
                if incomings and not have_inc: 
                    state.entity_chart_inc_list_add(node['resource'])
                    st.rerun()
                if not incomings and have_inc: 
                    state.entity_chart_inc_list_remove(node['resource'])
                    st.rerun()

            st.write('')

except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.error(message)
    print(message.replace('\n\n', '\n'))