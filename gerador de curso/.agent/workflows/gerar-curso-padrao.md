---
description: Fluxo padrão para geração de cursos a partir de arquivos originais e legados
---

Este workflow define o processo de criação de novos cursos ou regeneração de antigos, garantindo a consistência dos dados e reaproveitamento de metadados.

### Passos do Workflow

1. **Extração de Dados**:
   - Localize os arquivos `.pdf` e `.docx` do produto na pasta `originais/`.
   - Use `pdftotext` para extrair a descrição técnica e o conteúdo programático.
   - Extraia as questões do quiz a partir do `document.xml` do arquivo `.docx`.

2. **Recuperação de Legado**:
   - Localize o arquivo Markdown (`.md`) do produto na pasta `antigos/`.
   - Extraia o **ID da Imagem** (`Imagem: XXXX`).
   - Extraia todos os links da seção **Material para Download**.
   - Verifique a existência de uma seção de **Vídeos**.

3. **Consolidação no `curso.txt`**:
   - Atualize o arquivo `curso.txt` na raiz do projeto com:
     - Novos dados extraídos (Passo 1).
     - Metadados e links legados (Passo 2).
     - Carga horária, tags e setores conforme o padrão meso.

4. **Geração dos Arquivos Finais**:
   - Crie o arquivo `.md` final na raiz do projeto.
   - Execute `python3 conversor.py <arquivo>.md` para gerar o `.xml`.

5. **Finalização e Organização**:
   - Atualize o `CHECKLIST_UPLOAD.md`.
   - Mova os arquivos temporários `_pdf.txt` e `_docx.txt` para a pasta `temp/`.
   - Notifique o usuário sobre a conclusão do curso atual.

6. **Espera pelo Próximo Curso**:
   - Aguarde o usuário informar o nome do próximo produto no chat para reiniciar o fluxo.
