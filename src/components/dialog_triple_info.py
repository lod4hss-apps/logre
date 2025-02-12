import streamlit as st
from schema import DisplayTriple
from lib.prefixes import explicits_uri

@st.dialog('Triple information')
def dialog_triple_info(triple: DisplayTriple) -> None:
    
    # Subject
    st.markdown('### Subject')
    col1, col2 = st.columns([1, 3])

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**URI**")
    col2.markdown(f"[{triple.subject.uri}]({explicits_uri(triple.subject.uri)})")

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Label**")
    col2.markdown(triple.subject.label)

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Comment**")
    col2.markdown(triple.subject.comment)

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**Class**")
    col2.markdown(f"{triple.subject.class_label} ([{triple.subject.class_uri}]({explicits_uri(triple.subject.class_uri)}))")

    st.divider()

    # Predicate
    st.markdown('### Predicate')
    col1, col2 = st.columns([1, 3])

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**URI**")
    col2.markdown(f"[{triple.predicate.uri}]({explicits_uri(triple.predicate.uri)})")

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Label**")
    col2.markdown(triple.predicate.label)

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Order**")
    col2.markdown(triple.predicate.order if triple.predicate.order != 1000000000000000000 else '')

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Cardinality**")
    col2.markdown(f"{triple.predicate.min_count if triple.predicate.min_count is not None else 'n'} to {triple.predicate.max_count if triple.predicate.max_count != 1000000000000000000 else 'n' }")
    
    col1, col2 = st.columns([1, 3])
    col1.markdown("**Domain class**")
    col2.markdown(triple.predicate.domain_class_uri)

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Range class**")
    col2.markdown(triple.predicate.range_class_uri)
    

    st.divider()

    # Object

    if triple.object.is_literal:
        st.markdown('### Object (Literal)')
        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**Value**")
        col2.markdown(triple.object.label)

    else:
        st.markdown('### Object')

        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**URI**")
        col2.markdown(f"[{triple.object.uri}]({explicits_uri(triple.object.uri)})")

        col1, col2 = st.columns([1, 3])
        col1.markdown("**Label**")
        col2.markdown(triple.object.label)

        col1, col2 = st.columns([1, 3])
        col1.markdown("**Comment**")
        col2.markdown(triple.object.comment or '')

        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**Class**")
        col2.markdown(f"{triple.object.class_label} ([{triple.object.class_uri}]({explicits_uri(triple.object.class_uri)}))")



