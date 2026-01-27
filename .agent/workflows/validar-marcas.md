---
description: Validação e Padronização de Marcas nos Cursos
---

Este workflow descreve como garantir que todos os cursos sigam as diretrizes de marca da mesoestetic®.

### Regras de Ouro
1. **Lowercase (com Exceções)**: A maioria dos nomes de produtos deve estar em letras minúsculas.
   - **Exceções (Sempre Maiúsculas)**: `X-DNA®` e `NCTC®`.
   - Correto: `argibenone®`, `X-DNA®`, `NCTC®`.
2. **Símbolo ®**: Todos os nomes de produtos no corpo do texto devem ser seguidos pelo símbolo `®`.
   - **Nota**: O script remove este símbolo automaticamente do campo de **Tags** para manter as hashtags limpas.
3. **Sem Numeração/Letras**: Perguntas e alternativas de Quizzes NÃO devem ter numeração ou letras manuais.
4. **Links de Download**: Não incluir itens na seção "Material para Download" que não possuam URL definida.
5. **Seção Resumo**: Todo curso deve conter uma seção `## Resumo` ao final.
6. **Hashtags (Tags)**: Não devem conter o símbolo `®`.

### Automação
A lógica de padronização está integrada ao script `conversor.py` e ao `limpador_links.py`.

Para validar as regras e gerar o XML atualizado:

// turbo
1. Execute a limpeza e conversão:
```bash
python3 limpador_links.py && ./venv/bin/python3 conversor.py <nome-do-arquivo>.md
```

O script irá automaticamente:
- Formatar marcas (respeitando as exceções `X-DNA` e `NCTC`).
- Adicionar o símbolo `®` no conteúdo e remover das Tags.
- Remover itens de download sem link.
- Vincular o autor dinâmico (Formador).
- Gerar o XML pronto para importação.
