import streamlit as st 
import pandas as pd
import altair as alt

# Sidebar
with st.sidebar:
    st.sidebar.image("Coca-Cola_logo.svg", width=200) 
    st.subheader("Sobre o nosso site")
    st.write("""
    O site oferece gráficos e tabelas que avaliam as opiniões nas redes sociais sobre cada subsidiária da Coca-Cola Company, classificando-as como neutras, positivas ou negativas. Na aba Home, onde está disponível a visão geral da holding, você encontra todos os gráficos de forma condensada, proporcionando um panorama geral. 

    Ao selecionar uma subsidiária específica, os usuários podem explorar análises de sentimento mais detalhadas por meio de gráficos interativos, tabelas classificatórias e um sistema de monitoramento de crises que avalia a gravidade das situações enfrentadas por cada subempresa.

    Para uma gestão mais eficiente, contamos com um chatbot chamado E-Cris, nossa assistente virtual, que orienta sobre os tipos de crises e fornece informações sobre as melhores práticas de gerenciamento. 
    """)

# Título
st.markdown("<h1 style='color: red;'>The Coca-Cola Company</h1>", unsafe_allow_html=True)
# Subtítulo
st.markdown("<h2 style='color: #000000; font-size: 24px; font-weight: bold;'>Escolha uma das subsidiárias para monitorar:</h2>", unsafe_allow_html=True)

# Box para selecionar a subsidiária
option = st.selectbox(
    "Qual subsidiária você quer monitorar?",
    ("Todas", "Fanta", "Coca-Cola", "Del Valle", "Schweppes"),
)

# Carregar dados de comentários
combined_df = pd.read_csv('/mnt/data/combined_comments.csv')  # Substitua pelo caminho correto se necessário

# Filtrar dados pela opção selecionada
if option != "Todas":
    filtered_df = combined_df[combined_df['subsidiary'] == option]
else:
    filtered_df = combined_df

# Exibir amostra dos dados carregados
st.write("Amostra dos dados:")
st.dataframe(filtered_df.head())

# Contagem dos sentimentos
sentiment_counts = filtered_df['sentiment'].value_counts()

# Criar gráfico de barras para exibir a contagem de sentimentos
st.subheader("Distribuição de Sentimentos")
st.bar_chart(sentiment_counts)

# Criar gráfico de setores para exibir a proporção de sentimentos
st.subheader("Proporção de Sentimentos")
st.write(alt.Chart(filtered_df).mark_arc().encode(
    theta=alt.Theta(field='sentiment', type='nominal', aggregate='count'),
    color=alt.Color(field='sentiment', type='nominal'),
    tooltip=['sentiment', 'count()']
))

# Monitoramento de crise
st.subheader("Análise de Crises")
negative_comments = filtered_df[filtered_df['sentiment'] == 'negativo']
st.write(f"Número de comentários negativos: {len(negative_comments)}")

if len(negative_comments) > 50:
    st.error("Atenção: Possível crise detectada! Alto volume de comentários negativos.")
else:
    st.success("Situação estável.")

