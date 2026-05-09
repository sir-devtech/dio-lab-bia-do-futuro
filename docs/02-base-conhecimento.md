# Base de Conhecimento

> [!TIP]
> **Prompt usado para esta etapa:**
> 
> Organize a base de conhecimento do agente "Edu" usando os 4 arquivos da pasta `data/` (em anexo). Explique pra que serve cada arquivo e monte um exemplo de contexto formatado que será enviado pro LLM. Preencha o template abaixo.
>
> [cole ou anexe o template `02-base-conhecimento.md` pra contexto]

## Dados Utilizados

| Arquivo | Formato | Para que serve no Edu? |
|---------|---------|---------------------|
| `historico_atendimento.csv` | CSV | Contextualizar interações anteriores, ou seja, dar continuidade ao atendimento de forma mais eficiente. |
| `perfil_investidor.json` | JSON | Personalizar as explicações sobre as dúvidas e necessidades de aprendizado do cliente. |
| `produtos_financeiros.json` | JSON | Conhecer os produtos disponíveis para que eles possam ser ensinados ao cliente. |
| `transacoes.csv` | CSV | Analisar padrão de gastos do cliente e usar essas informações de forma didática. |

---

## Adaptações nos Dados

> Você modificou ou expandiu os dados mockados? Descreva aqui.

As seguintes adaptações foram realizadas:

1. **Perfil do cliente:** João Silva foi substituído por **Ana Lima**, 28 anos, Designer Gráfica, renda R$ 4.500, perfil conservador. As metas foram atualizadas para refletir objetivos mais próximos de um iniciante: completar reserva de emergência (6x salário = R$ 27.000), viagem internacional e curso de especialização.

2. **Transações:** Expandidas de 10 linhas (apenas outubro) para **38 linhas cobrindo 3 meses** (agosto, setembro e outubro), com categorias mais variadas incluindo `poupanca`, `beleza` e `educacao`. Isso permite que o Edu faça análises de tendência entre meses.

3. **Histórico de atendimento:** Atualizado para refletir os temas de interesse da Ana Lima (reserva de emergência, CDB, Tesouro Selic), mantendo a estrutura original.

4. **Produto Fundo Imobiliário (FII):** Mantido em substituição ao Fundo Multimercado original, por ser um produto amplamente conhecido e validável.

---

## Estratégia de Integração

### Como os dados são carregados?
> Descreva como seu agente acessa a base de conhecimento.

Existem duas possibilidades, injetar os dados diretamente no prompt (Ctrl + C, Ctrl + V) ou carregar os arquivos via código, como no exemplo abaixo:

```python
import pandas as pd
import json

import os

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

with open(os.path.join(BASE_DIR, "perfil_investidor.json"), encoding="utf-8") as f:
    perfil = json.load(f)
transacoes = pd.read_csv(os.path.join(BASE_DIR, "transacoes.csv"))
historico = pd.read_csv(os.path.join(BASE_DIR, "historico_atendimento.csv"))
with open(os.path.join(BASE_DIR, "produtos_financeiros.json"), encoding="utf-8") as f:
    produtos = json.load(f)
```

### Como os dados são usados no prompt?
> Os dados vão no system prompt? São consultados dinamicamente?

Para simplificar, podemos simplesmente "injetar" os dados em nosso prompt, agarntindo que o Agente tenha o melhor contexto possível. Lembrando que, em soluções mais robustas, o ideal é que essas informaçoes sejam carregadas dinamicamente para que possamos ganhar flexibilidade.

