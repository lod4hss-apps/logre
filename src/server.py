# import streamlit as st
# import lib.state as state

# # Load the query parameters
# state.set_query_params(st.query_params)

# # Dispatch to right page
# if 'page' not in st.query_params:
#     st.switch_page("pages/documentation.py")
# else:
#     st.switch_page(f"pages/{st.query_params['page']}.py")


import streamlit as st

def on_save_option(option_name):
    st.session_state['options'][option_name] = st.session_state[option_name]

if 'options' not in st.session_state:
    st.session_state['options'] = {
        'option1': 'foo',
        'option2': 'abc',
        'option3': 123
    }

options_1 = ["foo", "bar", "bazz"]
options_2 = ["abc", "def", "ghi"]
options_3 = [123, 456, 789]

option1 = st.selectbox('Option 1', options=options_1, key="option1")
st.write(option1)
if option1 != st.session_state['options']['option1']:
    st.button('Save option 1', on_click=on_save_option, args=('option1',))

option2 = st.selectbox('Option 2', options=options_2, key="option2")
st.write(option2)
if option2 != st.session_state['options']['option2']:
    st.button('Save option 2', on_click=on_save_option, args=('option2',))

option3 = st.selectbox('Option 3', options=options_3, key="option3")
st.write(option3)
if option3 != st.session_state['options']['option3']:
    st.button('Save option 3', on_click=on_save_option, args=('option3',))

st.divider()

st.write('Session State:')
st.write(st.session_state)