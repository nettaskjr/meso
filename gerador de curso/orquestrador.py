import os
import re
import sys
import subprocess
from pypdf import PdfReader
from docx import Document

class MesoOrchestrator:
    def __init__(self, spec_file="curso.txt"):
        self.spec_file = spec_file
        self.specs = {}
        self.course_slug = ""
        self.originais_dir = "originais"
        
    def parse_specs(self):
        print(f"📖 Lendo especificações de: {self.spec_file}")
        with open(self.spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.specs['curso'] = re.search(r'curso:\s*(.*)', content).group(1).strip()
        self.course_slug = self.specs['curso'].replace(' ', '')
        self.specs['titulo'] = re.search(r'Título:\s*(.*)', content).group(1).strip()
        
        # Extrair Metadados
        meta_section = re.search(r'Metadados\n(.*?)(?=\nDescrição:)', content, re.DOTALL).group(1)
        self.specs['metadata'] = {}
        for line in meta_section.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                self.specs['metadata'][k.strip()] = v.strip()
        
        # Extrair Links de Download
        downloads = []
        dl_matches = re.finditer(r'- \[(.*?)\]\((.*?)\)', content)
        for m in dl_matches:
            label, url = m.groups()
            if url.strip():
                downloads.append(f"- [{label}]({url})")
        self.specs['downloads'] = downloads
        
        # Quiz Meta
        quiz_section = re.search(r'Quiz:\s*(.*?)\nDuração:\s*(.*?)\nNota de corte:\s*(.*)', content)
        self.specs['quiz_title'] = quiz_section.group(1).strip()
        self.specs['quiz_duration'] = quiz_section.group(2).strip()
        self.specs['quiz_grade'] = quiz_section.group(3).strip()

    def extract_originals(self):
        print("🔍 Localizando arquivos originais...")
        pdf_file = ""
        docx_file = ""
        
        search_terms = self.specs['curso'].lower().split()
        
        def get_score(filename):
            fn = filename.lower()
            return sum(1 for term in search_terms if term in fn)

        pdf_files = [f for f in os.listdir(self.originais_dir) if f.lower().endswith('.pdf')]
        docx_files = [f for f in os.listdir(self.originais_dir) if f.lower().endswith('.docx')]
        
        best_pdf = max(pdf_files, key=get_score, default="")
        best_docx = max(docx_files, key=get_score, default="")
        
        if best_pdf and get_score(best_pdf) > 0: pdf_file = os.path.join(self.originais_dir, best_pdf)
        if best_docx and get_score(best_docx) > 0: docx_file = os.path.join(self.originais_dir, best_docx)
        
        if not pdf_file or not docx_file:
            print(f"❌ Erro: Não encontrei PDF ou DOCX para '{self.specs['curso']}' em {self.originais_dir}")
            return False, False
            
        # Extrair PDF
        print(f"📄 Extraindo PDF: {pdf_file}")
        reader = PdfReader(pdf_file)
        pdf_text = "\n".join([p.extract_text() for p in reader.pages])
        
        # Extrair DOCX
        print(f"📝 Extraindo DOCX: {docx_file}")
        doc = Document(docx_file)
        docx_text = "\n".join([p.text for p in doc.paragraphs])
        
        return pdf_text, docx_text

    def synthesize_markdown(self, pdf_text, docx_text):
        print("🧠 Sintetizando conteúdo dinâmico (Universal)...")
        
        # Limpar texto do PDF para processamento
        clean_pdf = re.sub(r'\n{2,}', '\n\n', pdf_text).strip()
        lines = [l.strip() for l in clean_pdf.split('\n') if len(l.strip()) > 5]
        
        # Heurística para Descrição Dinâmica
        # Tenta encontrar o primeiro parágrafo significativo
        core_desc = ""
        for p in clean_pdf.split('\n\n'):
            p = p.replace('\n', ' ').strip()
            if len(p) > 100 and not p.isupper():
                # Pega apenas a primeira frase ou até 300 caracteres para evitar "paredes de texto"
                first_sentence = p.split('. ')[0]
                if len(first_sentence) < 100 and '. ' in p:
                    # Se a primeira frase for muito curta, tenta pegar mais um pouco
                    core_desc = ". ".join(p.split('. ')[:2]) + "."
                else:
                    core_desc = first_sentence + "."
                break
        
        # Limpeza final de caracteres especiais que poluem o parágrafo
        core_desc = re.sub(r'[●•■*-]', '', core_desc).strip()
        core_desc = re.sub(r'\s{2,}', ' ', core_desc)

        if not core_desc and lines:
            core_desc = lines[0]

        description = (
            f"O treinamento **{self.specs['titulo']}** oferece uma imersão técnica completa voltada para profissionais que buscam excelência em resultados clínicos e performance comercial. "
            f"A abordagem integra o embasamento científico de vanguarda — focado em mecanismos de ação e eficácia comprovada — à aplicação prática de protocolos inovadores. "
            f"Contexto técnico: {core_desc} "
            "Ao concluir este módulo, o aluno estará apto a dominar as soluções diagnósticas e terapêuticas da mesoestetic®, elevando o padrão de atendimento e conversão em sua prática profissional."
        )
        
        # Gerar Tags Automáticas baseadas em base de dados de ativos e termos técnicos
        # Esta lista pode ser expandida conforme novos cursos surgirem
        concept_db = [
            'alopecia', 'peptídeos', 'tricologia', 'bulbo', 'queda', 'folículo', 'anágena', 'oxidação',
            'lipolítico', 'gordura', 'celulite', 'adiposidade', 'derme', 'epiderme', 'fibrose',
            'hiperpigmentação', 'melasma', 'ácido', 'tranexâmico', 'clareamento', 'fotoproteção',
            'antiaging', 'rugas', 'flacidez', 'colágeno', 'elastina', 'preenchimento', 'mesoterapia',
            'microagulhamento', 'biomimético', 'regeneração', 'homecare'
        ]
        
        found_tags = [self.specs['curso'].lower()]
        pdf_lower = pdf_text.lower()
        
        # Busca por marcas e ativos conhecidos na base do conversor (aproximação)
        for term in concept_db:
            if term in pdf_lower:
                found_tags.append(term)
        
        # Limita a 5 tags conforme regra anterior
        self.specs['metadata']['Tags'] = ", ".join(list(dict.fromkeys(found_tags))[:5])

        # Heurística para Conteúdo Programático (Dinâmico)
        prog_items = []
        for line in lines:
            # Filtra linhas que parecem títulos ou tópicos relevantes
            if 15 < len(line) < 70 and (line[0].isupper() or line[0] in '•-') and not line.isdigit():
                if any(k in line.lower() for k in ['curso', 'aula', 'protocolo', 'mecanismo', 'bio', 'estudo', 'fase', 'tipo', 'especificação', 'diagnóstico', 'estratégia', 'ativo', 'tratamento']):
                    clean_item = re.sub(r'^[•\-\d\.]+\s*', '', line).strip()
                    if clean_item and not clean_item.endswith(('.', ':', ',')):
                        prog_items.append(clean_item)
        
        programatico = list(dict.fromkeys(prog_items))[:8]

        resumo = f"Este treinamento capacita o profissional a dominar o tratamento de {self.specs['curso']} através de tecnologias inovadoras e ativos sinérgicos, detalhando protocolos integrados para maximizar resultados."
        
        # Processar Quiz (Parser ultra-robusto para DOCX)
        questions_md = ""
        
        # Estratégia 2: Dividir por blocos que parecem perguntas (terminam em ? ou são seguidos por alternativas)
        # Primeiro, tentamos identificar as alternativas para saber onde as perguntas terminam
        blocks = re.split(r'\n(?=[a-d][\)\.])', docx_text)
        
        # Reagrupar: Uma pergunta costuma ser o texto antes das alternativas
        current_q = ""
        current_opts = []
        
        # Tenta uma abordagem mais simples: encontrar linhas que terminam com ? ou que precedem 'a)'
        raw_lines = [l.strip() for l in docx_text.split('\n') if l.strip()]
        for i, line in enumerate(raw_lines):
            # Se a linha parece uma alternativa
            opt_match = re.match(r'^([a-d])[\)\.]\s*(.*)', line, re.IGNORECASE)
            if opt_match:
                char, opt_text = opt_match.groups()
                # Marcar como correta se houver indicação (x) ou se for a lógica de backup
                is_correct = '(x)' in line.lower()
                current_opts.append((opt_text, is_correct))
            
            # Se a linha parece uma pergunta (termina com ? ou a próxima linha é 'a)')
            elif line.endswith('?') or (i+1 < len(raw_lines) and re.match(r'^a[\)\.]', raw_lines[i+1], re.IGNORECASE)):
                # Se já tínhamos uma pergunta pendente, salva ela
                if current_q and current_opts:
                    questions_md += self._format_question_md(current_q, current_opts)
                
                current_q = line
                current_opts = []
        
        # Salva a última pergunta
        if current_q and current_opts:
            questions_md += self._format_question_md(current_q, current_opts)

        # Montar MD Final
        md_content = f"# {self.specs['titulo']}\n\n## Metadados\n"
        for k, v in self.specs['metadata'].items():
            md_content += f"- {k}: {v}\n"
        
        md_content += f"\n## Descrição\n{description}\n\n"
        md_content += "**Conteúdo Programático:**\n"
        for item in programatico: md_content += f"- {item}\n"
        
        md_content += f"\n**Material para Download:**\n"
        for dl in self.specs['downloads']: md_content += f"{dl}\n"
        
        md_content += f"\n## Resumo\n{resumo}\n\n"
        md_content += f"## Quiz: {self.specs['quiz_title']}\n"
        md_content += f"- **Duração:** {self.specs['quiz_duration']}\n"
        md_content += f"- **Nota de corte:** {self.specs['quiz_grade']}\n\n"
        md_content += questions_md
        
        md_path = f"{self.course_slug}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"✅ Markdown gerado: {md_path}")
        return md_path

    def _format_question_md(self, title, options):
        # Garante que ao menos uma opção seja verdadeira (se nenhuma for marcada, a primeira é fallback para evitar erro)
        if not any(is_correct for _, is_correct in options):
            options[0] = (options[0][0], True)
            
        md = f"#### Pergunta: {title}\n"
        for opt, is_true in options:
            mark = "x" if is_true else " "
            md += f"- [{mark}] {opt}\n"
        md += f"- **Explicação:** [Conforme detalhado no material técnico do curso.]\n\n"
        return md

    def run_converter(self, md_path):
        print(f"⚙️  Chamando conversor.py para gerar o XML...")
        try:
            subprocess.run(["python3", "conversor.py", md_path], check=True)
            return True
        except Exception as e:
            print(f"❌ Erro ao rodar conversor: {e}")
            return False

    def execute(self):
        self.parse_specs()
        pdf_text, docx_text = self.extract_originals()
        if pdf_text and docx_text:
            md_path = self.synthesize_markdown(pdf_text, docx_text)
            if self.run_converter(md_path):
                print(f"\n🚀 PROCESSO CONCLUÍDO COM SUCESSO!")
                print(f"📂 Arquivo pronto para importação: {md_path.replace('.md', '.xml')}")

if __name__ == "__main__":
    orch = MesoOrchestrator()
    orch.execute()
