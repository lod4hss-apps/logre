import streamlit as st
import json
from components.init import init
from components.menu import menu
from lib import state
from dialogs.confirmation import dialog_confirmation

# Initialize
init('wide')
menu()

# From state
data_bundle = state.get_data_bundle()
entity_uri = state.get_entity_uri()

# Title
col1, col2 = st.columns([5, 1], vertical_alignment="center")
col1.title("Data Bundle model")
col1.text('')

# with col2.container(horizontal=True, horizontal_alignment='right'):
  # if st.button('Save'):
  #   def replace_model() -> None:
  #     # Clear old model
  #     data_bundle.delete('model', ('?s', '?p', '?o'))
  #     # Upload new Turtle
  #     graph_uri = data_bundle.prefixes.lengthen(data_bundle.graph_model.uri)
  #     prefixes = json.dumps('\n'.join(list(map(lambda prefix: prefix.to_turtle(), data_bundle.prefixes))).split('<'))
  #     st.html(f"""
  #         <script>
  #             var endpointTechnology = "{data_bundle.endpoint.technology_name}";
  #             var username = "{data_bundle.endpoint.username}";
  #             var password = "{data_bundle.endpoint.password}";
  #             var url = "{data_bundle.endpoint.url}";
  #             var graphURI = "{graph_uri}";
  #             var prefixes = {prefixes}.join("<");
  #             uploadTurtle(endpointTechnology, username, password, url, graphURI, prefixes); 
  #         </script>
  #     """, unsafe_allow_javascript=True)
  #   dialog_confirmation("Your are about to clear your model Named Graph and replace it by what is currently displayed.", replace_model, rerun=False)

# Get the js code
with open("src/lib/shacl-maker.js") as file:
  js_code = file.read().strip()

properties_string = json.dumps([property.to_dict() for property in data_bundle.model.properties], ensure_ascii=False).replace("'", '')

st.html('<canvas id="canvas-shacl-maker" width="1450" height="800" tabindex="0"></canvas>')
st.html(f"<script>{js_code}</script>", unsafe_allow_javascript=True)
st.html(f"""
  <script>
    setCanvas(document.getElementById('canvas-shacl-maker'));
    var triples = JSON.parse('{properties_string}')

    addTriples(triples);
  </script>
""", unsafe_allow_javascript=True)


st.title('How to...')

st.markdown('##### ... select a box or a link?')
st.markdown('> Simply click on it.')

st.markdown('##### ... unselect a box or a link?')
st.markdown('> Simply click on the empty space.')

st.markdown('##### ... create a new box?')
st.markdown('> When nothing is selected, press on "b" on your keyboard (canvas should be focused).')

st.markdown('##### ... edit a box (class URI or name)?')
st.markdown('> When a box(es) is(are) selected, simply hit the keyboard, this will change the box content. Remember that first line is the class URI, and second is the class name.')

st.markdown('##### ... move one or multiple boxes?')
st.markdown('> To move something, you need to select it, and then drag and drop on the canvas.')

st.markdown('##### ...move everything?')
st.markdown('> To move everything - or said otherwise, to move the camera - just have nothing selected and drag and drop')

st.markdown('##### ... zoom or unzoom?')
st.markdown('> Use your wheeler (mouse or pad) to zoom or unzoom. There is also a way of fitting all your model in the canvas at once: press "z" key.')

st.markdown('##### ... link two boxes?')
st.markdown('> When nothing is selected, press "l" key, that will activate the create link mode (not visible at this point). Then you need to click on the first box concerned by the link (the subject). Your will then see your mouse linked to the box. Finally, click on the target (the object). You have then created a link (a predicate)!')

st.markdown('##### ... change information of a link?')
st.markdown('> When a link is selected, you just can hit the keyboard, and it will start the update. To update the predicate label, write "label: " followed by the label you would like to set/update. To update the URI of the link, write "uri: " followed by the uri you want to set/update. To update the cardinatlity of the link, write "card: " followed by the cardinality you want to set/update (eg: "0..3" or "0..\*" or "1"). To update the order of appearance of the property in formular, write "order: " followed by the order you want to set/update. You can also update multiple attribute at once, for example you can write "uri: rdfs:label - label: has name - card: 0..\*"')