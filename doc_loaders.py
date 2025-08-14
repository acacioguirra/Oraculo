from time import sleep
import os
from langchain_community.document_loaders import (WebBaseLoader,
                                                  YoutubeLoader,
                                                  CSVLoader,
                                                  PyPDFLoader,
                                                  TextLoader)
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from fake_useragent import UserAgent
import streamlit as st

# Configuração inicial do User-Agent para o ambiente
os.environ["USER_AGENT"] = 'meuapp-orion'

def carrega_site(url):
    """
    Carrega o conteúdo de uma página web a partir de uma URL.

    Args:
        url (str): A URL da página web a ser carregada.

    Returns:
        str: O conteúdo da página web como uma única string, ou uma string vazia em caso de falha.
    """
    documento = ''
    for i in range(5):
        try:
            # Altera o User-Agent a cada tentativa para evitar bloqueios
            os.environ["USER_AGENT"] = UserAgent().random
            loader = WebBaseLoader(url, raise_for_status=True)
            lista_documentos = loader.load()
            conteudos = [doc.page_content for doc in lista_documentos]
            documento = '\n\n'.join(conteudos)
            break
        except Exception as e:
            print(f"Erro ao carregar o site (tentativa {i+1}): {e}")
            sleep(3)
    
    if documento == '':
        st.error('Não foi possível carregar o site.')
        st.stop()
    
    return documento

def carrega_video(id_video):
    """
    Carrega a transcrição de um vídeo do YouTube.

    Args:
        id_video (str): O ID do vídeo do YouTube.

    Returns:
        str: A transcrição do vídeo como uma única string.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(id_video, languages=['pt'])
        conteudos = [item['text'] for item in transcript]
        documento = '\n\n'.join(conteudos)
        return documento
    except (NoTranscriptFound, TranscriptsDisabled) as e:
        print(f"Erro ao carregar a transcrição do vídeo: {e}")
        st.error("Não foi possível encontrar a transcrição em português para este vídeo.")
        st.stop()
    except Exception as e:
        print(f"Erro inesperado ao carregar a transcrição: {e}")
        st.error("Ocorreu um erro ao tentar carregar a transcrição do vídeo.")
        st.stop()
        
def carrega_csv(caminho):
    """
    Carrega o conteúdo de um arquivo CSV.

    Args:
        caminho (str): O caminho para o arquivo CSV.

    Returns:
        str: O conteúdo do arquivo CSV como uma única string.
    """
    loader = CSVLoader(caminho, encoding='utf-8')
    lista_documentos = loader.load()
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento

def carrega_pdf(caminho):
    """
    Carrega o conteúdo de um arquivo PDF.

    Args:
        caminho (str): O caminho para o arquivo PDF.

    Returns:
        str: O conteúdo do arquivo PDF como uma única string.
    """
    loader = PyPDFLoader(caminho)
    lista_documentos = loader.load()
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento

def carrega_txt(caminho):
    """
    Carrega o conteúdo de um arquivo de texto (.txt).

    Args:
        caminho (str): O caminho para o arquivo de texto.

    Returns:
        str: O conteúdo do arquivo de texto como uma única string.
    """
    loader = TextLoader(caminho)
    lista_documentos = loader.load()
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento