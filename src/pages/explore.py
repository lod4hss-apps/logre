import streamlit as st
from components.init import init
from components.menu import menu
from components.find_entities import dialog_find_entity
from tools.sparql_queries import list_entity_triples
import pandas as pd



##### The page #####

init(layout='wide')
menu()

if 'selected_entity' not in st.session_state or st.button('Find an entity'):
    dialog_find_entity()
else:
    col1, col2 = st.columns([1, 1], vertical_alignment='center')
    col1.markdown('# ' + st.session_state['selected_entity']['display_label'])
    col2.markdown(f"#### {st.session_state['selected_entity']['uri']}")

    with st.spinner('Fetching entity triples...'):
        triples = list_entity_triples(st.session_state['selected_entity']['uri'])
        # st.dataframe(pd.DataFrame(data=triples))

    st.text('')


    for i, triple in enumerate(triples):


        col1, col2, col3 = st.columns([1, 1, 1])

        if 'subject' in triple:
            subject_label = triple['subject_label'] if 'subject_label' in triple else 'No label'
            subject_class_label = triple['subject_class_label'] if 'subject_class_label' in triple else 'Unknown'
            subject_display_label = f"{subject_label} ({subject_class_label})"
            if col1.button(subject_display_label, type='tertiary', key=f'explore-subject-{i}'):
                st.session_state['selected_entity'] = {
                    'uri': triple['subject'],
                    'display_label': subject_display_label
                }
                st.rerun()
        else:
            subject_display_label = st.session_state['selected_entity']['display_label']
            col1.button(subject_display_label, type='tertiary', key=f'explore-subject-{i}')

        if 'predicate' in triple:
            predicate_label = triple['predicate_label'] if 'predicate_label' else 'No label'
            col2.write(predicate_label)


        if 'object' in triple:
            if triple['object_literal'] == 'true':
                object_display_label = triple['object']
                col3.write(object_display_label)
            else:
                object_label = triple['object_label'] if 'object_label' in triple else 'No label'
                object_class_label = triple['object_class_label'] if 'object_class_label' in triple else 'Unknown'
                object_display_label = f"{object_label} ({object_class_label})"
                if col3.button(object_display_label, type='tertiary', key=f'explore-object-{i}'):
                    st.session_state['selected_entity'] = {
                        'uri': triple['object'],
                        'display_label': object_display_label
                    }
                    st.rerun()
        else:
            object_display_label = st.session_state['selected_entity']['display_label']
            col3.button(object_display_label, type='tertiary', key=f'explore-object-{i}')