```text
DADOS DO CLIENTE E PERFIL (data/perfil_investidor.json):
{
  "nome": "João Silva",
  "idade": 32,
  "profissao": "Analista de Sistemas",
  "renda_mensal": 5000.00,
  "perfil_investidor": "moderado",
  "objetivo_principal": "Construir reserva de emergência",
  "patrimonio_total": 15000.00,
  "reserva_emergencia_atual": 10000.00,
  "aceita_risco": false,
  "metas": [
    {
      "meta": "Completar reserva de emergência",
      "valor_necessario": 15000.00,
      "prazo": "2026-06"
    },
    {
      "meta": "Entrada do apartamento",
      "valor_necessario": 50000.00,
      "prazo": "2027-12"
    }
  ]
}

TRANSACOES DO CLIENTE (data/transacoes.csv):
data,descricao,categoria,valor,tipo
2025-10-01,Salário,receita,5000.00,entrada
2025-10-02,Aluguel,moradia,1200.00,saida
2025-10-03,Supermercado,alimentacao,450.00,saida
2025-10-05,Netflix,lazer,55.90,saida
2025-10-07,Farmácia,saude,89.00,saida
2025-10-10,Restaurante,alimentacao,120.00,saida
2025-10-12,Uber,transporte,45.00,saida
2025-10-15,Conta de Luz,moradia,180.00,saida
2025-10-20,Academia,saude,99.00,saida
2025-10-25,Combustível,transporte,250.00,saida

HISTORICO DE ATENDIMENTO DO CLIENTE (data/historico_atendimento.csv):
data,canal,tema,resumo,resolvido
2025-09-15,chat,CDB,Cliente perguntou sobre rentabilidade e prazos,sim
2025-09-22,telefone,Problema no app,Erro ao visualizar extrato foi corrigido,sim
2025-10-01,chat,Tesouro Selic,Cliente pediu explicação sobre o funcionamento do Tesouro Direto,sim
2025-10-12,chat,Metas financeiras,Cliente acompanhou o progresso da reserva de emergência,sim
2025-10-25,email,Atualização cadastral,Cliente atualizou e-mail e telefone,sim

PRODUTOS DISPONIVEIS PARA ENSINO (data/produtos_financeiros.json):
[
  {
    "nome": "Tesouro Selic",
    "categoria": "renda_fixa",
    "risco": "baixo",
    "rentabilidade": "100% da Selic",
    "aporte_minimo": 30.00,
    "indicado_para": "Reserva de emergência e iniciantes"
  },
  {
    "nome": "CDB Liquidez Diária",
    "categoria": "renda_fixa",
    "risco": "baixo",
    "rentabilidade": "102% do CDI",
    "aporte_minimo": 100.00,
    "indicado_para": "Quem busca segurança com rendimento diário"
  },
  {
    "nome": "LCI/LCA",
    "categoria": "renda_fixa",
    "risco": "baixo",
    "rentabilidade": "95% do CDI",
    "aporte_minimo": 1000.00,
    "indicado_para": "Quem pode esperar 90 dias (isento de IR)"
  },
  {
    "nome": "Fundo Imobiliário (FII)",
    "categoria": "fundo",
    "risco": "medio",
    "rentabilidade": "Dividend Yield (DY) costuma ficar entre 6% a 12% ao ano",
    "aporte_minimo": 100.00,
    "indicado_para": "Perfil moderado que busca diversificação e renda recorrente mensal"
  },
  {
    "nome": "Fundo de Ações",
    "categoria": "fundo",
    "risco": "alto",
    "rentabilidade": "Variável",
    "aporte_minimo": 100.00,
    "indicado_para": "Perfil arrojado com foco no longo prazo"
  }
]
```

---

## Exemplo de Contexto Montado

> Mostre um exemplo de como os dados são formatados para o agente.

O contexto é injetado diretamente no prompt, contendo todas as informações relevantes da Ana Lima. Histórico de conversa multi-turno é mantido no `st.session_state` e incluído no prompt a cada nova mensagem.

```
DADOS DO CLIENTE:
- Nome: Ana Lima, 28 anos, Designer Gráfica
- Renda: R$ 4.500 | Perfil: Conservador
- Objetivo: Construir reserva de emergência e começar a investir
- Patrimônio: R$ 8.000 | Reserva atual: R$ 5.000
- Metas:
  - Completar reserva de emergência (6x salário): R$ 27.000 até 2027-06
  - Viagem internacional: R$ 8.000 até 2026-12
  - Curso de especialização: R$ 5.000 até 2026-08

RESUMO DE GASTOS (outubro/2025):
- Moradia: R$ 1.137,90 (aluguel + luz + internet)
- Alimentação: R$ 490,00 (supermercado + restaurante)
- Transporte: R$ 226,00 (combustível + Uber)
- Saúde: R$ 121,00 (academia + farmácia)
- Lazer: R$ 55,90 (Netflix)
- Poupança: R$ 500,00
- Total de saídas: R$ 2.530,80

PRODUTOS DISPONÍVEIS PARA EXPLICAR:
- Tesouro Selic (risco baixo) — ideal para reserva de emergência
- CDB Liquidez Diária (risco baixo) — ótimo ponto de partida
- LCI/LCA (risco baixo) — isento de IR após 90 dias
- Fundo Imobiliário - FII (risco médio)
- Fundo de Ações (risco alto)
```
