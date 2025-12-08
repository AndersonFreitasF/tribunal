# TECH BIBLE

### 1. PROTOCOLO DE DECISÃO (Seguro VS Melhor)
Nenhuma tecnologia é escolhida sem disputa. Para cada decisão, apresente:
- **Seguro (Sua escolha):** A recomendação principal.
- **Melhor (A alternativa):** A melhor concorrente de mercado.
- **Critério de Desempate:** Compare explicitamente Adequação, Consumo de Recursos e Maturidade.

### 2. LISTA DE EXCLUSÃO (VETO AUTOMÁTICO)
O desrespeito a estas regras gera veto imediato na auditoria:
- **INFRA:** PROIBIDO Kubernetes para projetos pequenos (Size < M). PROIBIDO Bare Metal, FTP e SSH manual.
- **CODE:** PROIBIDO uso de 'any' (TS). PROIBIDO Magic Strings e God Classes.
- **UX:** PROIBIDO UI inconsistente, ausência de Loading States ou falta de validação visual.
- **SEC:** PROIBIDO Credenciais hardcoded, .env no commit e SQL sem Prepared Statements.

### 3. SAÍDA OBRIGATÓRIA
- **Lei do Trade-off:** Para TODA escolha, cite: 1 Custo Oculto + 1 Ponto de Falha.
- **Diagramas:** Use Mermaid para explicar fluxos.
