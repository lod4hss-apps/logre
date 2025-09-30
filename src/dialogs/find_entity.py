import streamlit as st
from requests.exceptions import HTTPError, ConnectionError
from lib import state
from lib.errors import get_HTTP_ERROR_message
from lib.utils import get_max_length_text


@st.dialog('Find an entity', width='medium')
def dialog_find_entity() -> None:
    """
    Displays a dialog for searching and selecting an entity within the selected Data Bundle.

    Behavior:
        - Allows filtering entities by class and by partial label match.
        - Lets the user choose the number of entities to retrieve.
        - Displays a list of matching entities as buttons, truncating labels if necessary.
        - Updates the application state with the selected entity URI and navigates to the entity page upon selection.

    Returns:
        None
    """
    try: 

        # From state
        data_bundle = state.get_data_bundle()

        with st.container(horizontal=True):
            # Class filter
            classes_labels = [c.get_text() for c in data_bundle.model.classes if c.class_uri != 'rdfs:Datatype']
            class_label = st.selectbox('Find instance of class:', options=classes_labels, index=None, width=220)

            # Label filter
            entity_label = st.text_input('Entity label contains:', help='Write the entity label (or a part of it) and hit "Enter"')

            # Retrieved entities
            limit = st.selectbox('Number to retrieve:', options=[10, 20, 50, 100], width=120)

            # Find the selected entity from the selected label
            if class_label:
                class_index = classes_labels.index(class_label)
                selected_class_uri = data_bundle.model.classes[class_index].uri
            else:
                selected_class_uri = None

        st.divider()    

        # Fetch the entities
        label = entity_label if entity_label else ''
        entities = data_bundle.find_entities(label=label, class_uri=selected_class_uri, limit=limit)

        # Set the state selected entity as being the one chosen
        for i, entity in enumerate(entities):
            entity_text = get_max_length_text(entity.get_text(comment=True), 90)
            if st.button(entity_text, type='tertiary', key=f'dlg-find-entity-{i}'):
                state.set_entity_uri(entity.uri)
                st.switch_page("pages/entity.py")
    
    except HTTPError as err:
        message = get_HTTP_ERROR_message(err)
        st.error(message)
        print(message.replace('\n\n', '\n'))

    except ConnectionError as err:
        st.error('Failed to connect to server: check your internet connection and/or server status.')
        print('[CONNECTION ERROR]')