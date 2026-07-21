#Imports
import pandas as pd 
import numpy as np

# 1. CARREGAMENTO DOS DADOS

# Carregar o CSV (atenção: encoding? separador?)
produtos=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/produtos.csv')
resumo_mensal=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/resumo_mensal.csv')
sazonalidade_top=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/sazonalidade_top15.csv')
venda_diarias=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/vendas_diarias_2021_2025.csv')
venda_mensais=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/vendas_mensais_2021_2025.csv')
venda_semanais=pd.read_csv('/Users/mayararosa/Documents/Dataset pedido de encomenda/smartshelf/vendas_semanais_2021_2025.csv')

# 2. INSPEÇÃO EXPLORATÓRIA (executada durante o desenvolvimento)

#Dicionario
todos = {
    "produtos": produtos,
    "resumo_mensal": resumo_mensal,
    "sazonalidade_top": sazonalidade_top,
    "venda_diarias": venda_diarias,
    "venda_mensais": venda_mensais,
    "venda_semanais": venda_semanais,
}

# Criando um loop para facilitar e ira ficar como comentario, ja que o codigo esta pronto e foi utilizado para verificar
#for nome, df in todos.items():
    #print(f"===== {nome} =====")
    #As 5 primeiras linhas
    #print(df.head())
    #Verificando as informacoes de cada um
    #df.info()
    #A descricao de cada um 
    #print(df.describe())
    #Listar quantos valores unicos possui
    #print(df.nunique())
    #Verificar se ha valores duplicados
    #print(df.duplicated().sum())

# 3. LIMPEZA E PREPARAÇÃO (venda_diarias = fonte de verdade)

# Ver intervalo de datas (mínimo e máximo fazem sentido?)
data_minima = venda_diarias['data'].min()
data_maxima = venda_diarias['data'].max() 
print(f"intervalo de datas: {data_minima} ate {data_maxima}")

# Converter 'data' de texto para datetime (errors='coerce' -> datas
# inválidas viram NaT em vez de rebentar)
venda_diarias['data'] = pd.to_datetime(venda_diarias['data'], format='%Y-%m-%d', errors='coerce')
print("Verificar se ha NaT no codigo")
print(venda_diarias['data'].isna().sum())

# Extrair ano e mês da data (só possível porque 'data' já é datetime)
venda_diarias['ano'] = venda_diarias['data'].dt.year
venda_diarias['mes'] = venda_diarias['data'].dt.month

# 4. AGREGAÇÃO MENSAL + VALIDAÇÃO CONTRA GABARITO

# Somar unidades vendidas por produto x ano x mês
agregacao = venda_diarias.groupby(["product_id", "ano", "mes"])["unidades"].sum().reset_index()
print ("Shape da agregacao do codigo", agregacao.shape)

# Validar: comparar a minha agregação com o gabarito pronto (venda_mensais)
validacao = pd.merge(agregacao, venda_mensais, on=['product_id', 'ano', 'mes'])

# Diferença entre a minha soma (unidades_x) e o gabarito (unidades_y)
validacao['diferenca'] = validacao['unidades_x'] - validacao['unidades_y']

# Contar linhas divergentes: se 0, a agregação está correta
divergencias = (validacao['diferenca'] != 0).sum()
print(f"Linhas divergentes: {divergencias}")

# 5. GRELHA COMPLETA (preencher meses sem vendas com 0)

# Valores únicos de cada dimensão
produtos_unicos = agregacao["product_id"].unique()
anos_unicos = agregacao["ano"].unique()
meses_unicos = agregacao["mes"].unique()

# Transformar cada lista em mini-tabela para o cruzamento
df_produtos = pd.DataFrame({"product_id": produtos_unicos})
df_anos = pd.DataFrame({"ano": anos_unicos})
df_meses = pd.DataFrame({"mes": meses_unicos})

# Grelha = produto cartesiano (todas as combinações possíveis)
grelha = df_produtos.merge(df_anos, how="cross").merge(df_meses, how="cross")
print(grelha.shape)  

# Encaixar a agregação na grelha (how='left' mantém TODAS as linhas da grelha)
resultado = grelha.merge(agregacao, on=["product_id", "ano", "mes"], how="left")

