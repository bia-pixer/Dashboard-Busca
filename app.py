
import streamlit as st
from modules import noticias_google, tendencia_google

st.set_page_config(layout='wide', 
                   page_title='Busca de Ativos Virtuais',
                   page_icon=':grey_question:')

st.title('Busca de Ativos Virtuais')

# Configuração da barra lateral ------------------------------------------------
st.sidebar.markdown("## Menu Lateral Bla bla bla")

# Seção de Busca ---------------------------------------------------------------
column1, column2 = st.columns(2)

termo = column1.text_input("Digite um termo para pesquisa:")
token_adress = column2.text_input("Digite o endereço do token para a busca no block explorer:")

if termo:
    st.write(f"Você pesquisou pelo termo: {termo}")

# Notícias ---------------------------------------------------------------------
st.subheader('Principais Notícias', divider='gray')

news_df = noticias_google(termo)

st.dataframe(data=news_df, 
             use_container_width=True, 
             hide_index=True,
             column_order=('Fonte', 'Manchete', 'Data', 'Descrição', 'Link'))

# dados_interesse, dados_regiao, relacionados = tendencia_google('eike token')