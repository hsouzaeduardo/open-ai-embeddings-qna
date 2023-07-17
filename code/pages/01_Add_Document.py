import streamlit as st
import os, json, re, io
from os import path
import requests
import mimetypes
import traceback
import chardet
from utilities.helper import LLMHelper
import uuid
from redis.exceptions import ResponseError 
from urllib import parse
    
def upload_text_and_embeddings():
    file_name = f"{uuid.uuid4()}.txt"
    source_url = llm_helper.blob_client.upload_file(st.session_state['doc_text'], file_name=file_name, content_type='text/plain; charset=utf-8')
    llm_helper.add_embeddings_lc(source_url) 
    st.success("Embeddings adicionadas com sucesso.")

def remote_convert_files_and_add_embeddings(process_all=False):
    url = os.getenv('CONVERT_ADD_EMBEDDINGS_URL')
    if process_all:
        url = f"{url}?process_all=true"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            st.success(f"{response.text}\nPlease note this is an asynchronous process and may take a few minutes to complete.")
        else:
            st.error(f"Error: {response.text}")
    except Exception as e:
        st.error(traceback.format_exc())

def delete_row():
    st.session_state['data_to_drop'] 
    redisembeddings.delete_document(st.session_state['data_to_drop'])

def add_urls():
    urls = st.session_state['urls'].split('\n')
    for url in urls:
        if url:
            llm_helper.add_embeddings_lc(url)
            st.success(f"Embeddings added successfully for {url}")

def upload_file(bytes_data: bytes, file_name: str):
    # Upload a new file
    st.session_state['filename'] = file_name
    content_type = mimetypes.MimeTypes().guess_type(file_name)[0]
    charset = f"; charset={chardet.detect(bytes_data)['encoding']}" if content_type == 'text/plain' else ''
    st.session_state['file_url'] = llm_helper.blob_client.upload_file(bytes_data, st.session_state['filename'], content_type=content_type+charset)


try:
    # Set page layout to wide screen and menu item
    menu_items = {
	'Get help': None,
	'Report a bug': None,
	'About': '''
	 ## Embeddings App
	 Embedding testing application.
	'''
    }
    st.set_page_config(layout="wide", menu_items=menu_items)

    llm_helper = LLMHelper()

    with st.expander("Adicionar um único documento à base de conhecimento", expanded=True):
        st.write("Para PDF pesado ou longo, use a opção 'Adicionar documentos em lote' abaixo.")
        st.checkbox("Traduzir documento para inglês", key="translate")
        uploaded_file = st.file_uploader("Carregue um documento para adicioná-lo à base de conhecimento", type=['pdf','jpeg','jpg','png', 'txt'])
        if uploaded_file is not None:
            # To read file as bytes:
            bytes_data = uploaded_file.getvalue()

            if st.session_state.get('filename', '') != uploaded_file.name:
                upload_file(bytes_data, uploaded_file.name)
                converted_filename = ''
                if uploaded_file.name.endswith('.txt'):
                    # Add the text to the embeddings
                    llm_helper.add_embeddings_lc(st.session_state['file_url'])

                else:
                    # Get OCR with Layout API and then add embeddigns
                    converted_filename = llm_helper.convert_file_and_add_embeddings(st.session_state['file_url'], st.session_state['filename'], st.session_state['translate'])
                
                llm_helper.blob_client.upsert_blob_metadata(uploaded_file.name, {'converted': 'true', 'embeddings_added': 'true', 'converted_filename': parse.quote(converted_filename)})
                st.success(f"Arquivo {uploaded_file.name} de embeddings adicionado à base de conhecimento.")
            
            # pdf_display = f'<iframe src="{st.session_state["file_url"]}" width="700" height="1000" type="application/pdf"></iframe>'

    with st.expander("Adicionar texto à base de conhecimento", expanded=False):
        col1, col2 = st.columns([3,1])
        with col1: 
            st.session_state['doc_text'] = st.text_area("Adicione um novo conteúdo de texto e clique em 'Compute Embeddings'", height=600)

        with col2:
            st.session_state['embeddings_model'] = st.selectbox('Embeddings models', [llm_helper.get_embeddings_model()['doc']], disabled=True)
            st.button("Compute Embeddings", on_click=upload_text_and_embeddings)

    with st.expander("Adicionar documentos em lote", expanded=False):
        uploaded_files = st.file_uploader("Carregue um documento para adicioná-lo à conta de armazenamento do Azure", type=['pdf','jpeg','jpg','png', 'txt'], accept_multiple_files=True)
        if uploaded_files is not None:
            for up in uploaded_files:
                # To read file as bytes:
                bytes_data = up.getvalue()

                if st.session_state.get('filename', '') != up.name:
                    # Upload a new file
                    upload_file(bytes_data, up.name)
                    if up.name.endswith('.txt'):
                        # Add the text to the embeddings
                        llm_helper.blob_client.upsert_blob_metadata(up.name, {'converted': "true"})

        col1, col2, col3 = st.columns([2,2,2])
        with col1:
            st.button("Converta novos arquivos e adicione incorporações", on_click=remote_convert_files_and_add_embeddings)
        with col3:
            st.button("Converta todos os arquivos e adicione embeddings", on_click=remote_convert_files_and_add_embeddings, args=(True,))

    with st.expander("Adicionar URLs à base de conhecimento", expanded=True):
        col1, col2 = st.columns([3,1])
        with col1: 
            st.session_state['urls'] = st.text_area("Adicione URLs e clique em 'Compute Embeddings'", placeholder="COLOQUE SUAS URLS AQUI SEPARADAS POR UMA NOVA LINHA", height=100)

        with col2:
            st.selectbox('Embeddings models', [llm_helper.get_embeddings_model()['doc']], disabled=True, key="embeddings_model_url")
            st.button("Compute Embeddings", on_click=add_urls, key="add_url")

    with st.expander("Exibir documentos na base de conhecimento", expanded=False):
        # Query RediSearch to get all the embeddings
        try:
            data = llm_helper.get_all_documents(k=1000)
            if len(data) == 0:
                st.warning("Nenhuma incorporação encontrada. Copie e cole seus dados na entrada de texto e clique em 'Compute Embeddings' ou drag-and-drop seus documentos.")
            else:
                st.dataframe(data, use_container_width=True)
        except Exception as e:
            if isinstance(e, ResponseError):
                st.warning("Nenhuma incorporação encontrada. Copie e cole seus dados na entrada de texto e clique em 'Compute Embeddings' out drag-and-drop seus documentos.")
            else:
                st.error(traceback.format_exc())


except Exception as e:
    st.error(traceback.format_exc())
