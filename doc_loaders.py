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

os.environ["USER_AGENT"] = 'meuapp-orion'


def carrega_site(url):
    documento = ''
    for i in range(5):
        try:
            os.environ["USER_AGENT"] = UserAgent().random    
            loader = WebBaseLoader(url, raise_for_status=True)
            lista_documentos = loader.load()
            conteudos=[]
            for doc in lista_documentos:
                conteudos.append(doc.page_content)
            documento = '\n\n'.join(conteudos)    
            #documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
            break
        except:
            print(f"Erro ao carregar o site{i+1}")
            sleep(3)
    if documento == '':
        st.error('Não foi possivel carregar o site')
        st.stop()
    return documento


def carrega_video(id_video):
    transcript = YouTubeTranscriptApi.get_transcript(id_video, languages=['pt'])
    conteudos=[]
    for item in transcript:
        conteudos.append(item['text'])
    documento = '\n\n'.join(conteudos)
    #texto = "\n".join([item['text'] for item in transcript])
    return documento


def carrega_csv(caminho):
    loader = CSVLoader(caminho, encoding='utf-8')
    lista_documentos = loader.load()  
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento

def carrega_pdf(caminho):
    loader = PyPDFLoader(caminho)
    lista_documentos = loader.load()  
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento

def carrega_txt(caminho):
    loader = TextLoader(caminho)
    lista_documentos = loader.load()  
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento
