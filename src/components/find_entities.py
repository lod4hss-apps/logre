import streamlit as st
from lib.sparql_queries import list_used_classes, list_entities


@st.dialog("Find an entity", width='large')
def dialog_find_entity() -> None:
    """
    Dialog function that allow user to look for an entity.
    If an entity is selected, set this entity in the session (as 'selected_entity') and close the dialog.
    """

    graph = st.session_state['all_graphs'][st.session_state['activated_graph_index']]
    st.markdown(f"**Graph: *{graph['label']}***")

    # If the user did not yet choose an endpoint, display a message and do nothing else
    if 'endpoint' not in st.session_state:
        st.warning('You must first choose an endpoint')
        return

    # First, begin to load all the used classes on the endpoint
    # This is to speed up the search with class filtering
    classes = []

    with st.spinner(f'Fetching all classes from graph {graph["label"]}...'):
        classes += list_used_classes(graph['uri'])

    # If no classes has been found on the endpoint
    if len(classes) == 0: 
        st.info("No entity having a class found on this graph")
        return

    # User commands: Select a class, and type an entity name
    col1, col2 = st.columns([2, 4])
    selected_class_label = col1.selectbox('Entity class (optional)', [cls['label'] for cls in classes], index=None, placeholder='Class', help="Performance is highly improved when selecting a class.")
    label = col2.text_input("Entity label (case insensitive)", placeholder='Write the entity label (or a part of it) and hit "Enter"')

    # If the user has selected a class, find it (get its dictionary)
    if selected_class_label:
        selected_class = [cls for cls in classes if cls['label'] == selected_class_label][0]
    else:
        selected_class = None

    # If there is something written in the label, find similar entities
    if label or selected_class:
        with st.spinner("Fetching corresponding entities from endpoint"):
            entities = []
            entities += list_entities(label, selected_class['uri'] if selected_class is not None else None, graph=graph['uri'], limit=20)

            # If some entities match: display them with a select option
            st.divider()
            
            # Not found message
            if len(entities) == 0:
                st.info('No such entities found')

            # Display the list of entity as buttons to select them.
            for i, entity in enumerate(entities):
                display_label = f"{entity['label']} ({entity['class_label']})"
                if st.button(display_label, type='tertiary', key=f"find_entity_{i}"):
                    st.session_state['selected_entity'] = {
                        'uri': entity['uri'],
                        'display_label': display_label,
                        'class_uri': entity['cls'],
                        'class_label': entity['class_label'],
                    }
                    st.rerun()

