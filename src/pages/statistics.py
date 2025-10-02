import streamlit as st
import pandas as pd
from requests.exceptions import HTTPError, ConnectionError
from code_editor import code_editor
from components.init import init
from components.menu import menu
from lib import state
from lib.errors import get_HTTP_ERROR_message
from dialogs.confirmation import dialog_confirmation
from dialogs.query_name import dialog_query_name
from dialogs.confirmation import dialog_confirmation
import plotly.graph_objects as go

# Initialize
init(layout='wide')
menu()

try:

    # From state
    data_bundle = state.get_data_bundle()


    with st.container(horizontal=True, horizontal_alignment='distribute'):
    # Classes Pie chart

        with st.spinner('Counting classes'):
            query = f"""
                SELECT ?class (COUNT(?instance) AS ?count)
                WHERE {{
                    {data_bundle.graph_data.sparql_begin}
                        ?instance {data_bundle.model.type_property} ?class .
                    {data_bundle.graph_data.sparql_end}
                }}
                GROUP BY ?class
                ORDER BY DESC(?count)
            """
            results = data_bundle.run(query)
            total = sum([result['count'] for result in results])

        labels = [data_bundle.model.find_class(result["class"]).label for result in results]
        values = [result["count"] for result in results]
        orange_colors = ['rgb(255, 230, 204)', 'rgb(255, 216, 179)', 'rgb(255, 204, 153)', 'rgb(255, 191, 128)', 'rgb(255, 179, 102)', 'rgb(255, 165, 77)', 'rgb(255, 153, 51)', 'rgb(255, 140, 26)', 'rgb(255, 127, 0)', 'rgb(230, 115, 0)', 'rgb(204, 102, 0)', 'rgb(179, 89, 0)']

        if len(results):
            chart = go.Pie(
                labels=labels,
                values=values,
                hole=0.5,
                title=f"Total: {total}",
                textposition="inside",
                textinfo="percent+label",
                name="",
                marker_colors=orange_colors
            )
            fig = go.Figure()
            fig.add_trace(chart)
            fig.update_layout(showlegend=False, title=f"Classes distribution", title_x=0.4)
            st.plotly_chart(fig)
        else:
            with st.container(horizontal=True, horizontal_alignment='center'):
                st.markdown('*There is no instances in the data*', width='content')


        # Properties Pie chart

        with st.spinner('Counting properties'):
            query = f"""
                SELECT ?property (COUNT(*) AS ?count)
                WHERE {{
                    {data_bundle.graph_data.sparql_begin}
                        ?subject ?property ?object .
                    {data_bundle.graph_data.sparql_end}
                }}
                GROUP BY ?property
                ORDER BY DESC(?count)
            """
            results = data_bundle.run(query)
            # Filter out type, label and comment properties
            results = [result for result in results if result['property'] not in [data_bundle.model.type_property, data_bundle.model.label_property, data_bundle.model.comment_property]]
            total = sum([result['count'] for result in results])

        labels = [data_bundle.model.find_properties(result["property"])[0].label for result in results]
        values = [result["count"] for result in results]
        orange_colors = ['rgb(255, 230, 204)', 'rgb(255, 216, 179)', 'rgb(255, 204, 153)', 'rgb(255, 191, 128)', 'rgb(255, 179, 102)', 'rgb(255, 165, 77)', 'rgb(255, 153, 51)', 'rgb(255, 140, 26)', 'rgb(255, 127, 0)', 'rgb(230, 115, 0)', 'rgb(204, 102, 0)', 'rgb(179, 89, 0)']

        if len(results):
            chart = go.Pie(
                labels=labels,
                values=values,
                hole=0.5,
                title=f"Total: {total}",
                textposition="inside",
                textinfo="percent+label",
                name="",
                marker_colors=orange_colors
            )
            fig = go.Figure()
            fig.add_trace(chart)
            fig.update_layout(showlegend=False, title=f"Properties distribution", title_x=0.37)
            st.plotly_chart(fig)
        else:
            with st.container(horizontal=True, horizontal_alignment='center'):
                st.markdown('*There is no triple in the data*', width='content')


except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.error(message)
    print(message.replace('\n\n', '\n'))

except ConnectionError as err:
    st.error('Failed to connect to server: check your internet connection and/or server status.')
    print('[CONNECTION ERROR]')