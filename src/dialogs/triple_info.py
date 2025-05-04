import streamlit as st
from model import Statement
from lib import state

@st.dialog('Triple information')
def dialog_triple_info(triple: Statement) -> None:

    # From state
    endpoint = state.get_endpoint()
    
    # Subject
    st.markdown('### Subject')
    col1, col2 = st.columns([1, 3])

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**URI**")
    col2.markdown(f"[{triple.subject.uri}]({endpoint.sparql.lenghten_prefix(triple.subject.uri)})")

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Label**")
    col2.markdown(triple.subject.label)

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Comment**")
    col2.markdown(triple.subject.comment)

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**Class**")
    col2.markdown(f"{triple.subject.class_label} ([{triple.subject.class_uri}]({endpoint.sparql.lenghten_prefix(triple.subject.class_uri)}))")

    st.divider()

    # Predicate
    st.markdown('### Predicate')
    col1, col2 = st.columns([1, 3])

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**URI**")
    col2.markdown(f"[{triple.predicate.uri}]({endpoint.sparql.lenghten_prefix(triple.predicate.uri)})")

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Label**")
    col2.markdown(triple.predicate.label or '')

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Order**")
    col2.markdown(triple.predicate.order if triple.predicate.order != 1000000000000000000 else '')

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Cardinality**")
    from_count = triple.predicate.min_count or '0'
    to_count = triple.predicate.max_count or 'n' if triple.predicate.max_count != 1000000000000000000 else 'n'
    col2.markdown(f"{from_count} to {to_count}")
    
    col1, col2 = st.columns([1, 3])
    col1.markdown("**Domain class**")
    col2.markdown(triple.predicate.domain_class_uri or '')

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Range class**")
    col2.markdown(triple.predicate.range_class_uri or '')
    

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
        col2.markdown(f"[{triple.object.uri}]({endpoint.sparql.lenghten_prefix(triple.object.uri)})")

        col1, col2 = st.columns([1, 3])
        col1.markdown("**Label**")
        col2.markdown(triple.object.label)

        col1, col2 = st.columns([1, 3])
        col1.markdown("**Comment**")
        col2.markdown(triple.object.comment or '')

        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**Class**")
        first_part = triple.object.class_label or ''
        second_part = f" ([{triple.object.class_uri}]({endpoint.sparql.lenghten_prefix(triple.object.class_uri)}))" if triple.object.class_uri else ""
        col2.markdown(first_part + second_part)



