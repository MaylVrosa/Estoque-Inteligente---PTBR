#Imports
import pandas as pd 
import numpy as np

#Inspeção do dataset
# Carregar o CSV (atenção: encoding? separador?)
produtos=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/produtos.csv')
resumo_mensal=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/resumo_mensal.csv')
sazonalidade_top=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/sazonalidade_top15.csv')
venda_diarias=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/vendas_diarias_2021_2025.csv')
venda_mensais=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/vendas_mensais_2021_2025.csv')
venda_semanais=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/vendas_semanais_2021_2025.csv')

#Dicionario
todos = {
    "produtos": produtos,
    "resumo_mensal": resumo_mensal,
    "sazonalidade_top": sazonalidade_top,
    "venda_diarias": venda_diarias,
    "venda_mensais": venda_mensais,
    "venda_semanais": venda_semanais,
}

# Criando um loop para facilitar
for nome, df in todos.items():
    print(f"===== {nome} =====")
    #As 5 primeiras linhas
    print(df.head())
    #Verificando as informacoes de cada um
    df.info()
    #A descricao de cada um 
    print(df.describe())
    #Listar quantos valores unicos possui
    print(df.nunique())
    #Verificar se ha valores duplicados
    print(df.duplicated().sum())

# Ver intervalo de datas (mínimo e máximo fazem sentido?)
data_minima = venda_diarias['data'].min()
data_maxima = venda_diarias['data'].max() 
print(f"intervalo de datas: {data_minima} ate {data_maxima}")

# Converter em datas
venda_diarias['data'] = pd.to_datetime(venda_diarias['data'], format='%Y-%m-%d', errors='coerce')

#Verificar as informacoes
venda_diarias.info()

# contagem de NaT - o teu lembrete, já em código
print("Verificar se ha NaT no codigo")
print(venda_diarias['data'].isna().sum())

#Criar ano e mes em venda_diarias
venda_diarias['ano'] = venda_diarias['data'].dt.year
venda_diarias['mes'] = venda_diarias['data'].dt.month

#Verificar as primeiras linhas
print("Verificar as primeiras linhas apos a alteracao")
print(venda_diarias.head())

#Agrupar por produto + ano + mes e somar unidades e usar o reset para facilitar a visualizacao
agregacao = venda_diarias.groupby(["product_id", "ano", "mes"])["unidades"].sum().reset_index()

#Verificar as primeiras linhas e o shape
print ("Shape da agregacao do codigo")
print(agregacao.shape)
print("Verificar as primeiras linhas apos a alteracao")
print(agregacao.head())

#Juntar as duas tabelas para ver se esta certo
validacao = pd.merge(agregacao, venda_mensais, on=['product_id', 'ano', 'mes'])
print("Verificar as primeiras linhas apos a alteracao")
print(validacao.head())
print ("Shape da validacao do codigo")
print(validacao.shape)

# Criando a coluna da esquerda
validacao['diferenca'] = validacao['unidades_x'] - validacao['unidades_y']

# Conta as divergências onde a diferença é diferente de zero
divergencias = (validacao['diferenca'] != 0).sum()
print(f"Linhas divergentes: {divergencias}")

# Verificacao dos produtos unicos
produtos_unicos = agregacao["product_id"].unique()
anos_unicos = agregacao["ano"].unique()
meses_unicos = agregacao["mes"].unique()

# Transformando o array em mini tabelas
df_produtos = pd.DataFrame({"product_id": produtos_unicos})
df_anos = pd.DataFrame({"ano": anos_unicos})
df_meses = pd.DataFrame({"mes": meses_unicos})

#Construir a grelha
grelha = df_produtos.merge(df_anos, how="cross").merge(df_meses, how="cross")
#print do shape da grelha
print(grelha.shape)  

#print das combinacoes unicas
print(f"combinacoes unicas {produtos_unicos}, {anos_unicos}, {meses_unicos}")
print(len(produtos_unicos), len(anos_unicos), len(meses_unicos))

# Vamos juntar as duas tabelas da grelha e da agregacao
resultado = grelha.merge(agregacao, on=["product_id", "ano", "mes"], how="left")

#Preencher os vazios com 0
resultado["unidades"] = resultado["unidades"].fillna(0)

# Print shape
print(resultado.shape)
print(resultado["unidades"].isna().sum())

print(resultado[(resultado["product_id"]==1000) & (resultado["ano"]==2021) & (resultado["mes"]==1)])

#Ajustando a tabela para que seja possivel realizar os pesos das encomendas e faze-la
tabela_pivot = resultado.pivot_table(
    index=["product_id", "mes"],   
    columns="ano",          
    values="unidades"      
)

#Criando a previsao da encomenda
tabela_pivot["previsao"] = (
    tabela_pivot[2025] * 0.35
    + tabela_pivot[2024] * 0.25
    + tabela_pivot [2023] * 0.18
    + tabela_pivot [2022] * 0.12
    + tabela_pivot [2021] * 0.10
)

#Verificar pelo head
print(tabela_pivot.head())

# 'solta' product_id e mes do índice, de volta a colunas normais
previsao_final = tabela_pivot.reset_index()
print(previsao_final.head())

# Fazer o backtest para verificar se funciona o sistema de previsao
tabela_pivot["previsao_2025"] = (
    tabela_pivot[2024] * 0.389  
    + tabela_pivot[2023] * 0.277
    + tabela_pivot[2022] * 0.2
    + tabela_pivot[2021] * 0.133
)

print(tabela_pivot.head())

#Calcular a diferenca do teste e do valor real 
tabela_pivot["erro"] = (tabela_pivot["previsao_2025"] - tabela_pivot[2025]).abs()

# Verificar o MAE - Mean Absolute Error
mae = tabela_pivot["erro"].mean()
print(f"MAE (erro médio absoluto): {mae}")

# manter só as linhas onde houve vendas reais em 2025
com_vendas = tabela_pivot[tabela_pivot[2025] != 0]

# Contar quantas linhas e verificar o MAPE(Mean Absolute Percentage Error)
total = len(tabela_pivot)
usadas = len(com_vendas)
print(f"MAPE calculado sobre {usadas} linhas; {total - usadas} excluídas (vendas zero)")

# erro percentual de cada linha: |previsto - real| / real
mape = (com_vendas["erro"] / com_vendas[2025]).mean() * 100
print(f"MAPE (erro percentual médio): {mape:.1f}%")

# Para soltar product_id e mes do índice
tabela_solta = tabela_pivot.reset_index()

# Escolher só as 3 colunas que interessam
previsoes_produtos = tabela_solta[["product_id", "mes", "previsao"]]

# stock FICTÍCIO para testar a fórmula; virá da contagem real depois
previsoes_produtos["stock"] = np.random.randint(0, 30, size=len(previsoes_produtos))

#Aplicando as previsoes e quanto devera ser a encomenda
previsoes_produtos["encomenda"] = previsoes_produtos["previsao"] * 1.15 - previsoes_produtos["stock"]

#Limitando o zero
previsoes_produtos["encomenda"] = previsoes_produtos["encomenda"].clip(lower=0)

print(previsoes_produtos.head())

#Acrescentar a unidades_por__caixa
previsoes_produtos = previsoes_produtos.merge(
    produtos[["product_id", "unidades_por_caixa"]],
    on="product_id",
    how="left"
)

