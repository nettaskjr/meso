# Gerador de Cursos LearnPress (Markdown para XML)

Este projeto automatiza a criação de cursos para o WordPress (LearnPress) a partir de arquivos Markdown, garantindo a padronização técnica e visual das marcas mesoestetic®.

## 🚀 Como Começar

### 1. Pré-requisitos
- Python 3.x instalado.

### 2. Configuração do Ambiente
Abra o terminal na pasta do projeto e execute:
```bash
python3 -m venv venv
./venv/bin/pip install lxml markdown
```

## 📐 Diretrizes de Marca e Conteúdo

Para que o curso seja validado e o XML gerado corretamente, siga estas regras:

1.  **Padronização de Marcas**:
    *   **Maiúsculas**: Apenas `X-DNA®` e `NCTC®`.
    *   **Minúsculas**: Todos os demais produtos (`argibenone®`, `cosmelan®`, `mesoestetic®`, etc.) devem estar em minúsculas.
    *   **Símbolo ®**: Obrigatório em todas as menções aos produtos no corpo do texto. O script adiciona automaticamente, exceto no campo **Tags**, onde o símbolo é removido para manter as hashtags limpas.
2.  **Quizzes Impecáveis**:
    *   **Sem Numeração**: Não numere as perguntas (ex: use `#### Pergunta: O que é...`).
    *   **Sem Letras nas Alternativas**: Use apenas os checklists `- [ ]` ou `- [x]`.
3.  **Links Limpos**: Materiais para download sem link são removidos automaticamente para não poluir o curso.
4.  **Resumo Obrigatório**: Todo curso deve terminar com uma seção `## Resumo`.

## 📝 Estrutura do Arquivo .md

```markdown
# nome do produto®: título do curso

## Metadados
- **Carga horária:** 15 minutos
- **Imagem:** [ID da Imagem no WordPress]
- **Setores:** [ex: Todos os colaboradores]
- **Nível:** [ex: Intermediário]
- **Formador(a):** Dra. Ana Cléia Barbosa

## Descrição
Texto técnico detalhado sobre o curso.

**Conteúdo Programático:**
- Item de conteúdo 1
- Item de conteúdo 2

**Material para Download:**
- [Aula](link-drive)
- [Protocolo](link-drive)

## Seção: Título da Seção
### Aula 01 – Título da Aula
- **Duração:** 5 minutos
- **Vídeo:** link-video-drive

## Quiz: Avaliação Final
- **Duração:** 20 minutos
- **Nota de corte:** 80%

#### Pergunta: Enunciado da pergunta?
- [ ] Opção incorreta
- [x] Opção correta

## Resumo
Sintese final do curso baseada na descrição.
```

## 🛠️ Execução

Para validar as marcas, limpar links vazios e gerar o XML, execute o comando combinado:

```bash
python3 limpador_links.py && ./venv/bin/python3 conversor.py <seu-arquivo>.md
```

O script criará o arquivo `.xml` pronto para importação.

## 📤 Como Importar no WordPress
1. Acesse o painel WordPress.
2. Vá em **Ferramentas > Importar**.
3. Escolha **WordPress** e faça o upload do arquivo `.xml`.
4. O autor do curso será criado automaticamente com base no campo **Formador(a)**.

## 🤖 Workflows do Agente
Você pode solicitar ao assistente a execução do workflow `/validar-marcas` para garantir que todos os arquivos do projeto estejam seguindo as normas atuais.
