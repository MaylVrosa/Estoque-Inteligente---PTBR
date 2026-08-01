# SmartShelf — Sistema Inteligente de Reposição de Stock

> **English version:** [SmartShelf---EN](https://github.com/MaylVrosa/SmartShelf---EN)

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Estado](https://img.shields.io/badge/estado-em%20desenvolvimento-orange)
![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

Sistema de apoio à reposição de stock para uma loja de conservas em Lisboa. O objetivo é responder a uma pergunta prática do dia a dia da loja: **quantas caixas de cada produto encomendar?** - combinando previsão de procura com contagem de stock em prateleira.

O projeto está a ser construído em três fases. Este README distingue de forma explícita **o que já funciona** do **que está planeado**, e é atualizado à medida que cada fase avança.

---

## Estado do projeto

| Fase | Descrição | Estado |
|------|-----------|--------|
| **Fase 1** | Previsão de procura (Python/pandas) + geração de lista de encomenda | **Concluída** |
| **Fase 2** | Contagem de stock por visão computacional (YOLOv8) | **Em curso** |
| **Fase 3** | Interface web com aprovação do gestor e exportação em PDF | **Planeada** |

*Última atualização: agosto de 2026.*

---

## Fase 1 — Previsão de procura 

A primeira fase está construída e validada. Recebe o histórico de vendas da loja e produz uma lista de encomenda por produto, em número de caixas.

**O que faz:**
- Calcula a procura prevista com uma **média ponderada de 5 anos** de vendas históricas.
- Foi validada com **backtesting**, obtendo um **MAPE de aproximadamente 28%** (erro percentual médio absoluto).
- Converte a previsão numa **lista de encomenda em caixas por produto**, pronta a usar.

**Nota sobre o MAPE:** ~28% é o valor atual honesto do modelo nesta fase. É um ponto de partida funcional, não um resultado final, a precisão deverá melhorar com mais dados e refinamento da ponderação.

---

## Fase 2 - Contagem por visão computacional 

Fase atualmente em desenvolvimento. A ideia é eliminar a contagem manual de stock: o gestor fotografa a prateleira e o sistema conta as latas.

**Fluxo previsto:**
1. O gestor fotografa a prateleira.
2. O modelo (YOLOv8) **deteta e conta as latas** por produto.
3. O resultado alimenta a fórmula da Fase 1, fechando o ciclo previsão → contagem → encomenda.

**Estado atual (honesto):**
- **Dataset em anotação** no Roboflow: ~34 fotografias, 4 classes de produtos.
- **Critério de anotação:** apenas objetos **totalmente visíveis** são anotados (latas parcialmente ocultas por outras não contam), para manter a consistência do conjunto.
- **Ambiente de treino:** Google Colab (GPU T4), por incompatibilidade do PyTorch com Mac Intel.
- **O modelo ainda não foi treinado.** Esta secção será atualizada com os resultados (ex.: mAP) assim que o primeiro treino estiver concluído.

---

## Fase 3 - Interface web 

Fase planeada, ainda não iniciada.

**Objetivo:** dar ao gestor uma interface simples onde:
- Reveja a contagem e a lista de encomenda sugerida.
- **Aprove ou ajuste** manualmente antes de confirmar.
- **Exporte a encomenda em PDF** para enviar ao fornecedor.

---

## Decisões de arquitetura

Algumas escolhas técnicas que orientam o projeto:

**Separação entre deteção e estimativa de profundidade.**
O modelo de visão tem uma única responsabilidade: **reconhecer a lata** na imagem. A estimativa de quantas latas existem em profundidade na prateleira (o que a câmara não vê diretamente) é **lógica pós-deteção, fora do modelo**. Isto mantém o modelo simples e a lógica de negócio testável de forma independente.

**Deteções de baixa confiança são marcadas como "duvidosas".**
Quando o modelo não tem confiança suficiente numa deteção, o item é assinalado para **confirmação manual** em vez de ser contado automaticamente. Isto preserva a margem de segurança da fórmula de encomenda — é preferível pedir confirmação a encomendar a menos por um erro de contagem.

**Privacidade dos dados da loja.**
Os dados reais de vendas e as fotografias reais das prateleiras são **mantidos privados**. Este repositório é público e usa **exclusivamente dados e imagens sintéticos**, gerados para demonstração.

---

## Início rápido (Fase 1)

> ⚙️ **Nota:** este quickstart assume caminhos relativos para os dados sintéticos incluídos no repositório. Se o `smartshelf.py` ainda tiver caminhos absolutos locais, é necessário ajustá-los primeiro (ver secção *Estrutura* abaixo).

```bash
# 1. Clonar o repositório
git clone https://github.com/MaylVrosa/Estoque-Inteligente---PTBR.git
cd Estoque-Inteligente---PTBR

# 2. Criar e ativar um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# 3. Instalar dependências
pip install pandas numpy

# 4. Correr a previsão
python smartshelf.py
```

> Ainda não existe `requirements.txt` — por agora as dependências (pandas, numpy) instalam-se manualmente. Será adicionado à medida que o projeto cresce.

---

## Estrutura do repositório

```
.
├── README.md                     # este ficheiro
├── smartshelf.py                 # Fase 1: previsão + lista de encomenda
├── fase2_visao.py                # Fase 2: deteção e contagem (em curso)
├── .gitignore
│
├── data/                         # dados SINTÉTICOS (nunca dados reais)
│   ├── produtos.csv
│   ├── resumo_mensal.csv
│   ├── sazonalidade_top15.csv
│   ├── vendas_diarias_2021_2025.csv
│   ├── vendas_mensais_2021_2025.csv
│   └── vendas_semanais_2021_2025.csv
│
└── dataset/                      # Fase 2: dataset de imagens (em anotação)
```

> **A corrigir:** atualmente o `smartshelf.py` carrega os CSV por caminho absoluto (ex.: `/Users/.../smartshelf/produtos.csv`). Para o código correr noutras máquinas, estes caminhos devem passar a relativos (ex.: `data/produtos.csv`).

---

## O que NÃO entra no repositório

Por privacidade e boas práticas, estes itens ficam **fora** do controlo de versões (ver `.gitignore`):

- **Ambientes virtuais** (`.venv/`, `.venv-anotacao/`, `.venv-visao/`) — cada pessoa cria o seu.
- **Pesos do modelo treinado** (`.pt`) — serão distribuídos via *GitHub Releases*, não no repositório.
- **Dados reais da loja** — apenas dados sintéticos são públicos.
- **Segredos** — ficheiros `.env`, chaves de API, credenciais.

---

## Manutenção

Este README acompanha o projeto. À medida que cada fase avança:

- A **tabela de estado** no topo é o primeiro sítio a atualizar.
- Os **resultados reais** (MAPE, mAP) substituem estimativas assim que existirem.
- Cada frase descreve o que o sistema **faz hoje**, não o que fará — o que estiver por construir vive na secção *Planeada*.

---

## Licença

Distribuído sob a licença MIT. Ver o ficheiro `LICENSE`.
