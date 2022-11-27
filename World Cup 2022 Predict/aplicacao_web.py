import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

# Titulo da página
st.title('PREVISÃO DAS PARTIDAS DA COPA')

# Algoritmo
df_selecao = pd.read_excel('DadosCopaDoMundoQatar2022.xlsx', sheet_name = 'selecoes',index_col='Seleção')
df_jogos  = pd.read_excel('DadosCopaDoMundoQatar2022.xlsx', sheet_name='jogos')

f = df_selecao["PontosRankingFIFA"]

a, b = min(f), max(f) 
fa, fb = 0.15, 1 
b1 = (fb - fa)/(b-a) 
b0 = fb - b*b1
forca = b0 + b1*f

def media_equipes(selecao1, selecao2):
    forca_casa = forca[f'{selecao1}']
    forca_fora = forca[f'{selecao2}']
    expectativa_de_gols = 2.72
    lambda_casa = expectativa_de_gols*forca_casa/(forca_casa + forca_fora)
    lambda_fora = expectativa_de_gols*forca_fora/(forca_fora + forca_fora)
    return [lambda_casa, lambda_fora]

def distribuicao(media):
    probs = []
    for i in range(7):
        probs.append(poisson.pmf(i,media))
    probs.append(1-sum(probs))
    return pd.Series(probs, index = ['0', '1', '2', '3', '4', '5', '6', '7+'])

def qtd_gols(casa,fora):
    lambda_casa, lambda_fora = media_equipes(selecao1=casa,selecao2=fora)
    gols_casa = np.random.poisson(lam=lambda_casa,size=1)
    gols_fora = np.random.poisson(lam=lambda_fora,size=1)
    saldo_time_casa = gols_casa - gols_fora
    saldo_time_fora = -saldo_time_casa
    placar = f'{saldo_time_casa}x{saldo_time_fora}'
    return [gols_casa, gols_fora, saldo_time_casa, saldo_time_fora, palcar]


def probabilidade(selecao1,selecao2):
    lambda_casa, lambda_fora = media_equipes(selecao1=selecao1, selecao2=selecao2)
    dist1, dist2 = distribuicao(media = lambda_casa), distribuicao(media= lambda_fora)
    matriz = np.outer(dist1, dist2)
    vitoria = np.tril(matriz).sum()-np.trace(matriz)    #Soma a triangulo inferior
    derrota = np.triu(matriz).sum()-np.trace(matriz)    #Soma a triangulo superior
    empate = 1 - (vitoria + derrota)
    probs = np.around([vitoria, empate , derrota], 3)
    
    probsp = [f'{100*i:.1f}%' for i in probs]

    nomes = ['0', '1', '2', '3', '4', '5', '6', '7+']
    matriz = pd.DataFrame(matriz, columns = nomes, index = nomes)
    matriz.index = pd.MultiIndex.from_product([[selecao1], matriz.index])
    matriz.columns = pd.MultiIndex.from_product([[selecao2], matriz.columns]) 

    output = {'seleção1': selecao1, 'seleção2': selecao2, 
             'f1': forca[selecao1], 'f2': forca[selecao2], 
             'media1': lambda_casa, 'media2': lambda_fora, 
             'probabilidades': probsp, 'matriz': matriz}
    
    return output

df_jogos['Vitoria'] = None
df_jogos['Empate'] = None
df_jogos['Derrota'] = None

for i in range(len(df_jogos)):
    s1 = df_jogos['seleção1'][i]
    s2 = df_jogos['seleção2'][i]
    v,e,d = probabilidade(selecao1=s1, selecao2=s2)['probabilidades']
    df_jogos.at[i,'Vitoria'] = v
    df_jogos.at[i,'Empate'] = e
    df_jogos.at[i,'Derrota'] = d

# Interface
st.markdown("# Copa do Mundo Qatar 2022") 

st.markdown("## Probabilidades das Partidas")
st.markdown('---')

listaselecoes1 = df_selecao.index.tolist()  
listaselecoes1.sort()
listaselecoes2 = listaselecoes1.copy()

j1, j2 = st.columns(2)
selecao1 = j1.selectbox('Escolha a primeira Seleção', listaselecoes1) 
listaselecoes2.remove(selecao1)
selecao2 = j2.selectbox('Escolha a segunda Seleção', listaselecoes2, index = 1)
st.markdown('---')

jogo = probabilidade(selecao1, selecao2)
prob = jogo['probabilidades']
matriz = jogo['matriz']

col1, col2, col3, col4, col5 = st.columns(5)
col1.image(df_selecao.loc[selecao1, 'LinkBandeiraGrande'])  
col2.metric(selecao1, prob[0])
col3.metric('Empate', prob[1])
col4.metric(selecao2, prob[2]) 
col5.image(df_selecao.loc[selecao2, 'LinkBandeiraGrande'])

st.markdown('---')
st.markdown("## 📊 Probabilidades dos Placares") 

def aux(x):
	return f'{str(round(100*x,1))}%'
st.table(matriz.applymap(aux))