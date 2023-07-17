import streamlit as st
import traceback
from utilities.helper import LLMHelper

def clear_summary():
    st.session_state['summary'] = ""

def get_custom_prompt():
    customtext = st.session_state['customtext']
    customprompt = "{}".format(customtext)
    return customprompt

def customcompletion():
    response = llm_helper.get_completion(get_custom_prompt(), max_tokens=500)
    st.session_state['result'] = response.encode().decode()

try:
    # Set page layout to wide screen and menu item
    menu_items = {
    'Ajuda': None,
    'Reportar a bug': None,
    'Sobre': '''
     ## Embeddings App
     Embedding testing application.
    '''
    }
    st.set_page_config(layout="wide", menu_items=menu_items)

    st.markdown("## Traga seu próprio prompt")

    llm_helper = LLMHelper()

    # displaying a box for a custom prompt
    st.session_state['customtext'] = st.text_area(label="Prompt",value='Digite o seu prompt e e receba o resultado.', height=800)
    st.button(label="Consultar a resposta", on_click=customcompletion)
    # displaying the summary
    result = ""
    if 'result' in st.session_state:
        result = st.session_state['result']
    st.text_area(label="Resultado", value=result, height=200)

except Exception as e:
    st.error(traceback.format_exc())
