import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from doc_loaders import *
import tempfile
from langchain_core.prompts import ChatPromptTemplate

# --- Constantes e Configurações Globais ---
MEMORIA = ConversationBufferMemory()

TIPOS_ARQUIVOS_VALIDOS = [
    'Site', 'Youtube', 'PDF', 'CSV', 'TXT'
]

CONFIG_MODELOS = {
    'Groq': {
        'modelos': ['llama3-70b-8192', "llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
        'chat': ChatGroq
    },
    'OpenAI': {
        'modelos': ['gpt-3.5-turbo', 'o1-mini', 'gpt-4o-mini'],
        'chat': ChatOpenAI
    }
}

# --- Funções de Carregamento e Processamento ---
def carrega_arquivo(tipo_arquivo, arquivo):
    """
    Carrega o conteúdo de um arquivo ou URL, dependendo do tipo especificado.

    Args:
        tipo_arquivo (str): O tipo de fonte ('Site', 'Youtube', 'PDF', etc.).
        arquivo (str ou uploaded_file): O conteúdo ou caminho para o arquivo.

    Returns:
        str: O conteúdo do documento carregado.
    """
    documento = ''
    if tipo_arquivo == 'Site':
        documento = carrega_site(arquivo)
    
    elif tipo_arquivo == 'Youtube':
        documento = carrega_video(arquivo)
    
    # Para arquivos de upload, cria um arquivo temporário para processamento
    elif tipo_arquivo == 'PDF':
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_pdf(nome_temp)
    
    elif tipo_arquivo == 'CSV':
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_csv(nome_temp)
    
    elif tipo_arquivo == 'TXT':
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_txt(nome_temp)

    # Inicializa ou mantém a memória na sessão
    st.session_state['memoria'] = MEMORIA
    return documento


def carrega_modelo(provedor, modelo, api_key, tipo_arquivo, arquivo):
    """
    Configura e inicializa a cadeia de processamento (chain) da LangChain.

    Args:
        provedor (str): O provedor do modelo ('Groq' ou 'OpenAI').
        modelo (str): O nome específico do modelo.
        api_key (str): A chave de API para o provedor.
        tipo_arquivo (str): O tipo de arquivo a ser carregado.
        arquivo (str ou uploaded_file): O arquivo ou URL a ser processado.
    """
    documento = carrega_arquivo(tipo_arquivo, arquivo)
    
    # Cria o prompt de sistema com o conteúdo do documento
    system_message = f'''Você é um assistente amigável chamado Oráculo.
    Você possui acesso às seguintes informações vindas de um documento {tipo_arquivo}:

    ####
    {documento}
    ####

    Utilize as informações fornecidas para basear as suas respostas.

    Sempre que houver $ na sua saída, substitua por S.
    
    Se a informação do documento for algo como "Just a moment...Enable JavaScript and cookies to continue"
    sugira ao usuário carregar novamente o Oráculo!'''
    
    template = ChatPromptTemplate.from_messages([
        ('system', system_message),
        ("placeholder", '{chat_history}'),
        ('user', '{input}')
    ])
    
    # Inicializa o modelo de chat com base no provedor
    chat = CONFIG_MODELOS[provedor]['chat'](model=modelo, api_key=api_key)
    chain = template | chat
    
    # Armazena a cadeia na sessão do Streamlit
    st.session_state['chain'] = chain

# --- Funções da Interface do Usuário (Streamlit) ---
def pagina_chat():
    """Define a página principal do chat no Streamlit."""
    st.set_page_config(
        page_title="Oráculo AI",
        page_icon="🤖",
        layout="wide"
    )
    
    st.header("👾 Bem vindo ao Oráculo", divider=True)
    
    # Verifica se a cadeia foi inicializada
    chain = st.session_state.get('chain')
    if chain is None:
        st.error("Carregue o Oráculo para começar.")
        st.stop()
    
    memoria = st.session_state.get('memoria', MEMORIA)
    
    # Exibe o histórico de mensagens
    for mensagem in memoria.chat_memory.messages:
        chat = st.chat_message(mensagem.type)
        chat.markdown(mensagem.content)
    
    input_usuario = st.chat_input("Fale com o Oráculo")
    
    # Lógica de processamento de nova mensagem do usuário
    if input_usuario:
        chat = st.chat_message('human')
        chat.markdown(input_usuario)
        
        chat = st.chat_message('ai')
        resposta = chat.write_stream(chain.stream({
            'input': input_usuario,
            'chat_history': memoria.chat_memory.messages
        }))
        
        # Salva a conversa na memória
        memoria.chat_memory.add_user_message(input_usuario)
        memoria.chat_memory.add_ai_message(resposta)
        st.session_state['memoria'] = memoria
        st.rerun()


def sidebar():
    """Define a barra lateral com as opções de configuração."""
    tabs = st.tabs(['Upload de Arquivos', 'Seleção de Modelos'])
    
    # Tab 1: Upload de Arquivos
    with tabs[0]:
        tipo_arquivo = st.selectbox("Selecione o tipo de arquivo", TIPOS_ARQUIVOS_VALIDOS)
        
        # Lógica para exibir o campo de entrada correto
        if tipo_arquivo == "Site":
            arquivo = st.text_input("Digite a URL do site")
        elif tipo_arquivo == "Youtube":
            arquivo = st.text_input("Digite a URL do vídeo")
        else:
            tipo_file_uploader = {
                "PDF": ".pdf",
                "CSV": ".csv",
                "TXT": ".txt"
            }
            arquivo = st.file_uploader(f"Faça o upload do arquivo {tipo_arquivo}", type=[tipo_file_uploader[tipo_arquivo]])
    
    # Tab 2: Seleção de Modelos
    with tabs[1]:
        provedor = st.selectbox("Selecione o provedor dos modelos", list(CONFIG_MODELOS.keys()))
        modelo = st.selectbox("Selecione o modelo", CONFIG_MODELOS[provedor]['modelos'])
        api_key = st.text_input(
            f"Adicione a API KEY para o provedor {provedor}",
            value=st.session_state.get(f'api_key_{provedor}', '')
        )
        st.session_state[f'api_key_{provedor}'] = api_key
    
    # Botões de ação
    if st.button("Inicializar Oráculo", use_container_width=True):
        if arquivo and api_key:
            carrega_modelo(provedor, modelo, api_key, tipo_arquivo, arquivo)
            memoria = st.session_state.get('memoria', MEMORIA)
            memoria.chat_memory.add_ai_message("Oráculo foi inicializado!🚀")
            st.session_state['memoria'] = memoria
            st.rerun()
        else:
            st.error("Por favor, forneça o arquivo/URL e a API Key.")

    if st.button("Apagar Histórico", use_container_width=True):
        st.session_state['memoria'] = MEMORIA
        st.rerun()

def main():
    """Ponto de entrada da aplicação Streamlit."""
    with st.sidebar:
        sidebar()
    pagina_chat()

if __name__ == '__main__':
    main()