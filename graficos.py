import streamlit as st 
import pandas as pd
import altair as alt
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
import re
from llama_index.llms.groq import Groq
from llama_index.core import VectorStoreIndex, get_response_synthesizer
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core import Settings
from llama_index.vector_stores.duckdb import DuckDBVectorStore

import os

# ===== CSS global: títulos e labels em branco =====
st.markdown("""
    <style>
    h1, h2, h3, h4, h5, h6, .stTabs [data-baseweb="tab"] {
        color: white !important;
    }
    label, .st-bk, .st-af, .st-ag, .st-ah, .st-ai { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# ===== LLM & Embeddings (E-Cris) =====
with open('chave_groq', 'r') as arquivo:
    chave_groq = arquivo.read().strip()  # remove quebras de linha

# Modelo principal e fallback
GROQ_PRIMARY = 'llama-3.3-70b-versatile'
GROQ_FALLBACK = 'llama-3.2-11b-text-preview'  # opcional

def make_llm(model_name=GROQ_PRIMARY, temperature=0):
    return Groq(api_key=chave_groq, model=model_name, temperature=temperature)

Settings.llm = make_llm()

modelo_embeddings = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
Settings.embed_model = HuggingFaceEmbedding(model_name=modelo_embeddings)
Settings.chunk_size = 2048
Settings.chunk_overlap = 512

# ===== Vector store / índice =====
vector_store = DuckDBVectorStore.from_local("./rag.duckdb")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
vector_index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

# Retriever mais amplo + pós-processamento leve
retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=8)
postprocessors = [SimilarityPostprocessor(similarity_threshold=0.05)]
response_synthesizer = get_response_synthesizer(response_mode='tree_summarize')

# IMPORTANTE: sem streaming aqui
query_engine = RetrieverQueryEngine.from_args(
    retriever=retriever,
    response_synthesizer=response_synthesizer,
    node_postprocessors=postprocessors
)

# ===== NLTK: baixar stopwords só se faltar =====
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# ===== Sidebar =====
with st.sidebar:
    st.sidebar.image("Coca-Cola_logo.svg", width=200) 
    st.subheader("Sobre o aplicativo")
    st.markdown("""
    <div style="text-align: justify;">
        O aplicativo apresenta gráficos e tabelas que avaliam as opiniões no TikTok sobre cada subsidiária da Coca-Cola Company, classificando-as como neutras, positivas ou negativas. Na aba "Monitoramento", é possível acessar uma visão geral da holding com todos os gráficos de forma condensada, oferecendo um panorama completo. O sistema de monitoramento de crises avalia a gravidade das situações enfrentadas por cada subempresa, e com o auxílio da assistente virtual E-Cris, é possível garantir uma gestão mais eficiente, fornecendo orientações sobre tipos de crises e as melhores práticas de gerenciamento.
    </div>
    """, unsafe_allow_html=True)

# ===== Título =====
st.markdown("<h1 style='color: red;'>The Coca-Cola Company</h1>", unsafe_allow_html=True)

# ===== Funções auxiliares =====
@st.cache_data
def load_df():
    # ajuste o encoding se necessário ('latin-1' caso seu CSV esteja assim)
    return pd.read_csv('Comentários combinados - combined_comments (1).csv', encoding='utf-8')

def answer_with_fallback(q: str) -> str:
    # 1) tenta via RAG
    try:
        resp = query_engine.query(q)
        text = getattr(resp, "response", "") or str(resp)
        if text.strip():
            return text
    except Exception:
        st.info("Alternando para resposta direta do modelo (sem RAG).")

    # 2) pergunta direta ao LLM (sem RAG)
    try:
        sys = ("Você é a E-Cris, assistente de gestão de crises. "
               "Responda com passos práticos, tom profissional e objetivos.")
        direct = Settings.llm.chat(messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": q}
        ])
        return direct.message.content
    except Exception:
        # 3) fallback final trocando para o modelo leve
        try:
            Settings.llm = make_llm(model_name=GROQ_FALLBACK)
            direct = Settings.llm.chat(messages=[
                {"role": "system", "content": "Você é a E-Cris, assistente de gestão de crises."},
                {"role": "user", "content": q}
            ])
            return direct.message.content
        except Exception:
            return "Não consegui gerar a resposta agora. Verifique a chave Groq e a conectividade."

# ===== Abas =====
tab1, tab2 = st.tabs(["Monitoramento", "E-Cris"])

# ===== Aba de monitoramento =====
with tab1:
    st.markdown("<h2 style='color: white; font-size: 24px; font-weight: bold;'>Escolha uma das subsidiárias para monitorar:</h2>", unsafe_allow_html=True)

    option = st.selectbox(
        "Qual subsidiária você quer monitorar?",
        ("Fanta", "Coca-Cola", "Del Valle", "Schweppes")
    )

    combined_df = load_df()

    filtered_df = combined_df[combined_df['subsidiária'] == option]

    st.write("Amostra dos dados:")
    st.dataframe(filtered_df)

    # Contagem dos sentimentos
    sentiment_counts = filtered_df['sentimento'].value_counts().reset_index()
    sentiment_counts.columns = ['sentimento', 'count']

    # Cores dos sentimentos (Altair)
    color_scale = alt.Scale(domain=['positivo', 'neutro', 'negativo'],
                            range=['#1f77b4', '#aec7e8', '#d62728'])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribuição de Sentimentos")
        bar_chart = alt.Chart(sentiment_counts).mark_bar().encode(
            x=alt.X('sentimento:N', sort='-y', title='Sentimento'),
            y=alt.Y('count:Q', title='Contagem'),
            color=alt.Color('sentimento:N', scale=color_scale, legend=None),
            tooltip=['sentimento', 'count']
        ).properties(width=300, height=300)
        st.altair_chart(bar_chart, use_container_width=False)

    with col2:
        st.subheader("Proporção de Sentimentos")
        pie_chart = alt.Chart(sentiment_counts).mark_arc().encode(
            theta=alt.Theta(field='count', type='quantitative'),
            color=alt.Color('sentimento:N', scale=color_scale),
            tooltip=['sentimento', 'count']
        ).properties(width=300, height=300)
        st.altair_chart(pie_chart, use_container_width=False)

    # Monitoramento de crise
    st.subheader("Análise de Crises")
    negative_comments = filtered_df[filtered_df['sentimento'] == 'negativo']
    st.write(f"Número de comentários negativos: {len(negative_comments)}")
    if len(negative_comments) > 40:
        st.error("Atenção: Possível crise detectada! Alto volume de comentários negativos.")
    else:
        st.success("Situação estável.")

    # Nuvem de palavras dos negativos
    st.subheader("Nuvem de Palavras dos Comentários Negativos")
    if not negative_comments.empty:
        all_negative_comments = " ".join(negative_comments['comentário'].dropna())
        nltk_stopwords = set(stopwords.words('portuguese'))
        additional_stopwords = {"q", "pra", "deu", "vai", "slk", "é", "isso", "tão", "tipo", "aqui"}
        all_stopwords = nltk_stopwords.union(additional_stopwords)

        words = re.findall(r'\b\w+\b', all_negative_comments.lower())
        filtered_words = [word for word in words if word not in all_stopwords]

        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='Reds',
            max_words=10
        ).generate(" ".join(filtered_words))

        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        st.pyplot(plt)
        plt.close()
    else:
        st.write("Não há comentários negativos para exibir a nuvem de palavras.")

# ===== Aba E-Cris =====
with tab2:
    st.markdown("<h2 style='color: white; font-size: 24px; font-weight: bold;'>E-Cris: Assistente Virtual</h2>", unsafe_allow_html=True)
    st.write("""
    Bem-vindo à E-Cris, sua assistente virtual para monitoramento e gerenciamento de crises. 
    Utilize esta seção para interagir com E-Cris e receber conselhos sobre melhores práticas de gerenciamento de crises.
    """)

    prompt = st.text_area("Digite sua pergunta para E-Cris:", placeholder="Como lidar com uma crise de imagem?")
    enviar = st.button("Enviar")

    if enviar:
        q = (prompt or "").strip()
        if not q:
            st.warning("Digite uma pergunta antes de enviar.")
        else:
            resposta_texto = answer_with_fallback(q)
            st.markdown(resposta_texto)
