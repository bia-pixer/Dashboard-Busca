import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def plot_transactions_summary(total_transfer, num_transfers):
    """
    Cria gráfico combinado de barras (transações/dia) e linha (valor total transferido)
    
    Parâmetros:
    total_transfer (pd.Series): Série temporal com valores totais transferidos por data
    num_transfers (pd.Series): Série temporal com número de transações por data
    """
    # Cria figura com eixo Y secundário
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Adiciona gráfico de barras (transações)
    fig.add_trace(
        go.Bar(
            x=num_transfers.index,
            y=num_transfers.values,
            name="Transações/dia",
            marker_color='#1f77b4'
        ),
        secondary_y=False
    )
    
    # Adiciona gráfico de linhas (valor transferido)
    fig.add_trace(
        go.Scatter(
            x=total_transfer.index,
            y=total_transfer.values,
            name="Valor total",
            line=dict(color='#ff7f0e', width=2.5)
        ),
        secondary_y=True
    )
    
    # Configura layout
    fig.update_layout(
        title='Atividade na Blockchain por Data',
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor='rgba(240,240,240,0.9)'
    )
    
    # Configura eixos
    fig.update_xaxes(title_text="Data")
    fig.update_yaxes(
        title_text="<b>Número de Transações</b>",
        secondary_y=False,
        showgrid=False
    )
    fig.update_yaxes(
        title_text="<b>Valor Total Transferido</b>",
        secondary_y=True,
        showgrid=False,
        tickprefix="Ξ " if 'Etherscan' in str(total_transfer) else "$ "  # Adapta símbolo
    )
    
    return fig

def plot_top_holders(token_dist, top_n=10, title='Distribuição de Tokens'):
    """
    Plota um gráfico de rosca com os maiores holders
    
    Parâmetros:
    token_dist (pd.Series): Série com endereços como índice e saldos como valores
    top_n (int): Quantidade de principais holders a exibir
    title (str): Título do gráfico
    """
    # Verifica se há dados
    if token_dist is None:
        raise ValueError("Dados de distribuição não disponíveis na API")
    
    # Processa os dados
    sorted_holders = token_dist.sort_values(ascending=False)
    top_holders = sorted_holders.head(top_n)
    others = sorted_holders.iloc[top_n:].sum()
    
    # Cria DataFrame final
    df = pd.concat([top_holders, pd.Series(others, index=['Outros'])])
    df = df.reset_index()
    df.columns = ['Endereço', 'Saldo']

    # Cria o gráfico
    fig = px.pie(
        df,
        names='Endereço',
        values='Saldo',
        hole=0.6,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Personaliza layout
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Saldo: %{value:.2f}"
    )
    
    fig.update_layout(
        uniformtext_minsize=12,
        uniformtext_mode='hide',
        showlegend=False,
        annotations=[dict(
            text=f'Top {top_n}',
            x=0.5,
            y=0.5,
            font_size=20,
            showarrow=False
        )]
    )
    
    return fig
