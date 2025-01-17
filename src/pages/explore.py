import streamlit as st
from components.init import init
from components.menu import menu
from components.find_entities import dialog_find_entity
from components.create_entity import create_entity
from components.create_triple import create_triple
from tools.sparql_queries import list_entity_triples


##### The page #####

init(layout='wide')
menu()

# General user commands
col1, col2, col3 = st.columns([1, 1, 1])
if col1.button('Find an entity'):
    dialog_find_entity()
if col2.button('Create an entity'):
    create_entity()
if col3.button('Create a triple'):
    create_triple()

st.divider()

# If an entity is selected (ie in session)
if 'selected_entity' in st.session_state:

    # Entity title with label, class and id
    col1, col2 = st.columns([2, 1], vertical_alignment='bottom')
    col1.markdown('# ' + st.session_state['selected_entity']['display_label'])
    col2.markdown(f"###### {st.session_state['selected_entity']['uri']}")

    # For each selected graph, displays all triples the selected entity has
    selected_graphs = [graph for graph in st.session_state['all_graphs'] if graph['activated']]
    for graph in selected_graphs:

        # Fetch all triples
        with st.spinner('Fetching entity triples...'):
            triples = list_entity_triples(st.session_state['selected_entity']['uri'], graph=graph['uri'])
            # st.dataframe(pd.DataFrame(data=triples))

        col1, _ = st.columns([5, 5])
        col1.divider()

        # Display all triples
        st.markdown(f'##### From graph "{graph["label"]}"')
        for i, triple in enumerate(triples):
            col1, col2, col3 = st.columns([2, 1, 2], vertical_alignment='center')
            
            # If the subject is not the selected entity
            if 'subject' in triple:
                subject_display_label = f"{triple['subject_label']} ({triple['subject_class_label']})"

                # Button to jump on the entity (change the "selected_entity" in session)
                if col1.button(subject_display_label, type='tertiary', key=f'explore-subject-{i}', help="Click to query this entity"):
                    st.session_state['selected_entity'] = {
                        'uri': triple['subject'],
                        'display_label': subject_display_label
                    }
                    st.rerun()
            else:
                # Otherwise, just displays a "fake button"
                subject_display_label = st.session_state['selected_entity']['display_label']
                col1.button(subject_display_label, type='tertiary', key=f'explore-subject-{i}', help="The current entity")


            # Display the property
            if 'predicate' in triple:
                predicate_label = triple['predicate_label'] if 'predicate_label' else 'No label'
                col2.write(predicate_label)

            # If the object is not the selected entity
            if 'object' in triple:

                # Object can also be a literal. In such case, juste display a text (instead of a button)
                if triple['object_literal'] == 'true':
                    object_display_label = triple['object']
                    col3.write(object_display_label, help="This is a Literal")
                else:
                    # Otherwise, do as subjects
                    object_display_label = f"{triple['object_label']} ({triple['object_class_label']})"
                    if col3.button(object_display_label, type='tertiary', key=f'explore-object-{i}', help="Click to query this entity"):
                        st.session_state['selected_entity'] = {
                            'uri': triple['object'],
                            'display_label': object_display_label
                        }
                        st.rerun()
            else:
                # Otherwise, just displays a "fake button"
                object_display_label = st.session_state['selected_entity']['display_label']
                col3.button(object_display_label, type='tertiary', key=f'explore-object-{i}', help="The current entity")