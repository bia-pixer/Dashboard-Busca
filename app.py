
import streamlit as st
import modules as m

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

if termo:
    news_df = m.noticias_google(termo)
    news_df = m.df_to_html_table(news_df)
    st.markdown(news_df, unsafe_allow_html=True)

# Google Trends ----------------------------------------------------------------
st.subheader('Tendências de Busca', divider='gray')

# if termo:
    # dados_interesse, dados_regiao, relacionados = m.tendencia_google(termo)

