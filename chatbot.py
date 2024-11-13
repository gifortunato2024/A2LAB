import streamlit as st 
import pandas as pd
import altair as alt
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
import re

# Baixar stopwords se necessário
nltk.download('stopwords')

# Sidebar
with st.sidebar:
    st.sidebar.image("Coca-Cola_logo.svg", width=200) 
    st.subheader("Sobre o aplicativo")
    st.write("""
    O site oferece gráficos e tabelas que avaliam as opiniões no Tiktok sobre cada subsidiária da Coca-Cola Company, classificando-as como neutras, positivas ou negativas. Na aba Home, onde está disponível a visão geral da holding, você encontra todos os gráficos de forma condensada, proporcionando um panorama geral. 

    Com um sistema de monitoramento de crises que avalia a gravidade das situações enfrentadas por cada subempresa, você pode contar com a nossa assistente virtual E-Cris para uma gestão mais eficiente, que orienta sobre os tipos de crises e fornece informações sobre as melhores práticas de gerenciamento. 
    """)

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
    sentiment_counts = filtered_df['sentimento'].value_counts()

    # Criar gráfico de barras para exibir a contagem de sentimentos
    st.subheader("Distribuição de Sentimentos")
    st.bar_chart(sentiment_counts)

    # Criar gráfico de setores para exibir a proporção de sentimentos
    st.subheader("Proporção de Sentimentos")
    st.write(alt.Chart(filtered_df).mark_arc().encode(
        theta=alt.Theta(field='sentimento', type='nominal', aggregate='count'),
        color=alt.Color(field='sentimento', type='nominal'),
        tooltip=['sentimento', 'count()']
    ))

    # Monitoramento de crise
    st.subheader("Análise de Crises")
    negative_comments = filtered_df[filtered_df['sentimento'] == 'negativo']
    st.write(f"Número de comentários negativos: {len(negative_comments)}")

    if len(negative_comments) > 50:
        st.error("Atenção: Possível crise detectada! Alto volume de comentários negativos.")
    else:
        st.success("Situação estável.")

    # Nuvem de palavras para comentários negativos com remoção de stopwords do NLTK e exibição das 10 palavras mais comuns
    st.subheader("Nuvem de Palavras dos Comentários Negativos")
    if not negative_comments.empty:
        all_negative_comments = " ".join(negative_comments['comentário'].dropna())
        nltk_stopwords = set(stopwords.words('portuguese'))

        # Limpeza do texto e remoção de stopwords
        words = re.sub(r'[^\w\s]', '', all_negative_comments).lower().split()
        filtered_words = [word for word in words if word not in nltk_stopwords]

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

# Aba E-Cris
with tab2:
    st.markdown("<h2 style='color: #000000; font-size: 24px; font-weight: bold;'>E-Cris: Assistente Virtual</h2>", unsafe_allow_html=True)
    st.write("""
    Bem-vindo à E-Cris, sua assistente virtual para monitoramento e gerenciamento de crises. 
    Utilize esta seção para interagir com E-Cris e receber conselhos sobre melhores práticas de gerenciamento de crises.
    """)
    # Simular a presença de um chatbot (esta parte pode ser expandida com uma integração de chatbot real)
    st.text_area("Digite sua pergunta para E-Cris:", placeholder="Como lidar com uma crise de imagem?")
    st.button("Enviar")