# Meses sem vendas vieram como NaN e preencher com 0
resultado["unidades"] = resultado["unidades"].fillna(0)
print("Buracos preenchidos (NaN restantes, deve ser 0):", resultado["unidades"].isna().sum())


# 6. PREVISÃO POR MÉDIA PONDERADA (5 anos)

# Pivô: uma linha por produto x mês, uma coluna por ano
tabela_pivot = resultado.pivot_table(
    index=["product_id", "mes"],   
    columns="ano",          
    values="unidades"      
)

# Previsão = soma de cada ano x o seu peso
tabela_pivot["previsao"] = (
    tabela_pivot[2025] * 0.35
    + tabela_pivot[2024] * 0.25
    + tabela_pivot [2023] * 0.18
    + tabela_pivot [2022] * 0.12
    + tabela_pivot [2021] * 0.10
)

# 7. BACKTEST — validar a qualidade da previsão (MAE e MAPE)

# Prever 2025 usando SÓ 2021-2024 (pesos renormalizados para somar 1)
tabela_pivot["previsao_2025"] = (
    tabela_pivot[2024] * 0.389  
    + tabela_pivot[2023] * 0.277
    + tabela_pivot[2022] * 0.2
    + tabela_pivot[2021] * 0.133
)

# Erro absoluto de cada linha: |previsto - real|
tabela_pivot["erro"] = (tabela_pivot["previsao_2025"] - tabela_pivot[2025]).abs()

# MAE — erro médio em unidades
mae = tabela_pivot["erro"].mean()
print(f"MAE (erro médio absoluto): {mae}")

# MAPE — erro médio em %. Excluir linhas com real=0 (não se divide por zero)
com_vendas = tabela_pivot[tabela_pivot[2025] != 0]
total = len(tabela_pivot)
usadas = len(com_vendas)
print(f"MAPE calculado sobre {usadas} linhas; {total - usadas} excluídas (vendas zero)")

mape = (com_vendas["erro"] / com_vendas[2025]).mean() * 100
print(f"MAPE (erro percentual médio): {mape:.1f}%")

# 8. FÓRMULA DA ENCOMENDA

# Tabela limpa: só produto, mês e previsão
tabela_solta = tabela_pivot.reset_index()
previsoes_produtos = tabela_solta[["product_id", "mes", "previsao"]]

# Stock FICTÍCIO para testar a fórmula; virá da contagem real (manual/foto) depois
previsoes_produtos["stock"] = np.random.randint(0, 60, size=len(previsoes_produtos))

# Aplicar a fórmula (previsão + 15% de margem de segurança, menos o stock)
previsoes_produtos["encomenda"] = previsoes_produtos["previsao"] * 1.15 - previsoes_produtos["stock"]

# Encomenda nunca é negativa (se há stock de sobra, não se encomenda)
previsoes_produtos["encomenda"] = previsoes_produtos["encomenda"].clip(lower=0)

# 9. CONVERTER EM CAIXAS

# Trazer o tamanho da caixa de cada produto
previsoes_produtos = previsoes_produtos.merge(
    produtos[["product_id", "unidades_por_caixa"]],
    on="product_id",
    how="left"
)

# Nº de caixas = encomenda / tamanho da caixa, arredondado para cima
previsoes_produtos["caixas_a_pedir"] = np.ceil(
    previsoes_produtos["encomenda"] / previsoes_produtos["unidades_por_caixa"]
)

# Unidades reais que essas caixas trazem
previsoes_produtos["unidades_totais"] = previsoes_produtos["caixas_a_pedir"] * previsoes_produtos["unidades_por_caixa"]

# Trazer o nome do produto (para a lista legível)
previsoes_produtos = previsoes_produtos.merge(
    produtos[["product_id", "nome"]],
    on="product_id",
    how="left"
)

# 10. LISTA FINAL DE ENCOMENDA

# Só os produtos que precisam de encomenda (caixas > 0)
encomenda_final = previsoes_produtos[previsoes_produtos["caixas_a_pedir"] > 0]

for indice, linha in encomenda_final.iterrows():
   print(f"{linha['nome']} (mês {linha['mes']}): pedir {linha['caixas_a_pedir']} caixa(s) = {linha['unidades_totais']} unidades")