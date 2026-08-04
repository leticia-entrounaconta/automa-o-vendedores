# Contrato da base consolidada

`parceiros_classificados.xlsx` contém uma aba `DADOS` com uma linha por vendedor e
uma aba `CONTROLE` com a rastreabilidade da execução. Quando houver exceções, terá
também a aba `PRODUCOES_NAO_RELACIONADAS`. A chave primária de relação
é `codigo_vendedor`; `cpf_cnpj` é somente alternativa para chaves únicas.

As datas de origem são preservadas. `data_referencia_producao` segue a prioridade
configurável `pagamento,producao,digitacao`; a origem fica registrada como
`pagamento`, `producao`, `digitacao` ou `sem_data`. O relatório atual não expõe
data de pagamento por proposta, portanto esse campo permanecerá falso até que o
relatório passe a fornecê-la.

Os indicadores são calculados na data da execução. Meses sem produção entram como
zero nas médias apenas quando houver histórico suficiente para 3 ou 6 meses;
caso contrário, a média fica nula. `percentual_queda` compara os últimos 30 dias
com os 30 dias imediatamente anteriores; quando não há base anterior, o valor é
nulo. Banco e produto principais são escolhidos pelo maior valor produzido e,
em empate, pelo nome em ordem alfabética.

`STATUS_PRODUCAO_VALIDA` permanece vazio até que os status reais sejam confirmados
no relatório. Sem essa configuração a base não afirma que uma proposta digitada é
uma venda válida.
