import streamlit as st
from graphly.schema import Statement, Prefixes, Model

@st.dialog('Triple information')
def dialog_triple_info(statement: Statement, prefixes: Prefixes, model: Model) -> None:
    """
    Displays detailed information about a given RDF triple (statement) in a dialog.

    Args:
        statement (Statement): The triple to display, containing subject, predicate, and object.
        prefixes (Prefixes): Prefix mappings used to expand URIs for display.
        model (Model): The model containing class information for the entities involved.

    Behavior:
        - Shows subject details: URI, label, comment, and class with expanded URI.
        - Shows predicate details: URI, label, order, cardinality, domain, and range.
        - Shows object details:
            - If a literal: displays its value.
            - If a class instance: displays URI, label, comment, and class with expanded URI.

    Returns:
        None
    """
    ### Subject ###

    st.markdown('### Subject')
    col1, col2 = st.columns([1, 3])

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**URI**")
    col2.markdown(f"[{statement.subject.uri}]({prefixes.lengthen(statement.subject.uri)})")

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Label**")
    col2.markdown(statement.subject.label)

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Comment**")
    col2.markdown(statement.subject.comment)

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**Class**")
    subject_class = model.find_class(statement.subject.class_uri)
    col2.markdown(f"{subject_class.get_text()} ([{subject_class.uri}]({prefixes.lengthen(subject_class.uri)}))")

    st.divider()

    ### Predicate ###

    st.markdown('### Predicate')
    col1, col2 = st.columns([1, 3])

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**URI**")
    col2.markdown(f"[{statement.predicate.uri}]({prefixes.lengthen(statement.predicate.uri)})")

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Label**")
    col2.markdown(statement.predicate.label or '')

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Order**")
    col2.markdown(statement.predicate.order if statement.predicate.order else '')

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Cardinality**")
    from_count = statement.predicate.min_count or '0'
    to_count = statement.predicate.max_count or 'n' if statement.predicate.max_count else 'n'
    col2.markdown(f"{from_count} to {to_count}")
    
    col1, col2 = st.columns([1, 3])
    col1.markdown("**Domain class**")
    col2.markdown(statement.predicate.domain.uri or '')

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Range class**")
    col2.markdown(statement.predicate.range.uri or '')

    st.divider()

    ### Object ###

    # If the object is a value
    if statement.object.resource_type == 'literal':
        st.markdown('### Object (Literal)')
        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**Value**")
        col2.markdown(statement.object.literal)

    # If the object is a class instance
    else:
        st.markdown('### Object')

        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**URI**")
        col2.markdown(f"[{statement.object.uri}]({prefixes.lengthen(statement.object.uri)})")

        col1, col2 = st.columns([1, 3])
        col1.markdown("**Label**")
        col2.markdown(statement.object.label)

        col1, col2 = st.columns([1, 3])
        col1.markdown("**Comment**")
        col2.markdown(statement.object.comment or '')

        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**Class**")
        object_class = model.find_class(statement.object.class_uri)
        col2.markdown(f"{object_class.get_text()} ([{object_class.uri}]({prefixes.lengthen(object_class.uri)}))")