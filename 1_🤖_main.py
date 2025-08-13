import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from doc_loaders import *
import tempfile
from langchain_core.prompts import ChatPromptTemplate

MEMORIA = ConversationBufferMemory()

TIPOS_ARQUIVOS_VALIDOS = [
    'Site', 'Youtube', 'PDF', 'CSV', 'TXT'
]

CONFIG_MODELOS = {  'Groq':
                            {'modelos': ['llama3-70b-8192', "llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
                            'chat': ChatGroq},
                    'OpenAI':
                            {'modelos': ['gpt-3.5-turbo', 'o1-mini', 'gpt-4o-mini'],
                            'chat': ChatOpenAI}
}


def carrega_arquivo(tipo_arquivo, arquivo):
    if tipo_arquivo == 'Site':
        documento = carrega_site(arquivo)

    if tipo_arquivo == 'Youtube':
        documento = carrega_video(arquivo)

    if tipo_arquivo == 'PDF':
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_pdf(nome_temp)

    if tipo_arquivo == 'CSV':
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_pdf(nome_temp)

    if tipo_arquivo == 'TXT':
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_pdf(nome_temp)
    st.session_state['memoria'] = MEMORIA
    return documento


def carrega_modelo(provedor, modelo, api_key, tipo_arquivo, arquivo):

    documento = carrega_arquivo(tipo_arquivo, arquivo)

    #Prompt
    system_message = '''Você é um assistente amigável chamado Oráculo.
    Você possui acesso às seguintes informações vindas 
    de um documento {}: 

    ####
    {}
    ####

    Utilize as informações fornecidas para basear as suas respostas.

    Sempre que houver $ na sua saída, substita por S.
     
    Se a informação do documento for algo como "Just a moment...Enable JavaScript and cookies to continue"
    sugira ao usuário carregar novamente o Oráculo!'''.format(tipo_arquivo, documento)

    template = ChatPromptTemplate.from_messages([
        ('system', system_message),
        ("placeholder", '{chat_history}'),
        ('user', '{input}')
    ])

    chat = CONFIG_MODELOS[provedor]['chat'](model=modelo, api_key=api_key)  
    chain = template | chat

    st.session_state['chain'] = chain

def pagina_chat():

    st.set_page_config(
        page_title="Oráculo AI",
        page_icon="🤖",
        layout="wide"
    )

    st.header("👾 Bem vindo ao Oráculo", divider = True)

    chain = st.session_state.get('chain')
    if chain is None:
        st.error("Carregue o Oráculo")
        st.stop()

    memoria = st.session_state.get('memoria', MEMORIA)

    for mensagem in memoria.chat_memory.messages:
        chat = st.chat_message(mensagem.type)
        chat.markdown(mensagem.content)

    input_usuario = st.chat_input("Fale com o Oráculo")

    if input_usuario:
        #USUARIO
        chat = st.chat_message('human')
        chat.markdown(input_usuario)

        #IA
        chat = st.chat_message('ai')
        resposta = chat.write_stream(chain.stream({
            'input': input_usuario,
            'chat_history': memoria.chat_memory.messages
            }))

        #Salvando na Memoria
        memoria.chat_memory.add_user_message(input_usuario)
        memoria.chat_memory.add_ai_message(resposta)
        st.session_state['memoria'] = memoria
        st.rerun()

def sidebar():
    tabs = st.tabs(['Upload de Arquivos', 'Seleção de Modelos'])
    with tabs[0]:
        tipo_arquivo = st.selectbox("Selecione o tipo de arquiivo", TIPOS_ARQUIVOS_VALIDOS)
        if tipo_arquivo == "Site":
            arquivo = st.text_input("Digite a URL do site")

        if tipo_arquivo == "Youtube":
            arquivo = st.text_input("Digite a URL do video ")

        if tipo_arquivo == "PDF":
            arquivo = st.file_uploader("Faça o upload do arquivo pdf", type=['.pdf'])

        if tipo_arquivo == "CSV":
            arquivo = st.file_uploader("Faça o upload do arquivo CSV", type=['.csv'])

        if tipo_arquivo == "TXT":
            arquivo = st.file_uploader("Faça o upload do arquivo TXT", type=['.txt'])

    with tabs[1]:
        provedor = st.selectbox("Selecione o provedor ods modelos", CONFIG_MODELOS.keys())

        modelo = st.selectbox("Selecione o modelo", CONFIG_MODELOS[provedor]['modelos'])

        api_key = st.text_input(
            f"Adicione a API KEY para o provedor {provedor}",
            value = st.session_state.get(f'api_key_{provedor}')
        )
    
        st.session_state[f'api_key_{provedor}'] = api_key

    if st.button("Inicializar Oráculo", use_container_width=True):
        carrega_modelo(provedor, modelo, api_key, tipo_arquivo, arquivo)

        memoria = st.session_state.get('memoria', MEMORIA)
        memoria.chat_memory.add_ai_message("Oráculo foi inicializado!🚀")
        st.session_state['memoria'] = memoria

    if st.button("Apagar Histórico", use_container_width=True):
        st.session_state['memoria'] = MEMORIA

def main():
    with st.sidebar:
        sidebar()
    pagina_chat()
    

if __name__ == '__main__':
    main()