
import streamlit as st 
import pandas as pd
import altair as alt
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
import re
import PyPDF2
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

# Baixar stopwords se necessário
nltk.download('stopwords')

# Configuração do chatbot

# Variáveis do ambiente
with open('chave_groq', 'r') as arquivo:
    chave_groq = arquivo.read()
groq_model = 'llama-3.2-90b-vision-preview'
modelo_embeddings = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
Settings.llm = Groq(api_key=chave_groq, model=groq_model, temperature=0)
Settings.embed_model = HuggingFaceEmbedding(model_name=modelo_embeddings)
Settings.chunk_size = 2048
Settings.chunk_overlap = 512

# Especificar diretamente os arquivos PDF
pdf_files = [
    'Material Gestão de Crise Trabalho Matheus.pdf',
    'crise-pdf.pdf',
    'crise_2_pdf.pdf',
    'crise_3_pdf.pdf'
]

# Função para ler conteúdo de PDFs
def read_pdf(file_path):
    pdf_text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            pdf_text += page.extract_text() + "\n"
    return pdf_text

# Carregar todos os documentos dos arquivos especificados
documents = []
for file_path in pdf_files:
    if os.path.exists(file_path):
        content = read_pdf(file_path)
        documents.append({"text": content})
    else:
        st.warning(f"Arquivo {file_path} não encontrado.")

# Criação do índice
vector_store = DuckDBVectorStore('rag.duckdb', persist_dir='rag')
storage_context = StorageContext.from_defaults(vector_store=vector_store)
vector_index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

# Criação do recuperador
retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=5)
response_synthesizer = get_response_synthesizer()
query_engine = RetrieverQueryEngine.from_args(
    retriever=retriever, 
    response_synthesizer=response_synthesizer,
    response_mode='tree_sumarize',
    node_postprocessors=[SimilarityPostprocessor(similarity_threshold=0.3)]
)

# Sidebar
with st.sidebar:
    st.sidebar.image("Coca-Cola_logo.svg", width=200) 
    st.subheader("Sobre o aplicativo")
    
    # Justificar o novo texto usando HTML e CSS embutido
    st.markdown("""
    <div style="text-align: justify;">
        O aplicativo apresenta gráficos e tabelas que avaliam as opiniões no TikTok sobre cada subsidiária da Coca-Cola Company, classificando-as como neutras, positivas ou negativas. Na aba "Monitoramento", é possível acessar uma visão geral da holding com todos os gráficos de forma condensada, oferecendo um panorama completo. O sistema de monitoramento de crises avalia a gravidade das situações enfrentadas por cada subempresa, e com o auxílio da assistente virtual E-Cris, é possível garantir uma gestão mais eficiente, fornecendo orientações sobre tipos de crises e as melhores práticas de gerenciamento.
    </div>
    """, unsafe_allow_html=True)

# Título
st.markdown("<h1 style='color: red;'>The Coca-Cola Company</h1>", unsafe_allow_html=True)

# Criar abas no aplicativo
tab1, tab2 = st.tabs(["Monitoramento", "E-Cris"])

# Aba de monitoramento
with tab1:
    st.markdown("<h2 style='color: #000000; font-size: 24px; font-weight: bold;'>Escolha uma das subsidiárias para monitorar:</h2>", unsafe_allow_html=True)

    # Box para selecionar a subsidiária
    option = st.selectbox(
        "Qual subsidiária você quer monitorar?",
        ("Fanta", "Coca-Cola", "Del Valle", "Schweppes")
    )

    # Carregar dados de comentários
    combined_df = pd.read_csv('Comentários combinados - combined_comments (1).csv')  # Substitua pelo caminho correto se necessário

    # Filtrar dados pela opção selecionada
    filtered_df = combined_df[combined_df['subsidiária'] == option]

    # Exibir amostra dos dados carregados
    st.write("Amostra dos dados:")
    st.dataframe(filtered_df)

    # Contagem dos sentimentos
    sentiment_counts = filtered_df['sentimento'].value_counts().reset_index()
    sentiment_counts.columns = ['sentimento', 'count']

    # Definir cores personalizadas
    color_scale = alt.Scale(domain=['positivo', 'neutro', 'negativo'],
                            range=['#1f77b4', '#aec7e8', '#d62728'])  # Azul escuro, azul claro e vermelho

    # Dividir em duas colunas para os gráficos
    col1, col2 = st.columns(2)

    with col1:
        bar_chart = alt.Chart(sentiment_counts).mark_bar().encode(
            x=alt.X('sentimento:N', sort='-y', title='Sentimento'),
            y=alt.Y('count:Q', title='Contagem'),
            color=alt.Color('sentimento:N', scale=color_scale, legend=None),
            tooltip=['sentimento', 'count']
        ).properties(
            width=400,  # Aumentar a largura do gráfico
            height=400  # Aumentar a altura do gráfico
        )
        st.altair_chart(bar_chart)

    with col2:
        pie_chart = alt.Chart(sentiment_counts).mark_arc().encode(
            theta=alt.Theta(field='count', type='quantitative'),
            color=alt.Color('sentimento:N', scale=color_scale),
            tooltip=['sentimento', 'count']
        ).properties(
            width=400,  # Aumentar a largura do gráfico
            height=400  # Aumentar a altura do gráfico
        )
        st.altair_chart(pie_chart)

    # Monitoramento de crise
    st.subheader("Análise de Crises")
    negative_comments = filtered_df[filtered_df['sentimento'] == 'negativo']
    st.write(f"Número de comentários negativos: {len(negative_comments)}")

    if len(negative_comments) > 40:
        st.error("Atenção: Possível crise detectada! Alto volume de comentários negativos.")
    else:
        st.success("Situação estável.")

    # Nuvem de palavras para comentários negativos com remoção de stopwords do NLTK e exibição das 10 palavras mais comuns
    st.subheader("Nuvem de Palavras dos Comentários Negativos")
    if not negative_comments.empty:
        all_negative_comments = " ".join(negative_comments['comentário'].dropna())
        nltk_stopwords = set(stopwords.words('portuguese'))

        # Adicionar *stopwords* extras
        additional_stopwords = {"q", "pra", "deu", "vai", "slk", "é", "isso", "tão", "tipo", "aqui"}
        all_stopwords = nltk_stopwords.union(additional_stopwords)

        # Limpeza do texto e remoção de stopwords
        words = re.findall(r'\b\w+\b', all_negative_comments.lower())  # Separar apenas palavras
        filtered_words = [word for word in words if word not in all_stopwords]

        # Criar a nuvem de palavras
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
    else:
        st.write("Não há comentários negativos para exibir a nuvem de palavras.")

# Aba E-Cris (Chatbot)
with tab2:
    st.markdown("<h2 style='color: #000000; font-size: 24px; font-weight: bold;'>E-Cris: Assistente Virtual</h2>", unsafe_allow_html=True)
    st.write("""
    Bem-vindo à E-Cris, sua assistente virtual para monitoramento e gerenciamento de crises. 
    Utilize esta seção para interagir com E-Cris e receber conselhos sobre melhores práticas de gerenciamento de crises.
    """)

    user_question = st.text_area("Digite sua pergunta para E-Cris:", placeholder="Como lidar com uma crise de imagem?")
    if st.button("Enviar"):
        if user_question.strip():
            response = query_engine.query(user_question)
            st.write("**E-Cris:**", response)
        else:
            st.write("Por favor, digite uma pergunta.")
