import streamlit as st 
import pandas as pd
import numpy as np
import altair as alt

#sidebar
with st.sidebar:
    st.sidebar.image("Coca-Cola_logo.svg", width=200) 
    st.subheader("Sobre o nosso site")
    st.write("""
O site oferece gráficos e tabelas que avaliam as opiniões nas redes sociais sobre cada subsidiária da Coca-Cola Company, classificando-as como neutras, positivas ou negativas. Na aba Home, onde está disponível a visão geral da holding, você encontra todos os gráficos de forma condensada, proporcionando um panorama geral. 

Ao selecionar uma subsidiária específica, os usuários podem explorar análises de sentimento mais detalhadas por meio de gráficos interativos, tabelas classificatórias e um sistema de monitoramento de crises que avalia a gravidade das situações enfrentadas por cada subempresa.

Para uma gestão mais eficiente, contamos com um chatbot chamado E-Cris, nossa assistente virtual, que orienta sobre os tipos de crises e fornece informações sobre as melhores práticas de gerenciamento. 
""")

#Titulo
st.markdown("<h1 style='color: red;'>The Coca-Cola Company</h1>", unsafe_allow_html=True)
#subtitulo
st.markdown("<h2 style='color: #000000; font-size: 24px; font-weight: bold;'>Escolha uma das subsidiárias para monitorar:</h2>", unsafe_allow_html=True)
#box para selecionar a subsidiária
option = st.selectbox(
    "Qual subsidiária você quer monitorar?",
    ("Todas", "Fanta", "Coca-Cola", "Del-Valle", "Schweppes"),
)

st.write("Você escolheu:", option)

chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])

st.bar_chart(chart_data)



