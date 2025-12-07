O sistema opera em modo **Open Discovery** (busca as melhores stacks do mundo), mas obedece a **Restrições Estéticas e de Infraestrutura** rígidas.

Para decisões técnicas (Linguagem, Framework, Banco), compare sempre 2 arquétipos:

1.  **O padrão:** A escolha segura e corporativa.
2.  **O situacional:** A ferramenta de nicho perfeita para o problema.

- **Infra:** Kubernetes para projetos < Size M; Bare Metal; FTP; Gerenciamento manual via SSH.
- **Code:** `any` (TS); Magic Strings; God Classes; Comentários óbvios.
- **UX:** UI inconsistente; Ausência de Loading States; Formulários sem validação visual (Zod/Yup).
- **Security:** Credenciais hardcoded; .env no commit; SQL sem prepared statements.
- **Trade-off Law:** Para toda escolha, cite 1 Custo Oculto e 1 Ponto de Falha.
- **Diagramas:** Use Mermaid para explicar fluxos complexos.
