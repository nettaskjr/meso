import os
import re
import sys
import argparse
import markdown
import unicodedata
from lxml import etree
import datetime
import random
import string

class LearnPressGenerator:
    def __init__(self, md_path, output_path):
        self.md_path = md_path
        self.output_path = output_path
        self.course_data = {
            'title': '',
            'metadata': {},
            'description': '',
            'excerpt': '',
            'sections': []
        }
        # Lista de produtos para normalização automática
        self.brand_products = [
            'melan 130 pigment control', 'melan tran3x', 'depigmentation solution',
            'age element', 'argibenone', 'cosmelan', 'NCTC', 'depigmentation',
            'melantranx', 'melantran3x', 'melaphenone', 'cosmesome', 'mesoestetic',
            'mesoprotech', 'c.prof', 'idebenona', 'X-DNA', 'mesotox', 'dmae', 'vitamina c', 'glutathion', 'solution',
            'mesopeel', 'blemiskin', 'melanostop tranex', 'jessner pro', 'eyecon', 'senopeptide',
            'skinmark', 'c.prof 223', 'darutosídeo', 'chlorella vulgaris', 'm.pen [pro]', 'PDRN', 'silício orgânico',
            'x.prof', 'dna', 'mesotox solution', 'acetil hexapeptídeo-8', 'pentapeptídeo-18', 'silício', 'skinretin', 'retinal',
            'redenx', 'mesohyal', 'Tripeptídeo 2KV', 'Tetrapeptídeo HNQV', 'Transetossomas',
            'melantran3x', 'melan tran3x', 'c.prof 210', 'Try Control Peptídeo', 'N-acetil glucosamina', 'idebenona', 'azeloglicina',
            'solutions', 'photoaging solution', 'photoaging', 'c.prof 211', 'taurina'
        ]

    def normalize_brand_names(self, text):
        if not text: return ""
        
        # 1. Garante sempre mesoestetic® (preservando o caso original do texto: Mesoestetic -> Mesoestetic®)
        text = re.sub(r'\b(mesoestetic)\b(?!®)', r'\1®', text, flags=re.IGNORECASE)
        
        # 2. Normaliza apenas as exceções que DEVEM ser sempre maiúsculas
        exceptions = ['NCTC', 'X-DNA', 'PDRN']
        for exc in exceptions:
            pattern = re.compile(r'\b' + re.escape(exc) + r'\b', re.IGNORECASE)
            text = pattern.sub(exc, text)
            
        # Nota: Removida a conversão forçada para minúsculas dos outros produtos 
        # para respeitar a grafia original do arquivo (ex: SOLUTIONS continuará SOLUTIONS)
        
        return text

    def parse_markdown(self):
        with open(self.md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extrair Título (# Titulo)
        title_match = re.search(r'^#\s+(.*)$', content, re.MULTILINE)
        if title_match:
            self.course_data['title'] = self.normalize_brand_names(title_match.group(1).strip())

        # Extrair Metadados
        meta_section = re.search(r'## Metadados\n(.*?)(?=\n##|$)', content, re.DOTALL)
        if meta_section:
            meta_text = meta_section.group(1)
            for line in meta_text.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.replace('-', '').replace('*', '').strip()
                    val = val.replace('*', '').replace('"', '').strip()
                    # Normalizar valores do metadados
                    normalized_val = self.normalize_brand_names(val)
                    # Remover símbolo ® de tags/hashtags conforme solicitado
                    if key.lower() in ['tags', 'tag']:
                        normalized_val = normalized_val.replace('®', '')
                    self.course_data['metadata'][key] = normalized_val

        # Extrair Descrição (Captura o texto bruto para processamento posterior)
        desc_section = re.search(r'## Descrição\n(.*?)(?=\n##|$)', content, re.DOTALL)
        desc_raw_text = desc_section.group(1).strip() if desc_section else ""

        # Extrair Resumo
        resumo_section = re.search(r'## Resumo\n(.*?)(?=\n##|$)', content, re.DOTALL)
        if resumo_section:
            self.course_data['excerpt'] = resumo_section.group(1).strip()

        # Extrair Seções e Lições/Quizzes
        # Aceita tanto "## Seção: Nome" quanto "## Quiz: Nome"
        sections_matches = re.finditer(r'## (Seção|Quiz):\s*(.*?)\n(.*?)(?=\n## (Seção|Quiz):|\n## Resumo|$)', content, re.DOTALL)
        for match in sections_matches:
            tag_type = match.group(1).strip()
            section_title = self.normalize_brand_names(match.group(2).strip())
            section_content = match.group(3).strip()
            
            section_description = ""
            items = []
            
            # Se a própria seção for um Quiz (## Quiz:)
            if tag_type == "Quiz":
                # Criamos um "bloco virtual" de quiz para o processador abaixo
                item_blocks = ["### Quiz: " + section_title + "\n" + section_content]
            else:
                # Caso padrão: Dividimos o conteúdo da seção pelos marcadores '###'
                item_blocks = re.split(r'\n(?=###)', "\n" + section_content)
            
            for block in item_blocks:
                block = block.strip()
                if not block: continue
                
                if not block.startswith('###'):
                    section_description = self.normalize_brand_names(block)
                    continue
                
                # Identificar se é Quiz ou Lesson
                if block.startswith('### Quiz:'):
                    # Processar Quiz
                    quiz_lines = block.split('\n')
                    quiz_title = self.normalize_brand_names(quiz_lines[0].replace('### Quiz:', '').strip())
                    quiz_body = '\n'.join(quiz_lines[1:]).strip()
                    
                    quiz_meta = {'duration': '10 minute', 'passing_grade': '80', 'retake_count': '10'}
                    # Extrair meta do Quiz
                    dur_match = re.search(r'^- \*\*Duração:\*\* (.*)$', quiz_body, re.MULTILINE | re.IGNORECASE)
                    if dur_match: 
                        quiz_meta['duration'] = dur_match.group(1).strip()
                        quiz_body = quiz_body.replace(dur_match.group(0), "").strip()
                    
                    grade_match = re.search(r'^- \*\*Nota de corte:\*\* (.*)$', quiz_body, re.MULTILINE | re.IGNORECASE)
                    if grade_match:
                        quiz_meta['passing_grade'] = grade_match.group(1).replace('%', '').strip()
                        quiz_body = quiz_body.replace(grade_match.group(0), "").strip()

                    # Extrair Perguntas
                    questions = []
                    question_blocks = re.split(r'\n(?=#### Pergunta:)', "\n" + quiz_body)
                    for q_block in question_blocks:
                        q_block = q_block.strip()
                        if not q_block.startswith('#### Pergunta:'): continue
                        
                        q_lines = q_block.split('\n')
                        q_header = self.normalize_brand_names(q_lines[0].replace('#### Pergunta:', '').strip())
                        
                        q_body = '\n'.join(q_lines[1:]).strip()
                        
                        q_explanation = ""
                        expl_match = re.search(r'^- \*\*Explicação:\*\* (.*)$', q_body, re.MULTILINE | re.IGNORECASE)
                        if expl_match:
                            q_explanation = self.normalize_brand_names(expl_match.group(1).strip())
                            q_body = q_body.replace(expl_match.group(0), "").strip()

                        # Extrair Opções
                        answers = []
                        option_matches = re.finditer(r'^- \[(x| )\] (.*)$', q_body, re.MULTILINE | re.IGNORECASE)
                        for idx, opt_match in enumerate(option_matches):
                            is_correct = opt_match.group(1).lower() == 'x'
                            ans_text = self.normalize_brand_names(opt_match.group(2).strip())
                            answers.append({
                                'title': ans_text,
                                'is_true': 'yes' if is_correct else '',
                                'order': idx + 1
                            })
                        
                        # Determinar tipo automaticamente pelo número de respostas corretas
                        correct_count = sum(1 for a in answers if a['is_true'] == 'yes')
                        q_type = 'multi_choice' if correct_count > 1 else 'single_choice'

                        questions.append({
                            'title': q_header,
                            'explanation': q_explanation,
                            'answers': answers,
                            'type': q_type
                        })
                    
                    # Injetar CSS para esconder o bloco do instrutor no Quiz (Limpeza visual)
                    clean_header_css = '<style>.quiz-instructor, .lp-quiz-instructor, .instructor-item { display: none !important; }</style>'
                    
                    items.append({
                        'type': 'lp_quiz',
                        'title': quiz_title,
                        'meta': quiz_meta,
                        'content': clean_header_css + markdown.markdown(self.normalize_brand_names(quiz_body)),
                        'questions': questions
                    })
                else:
                    # Processar Lição (Lesson)
                    lines = block.split('\n')
                    l_title_line = self.normalize_brand_names(lines[0].replace('###', '').strip())
                    l_raw_body = '\n'.join(lines[1:]).strip()
                    
                    l_duration = ""
                    l_video = ""
                    
                    duration_match = re.search(r'^- \*\*Duração:\*\* (.*)$', l_raw_body, re.MULTILINE | re.IGNORECASE)
                    if duration_match:
                        l_duration = duration_match.group(1).strip()
                        l_raw_body = l_raw_body.replace(duration_match.group(0), "").strip()

                    video_match = re.search(r'^- \*\*Vídeo:\*\* (.*)$', l_raw_body, re.MULTILINE | re.IGNORECASE)
                    if video_match:
                        l_video = video_match.group(1).strip()
                        l_raw_body = l_raw_body.replace(video_match.group(0), "").strip()

                    l_normalized_body = self.normalize_brand_names(l_raw_body)
                    if l_video:
                        embed_url = l_video.replace('/view?usp=drive_link', '/preview').replace('/view', '/preview')
                        video_html = f'<p style="text-align: center;"><iframe src="{embed_url}" width="640" height="360" allow="autoplay"></iframe></p>\n'
                        l_final_content = video_html + markdown.markdown(l_normalized_body)
                    else:
                        l_final_content = markdown.markdown(l_normalized_body)

                    items.append({
                        'type': 'lp_lesson',
                        'title': l_title_line, 
                        'content': l_final_content,
                        'duration': l_duration,
                        'video_url': l_video
                    })
            
            self.course_data['sections'].append({
                'title': section_title,
                'description': section_description,
                'items': items
            })

        # --- Lógica de Carga Horária (Soma ou Manual) ---
        total_minutes = 0
        has_durations = False
        for section in self.course_data['sections']:
            for item in section['items']:
                dur_text = ""
                if item['type'] == 'lp_lesson':
                    dur_text = item.get('duration', '').lower()
                elif item['type'] == 'lp_quiz':
                    dur_text = item['meta'].get('duration', '').lower()
                
                num_match = re.search(r'(\d+)', dur_text)
                if num_match:
                    num = int(num_match.group(1))
                    has_durations = True
                    if 'hora' in dur_text: total_minutes += num * 60
                    else: total_minutes += num
        
        if has_durations and total_minutes > 0:
            if total_minutes >= 60:
                h, m = divmod(total_minutes, 60)
                display_dur = f"{h}h" + (f" {m}min" if m > 0 else "")
            else: display_dur = f"{total_minutes} min"
            self.course_data['metadata']['Carga horária'] = display_dur
        else:
            manual_val = self.course_data['metadata'].get('Carga horária', '')
            if "calculado" in manual_val.lower(): self.course_data['metadata']['Carga horária'] = "0h"

        # Descrição Final
        if desc_raw_text:
            meta_block = "\n<!-- Metadados do Curso -->\n"
            exclude_from_desc = ['Imagem', 'Categoria', 'Tags', 'Autor']
            for key, val in self.course_data['metadata'].items():
                if key not in exclude_from_desc:
                    meta_block += f"<strong>{key}:</strong> {val}<br>\n"
            meta_block += "<br>\n"
            if "Conteúdo Programático" in desc_raw_text:
                clean_text = re.sub(r'\**Conteúdo Programático:?\**', 'TOKEN_PARA_SPLIT', desc_raw_text)
                parts = clean_text.split('TOKEN_PARA_SPLIT', 1)
                full_html = markdown.markdown(parts[0]) + meta_block + markdown.markdown("**Conteúdo Programático:**" + parts[1])
            elif "Material para Download" in desc_raw_text:
                clean_text = re.sub(r'\**Material para Download:?\**', 'TOKEN_PARA_SPLIT', desc_raw_text)
                parts = clean_text.split('TOKEN_PARA_SPLIT', 1)
                full_html = markdown.markdown(parts[0]) + meta_block + markdown.markdown("**Material para Download:**" + parts[1])
            else: full_html = markdown.markdown(desc_raw_text) + meta_block
            
            # Normalização de marca na descrição e resumo final
            self.course_data['description'] = self.normalize_brand_names(full_html)
            self.course_data['excerpt'] = self.normalize_brand_names(self.course_data['excerpt'])

    def slugify(self, text):
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
        return text

    def generate_xml(self):
        NS_WP = "http://wordpress.org/export/4.1.0/"
        NS_CONTENT = "http://purl.org/rss/1.0/modules/content/"
        NS_DC = "http://purl.org/dc/elements/1.1/"
        NS_EXCERPT = "http://wordpress.org/export/4.1.0/excerpt/"
        NS_WFW = "http://wellformedweb.org/CommentAPI/"
        nsmap = {
            'wp': NS_WP, 
            'content': NS_CONTENT, 
            'dc': NS_DC, 
            'excerpt': NS_EXCERPT,
            'wfw': NS_WFW
        }

        rss = etree.Element("rss", version="2.0", nsmap=nsmap)
        channel = etree.SubElement(rss, "channel")

        now_wp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now_rfc = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')

        # Adicionar informações de base do site (conforme modelo)
        etree.SubElement(channel, "title").text = "Mesoestetic Academy"
        etree.SubElement(channel, "link").text = "https://academy.mesoestetic.com.br"
        etree.SubElement(channel, "description").text = "Cursos e Treinamentos"
        etree.SubElement(channel, "pubDate").text = now_rfc
        etree.SubElement(channel, "language").text = "pt-BR"
        etree.SubElement(channel, "{%s}wxr_version" % NS_WP).text = "4.1.0"
        etree.SubElement(channel, "{%s}base_site_url" % NS_WP).text = "https://academy.mesoestetic.com.br"
        etree.SubElement(channel, "{%s}base_blog_url" % NS_WP).text = "https://academy.mesoestetic.com.br"
        etree.SubElement(channel, "{%s}plugin_name" % NS_WP).text = "learnpress"
        etree.SubElement(channel, "{%s}plugin_version" % NS_WP).text = "4.1.0"

        # Autor dinâmico baseado no Formador (se existir nos metadados)
        author_from_meta = self.course_data['metadata'].get('Formador(a)') or self.course_data['metadata'].get('Formador')
        if author_from_meta:
            # Slug do nome para o login (ex: Ana Cléia Barbosa -> ana-cleia-barbosa)
            author_login = self.slugify(author_from_meta)
        else:
            author_login = 'admin'

        # 1. Processar Termos (Categorias e Tags) para garantir IDs únicos
        term_definitions = []
        term_id_counter = 50000
        
        # Categorias
        if 'Categoria' in self.course_data['metadata']:
            categories = self.course_data['metadata']['Categoria'].split(',')
            for cat_name in categories:
                cat_name = cat_name.strip().replace('"', '')
                if cat_name:
                    term_id = term_id_counter
                    term_id_counter += 1
                    term_slug = self.slugify(cat_name)
                    term_definitions.append({
                        'id': term_id,
                        'name': cat_name,
                        'slug': term_slug,
                        'taxonomy': 'course_category'
                    })
                    # Registrar no canal
                    term = etree.SubElement(channel, "{%s}term" % NS_WP)
                    etree.SubElement(term, "{%s}term_id" % NS_WP).text = str(term_id)
                    etree.SubElement(term, "{%s}term_taxonomy" % NS_WP).text = "course_category"
                    etree.SubElement(term, "{%s}term_slug" % NS_WP).text = term_slug
                    etree.SubElement(term, "{%s}term_name" % NS_WP).text = etree.CDATA(cat_name)
                    etree.SubElement(term, "{%s}term_parent" % NS_WP).text = etree.CDATA("")
                    etree.SubElement(term, "{%s}term_description" % NS_WP).text = etree.CDATA("")

        # Tags
        if 'Tags' in self.course_data['metadata']:
            tags = self.course_data['metadata']['Tags'].split(',')
            for tag_name in tags:
                tag_name = tag_name.strip().replace('"', '')
                if tag_name:
                    term_id = term_id_counter
                    term_id_counter += 1
                    term_slug = self.slugify(tag_name)
                    term_definitions.append({
                        'id': term_id,
                        'name': tag_name,
                        'slug': term_slug,
                        'taxonomy': 'course_tag'
                    })
                    # Registrar no canal
                    term = etree.SubElement(channel, "{%s}term" % NS_WP)
                    etree.SubElement(term, "{%s}term_id" % NS_WP).text = str(term_id)
                    etree.SubElement(term, "{%s}term_taxonomy" % NS_WP).text = "course_tag"
                    etree.SubElement(term, "{%s}term_slug" % NS_WP).text = term_slug
                    etree.SubElement(term, "{%s}term_name" % NS_WP).text = etree.CDATA(tag_name)
                    etree.SubElement(term, "{%s}term_parent" % NS_WP).text = etree.CDATA("")
                    etree.SubElement(term, "{%s}term_description" % NS_WP).text = etree.CDATA("")

        # 2. Curso
        course_id = "99000"
        course_slug = self.slugify(self.course_data['title'])
        course_item = etree.SubElement(channel, "item")
        etree.SubElement(course_item, "title").text = self.course_data['title']
        etree.SubElement(course_item, "link").text = f"https://academy.mesoestetic.com.br/?lp_course={course_slug}"
        etree.SubElement(course_item, "pubDate").text = now_rfc
        etree.SubElement(course_item, "{%s}creator" % NS_DC).text = etree.CDATA(author_login)
        etree.SubElement(course_item, "guid", isPermaLink="false").text = f"https://academy.mesoestetic.com.br/?post_type=lp_course&#038;p={course_id}"
        etree.SubElement(course_item, "{%s}encoded" % NS_CONTENT).text = etree.CDATA(self.course_data['description'])
        etree.SubElement(course_item, "{%s}encoded" % NS_EXCERPT).text = etree.CDATA(self.course_data['excerpt'])
        etree.SubElement(course_item, "{%s}post_id" % NS_WP).text = course_id
        etree.SubElement(course_item, "{%s}post_date" % NS_WP).text = now_wp
        etree.SubElement(course_item, "{%s}post_name" % NS_WP).text = course_slug
        etree.SubElement(course_item, "{%s}status" % NS_WP).text = "draft"
        etree.SubElement(course_item, "{%s}post_type" % NS_WP).text = "lp_course"

        # Inicialização de contadores para IDs únicos
        id_counter = 100000
        section_id_counter = 100

        # Lógica de Imagem de Destaque (Featured Image)
        image_val = self.course_data['metadata'].get('Imagem')
        if image_val:
            # Opção 1: ID Numérico (Imagem já existente no WordPress)
            if image_val.isdigit():
                pm_thumb = etree.SubElement(course_item, "{%s}postmeta" % NS_WP)
                etree.SubElement(pm_thumb, "{%s}meta_key" % NS_WP).text = "_thumbnail_id"
                etree.SubElement(pm_thumb, "{%s}meta_value" % NS_WP).text = etree.CDATA(image_val)
            else:
                # Opção 2 e 3: URL ou Nome de Arquivo
                image_id = str(id_counter)
                id_counter += 1
                
                # Vincular a imagem ao curso
                pm_thumb = etree.SubElement(course_item, "{%s}postmeta" % NS_WP)
                etree.SubElement(pm_thumb, "{%s}meta_key" % NS_WP).text = "_thumbnail_id"
                etree.SubElement(pm_thumb, "{%s}meta_value" % NS_WP).text = etree.CDATA(image_id)
                
                # Se for URL completa, extraímos apenas o nome para o título
                display_name = image_val.split('/')[-1] if '/' in image_val else image_val
                
                # Criar o item de anexo no canal
                attach_item = etree.SubElement(channel, "item")
                etree.SubElement(attach_item, "title").text = display_name
                etree.SubElement(attach_item, "pubDate").text = now_rfc
                etree.SubElement(attach_item, "{%s}creator" % NS_DC).text = etree.CDATA(author_login)
                etree.SubElement(attach_item, "{%s}post_id" % NS_WP).text = image_id
                etree.SubElement(attach_item, "{%s}post_date" % NS_WP).text = now_wp
                etree.SubElement(attach_item, "{%s}status" % NS_WP).text = "inherit"
                etree.SubElement(attach_item, "{%s}post_type" % NS_WP).text = "attachment"
                etree.SubElement(attach_item, "{%s}post_name" % NS_WP).text = self.slugify(display_name.split('.')[0])
                etree.SubElement(attach_item, "{%s}attachment_url" % NS_WP).text = etree.CDATA(image_val)
        for td in term_definitions:
            cat_el = etree.SubElement(course_item, "category", 
                                    domain=td['taxonomy'], 
                                    nicename=td['slug'],
                                    id=str(td['id']),
                                    parent="0",
                                    description="")
            cat_el.text = etree.CDATA(td['name'])

        items_to_generate = []
        questions_to_generate = []

        for idx_s, section in enumerate(self.course_data['sections']):
            sec_id = str(section_id_counter)
            section_el = etree.SubElement(course_item, "{%s}section" % NS_WP)
            etree.SubElement(section_el, "{%s}section_id" % NS_WP).text = sec_id
            etree.SubElement(section_el, "{%s}section_name" % NS_WP).text = section['title']
            etree.SubElement(section_el, "{%s}section_course_id" % NS_WP).text = course_id
            etree.SubElement(section_el, "{%s}section_order" % NS_WP).text = str(idx_s + 1)
            etree.SubElement(section_el, "{%s}section_description" % NS_WP).text = etree.CDATA(section.get('description', ''))

            for idx_i, item_data in enumerate(section['items']):
                item_id = str(id_counter)
                id_counter += 1
                
                sec_item_el = etree.SubElement(section_el, "{%s}section_item" % NS_WP)
                etree.SubElement(sec_item_el, "{%s}section_id" % NS_WP).text = sec_id
                etree.SubElement(sec_item_el, "{%s}item_id" % NS_WP).text = item_id
                etree.SubElement(sec_item_el, "{%s}item_order" % NS_WP).text = str(idx_i + 1)
                etree.SubElement(sec_item_el, "{%s}item_type" % NS_WP).text = item_data['type']

                if item_data['type'] == 'lp_quiz':
                    # Preparar Quiz Questions
                    quiz_questions = []
                    for q in item_data['questions']:
                        q_id = str(id_counter)
                        id_counter += 1
                        quiz_questions.append({'id': q_id, 'data': q})
                        questions_to_generate.append({'id': q_id, 'data': q})
                    
                    item_data['generated_id'] = item_id
                    item_data['generated_questions'] = quiz_questions
                else:
                    item_data['generated_id'] = item_id
                
                items_to_generate.append(item_data)

        # 2. Gerar Itens (Lessons / Quizzes)
        for gen_item in items_to_generate:
            item = etree.SubElement(channel, "item")
            etree.SubElement(item, "title").text = gen_item['title']
            etree.SubElement(item, "{%s}creator" % NS_DC).text = etree.CDATA(author_login)
            etree.SubElement(item, "{%s}post_id" % NS_WP).text = gen_item['generated_id']
            etree.SubElement(item, "{%s}post_date" % NS_WP).text = now_wp
            etree.SubElement(item, "{%s}status" % NS_WP).text = "publish"
            etree.SubElement(item, "{%s}post_type" % NS_WP).text = gen_item['type']
            etree.SubElement(item, "{%s}post_name" % NS_WP).text = self.slugify(gen_item['title'])

            if gen_item['type'] == 'lp_lesson':
                etree.SubElement(item, "{%s}encoded" % NS_CONTENT).text = etree.CDATA(gen_item['content'])
                # Duration
                dur = gen_item.get('duration', '10 minute').lower().replace('minutos', 'minute').replace('minuto', 'minute').replace('horas', 'hour').replace('hora', 'hour')
                pm = etree.SubElement(item, "{%s}postmeta" % NS_WP)
                etree.SubElement(pm, "{%s}meta_key" % NS_WP).text = "_lp_duration"
                etree.SubElement(pm, "{%s}meta_value" % NS_WP).text = etree.CDATA(dur)
            
            elif gen_item['type'] == 'lp_quiz':
                # Meta do Quiz
                meta_fields = {
                    '_lp_duration': gen_item['meta']['duration'].lower().replace('minutos', 'minute').replace('minuto', 'minute').replace('horas', 'hour').replace('hora', 'hour'),
                    '_lp_passing_grade': gen_item['meta']['passing_grade'],
                    '_lp_retake_count': gen_item['meta']['retake_count'],
                    '_lp_show_result': 'yes',
                    '_lp_show_check_answer': 'yes'
                }
                for k, v in meta_fields.items():
                    pm = etree.SubElement(item, "{%s}postmeta" % NS_WP)
                    etree.SubElement(pm, "{%s}meta_key" % NS_WP).text = k
                    etree.SubElement(pm, "{%s}meta_value" % NS_WP).text = etree.CDATA(v)
                
                # Perguntas do Quiz
                for idx_q, q_info in enumerate(gen_item['generated_questions']):
                    q_el = etree.SubElement(item, "{%s}question" % NS_WP)
                    etree.SubElement(q_el, "{%s}quiz_id" % NS_WP).text = gen_item['generated_id']
                    etree.SubElement(q_el, "{%s}question_id" % NS_WP).text = q_info['id']
                    etree.SubElement(q_el, "{%s}question_order" % NS_WP).text = str(idx_q + 1)

            # Atribuição Curso
            pm_c = etree.SubElement(item, "{%s}postmeta" % NS_WP)
            etree.SubElement(pm_c, "{%s}meta_key" % NS_WP).text = "_lp_course"
            etree.SubElement(pm_c, "{%s}meta_value" % NS_WP).text = etree.CDATA(course_id)

        # 3. Gerar Questões
        for q_gen in questions_to_generate:
            q_id = q_gen['id']
            q_data = q_gen['data']
            
            item = etree.SubElement(channel, "item")
            etree.SubElement(item, "title").text = q_data['title']
            etree.SubElement(item, "{%s}creator" % NS_DC).text = etree.CDATA(author_login)
            etree.SubElement(item, "{%s}encoded" % NS_CONTENT).text = etree.CDATA("")
            etree.SubElement(item, "{%s}post_id" % NS_WP).text = q_id
            etree.SubElement(item, "{%s}status" % NS_WP).text = "publish"
            etree.SubElement(item, "{%s}post_type" % NS_WP).text = "lp_question"
            etree.SubElement(item, "{%s}post_name" % NS_WP).text = self.slugify(q_data['title'])
            
            # Answers
            for ans in q_data['answers']:
                ans_el = etree.SubElement(item, "{%s}answer" % NS_WP)
                etree.SubElement(ans_el, "{%s}question_id" % NS_WP).text = q_id
                etree.SubElement(ans_el, "{%s}answer_title" % NS_WP).text = etree.CDATA(ans['title'])
                etree.SubElement(ans_el, "{%s}answer_value" % NS_WP).text = f"val_{q_id}_{ans['order']}"
                etree.SubElement(ans_el, "{%s}answer_order" % NS_WP).text = str(ans['order'])
                etree.SubElement(ans_el, "{%s}answer_is_true" % NS_WP).text = ans['is_true']

            # Postmeta Questão
            lp_type = q_data['type']
            if lp_type == 'fill_in_blanks': lp_type = 'single_choice'
            
            meta_q = {'_lp_type': lp_type, '_lp_explanation': q_data['explanation']}
            for k, v in meta_q.items():
                pm = etree.SubElement(item, "{%s}postmeta" % NS_WP)
                etree.SubElement(pm, "{%s}meta_key" % NS_WP).text = k
                etree.SubElement(pm, "{%s}meta_value" % NS_WP).text = etree.CDATA(v)

        # 4. Metadados do Curso (Final)
        total_mins = 0
        for section in self.course_data['sections']:
            for it in section['items']:
                d = ""
                if it['type'] == 'lp_lesson': d = it.get('duration', '')
                elif it['type'] == 'lp_quiz': d = it['meta'].get('duration', '')
                n = re.search(r'(\d+)', d)
                if n: total_mins += (int(n.group(1))*60) if 'hora' in d.lower() else int(n.group(1))

        technical_duration = f"{total_mins} minute" if total_mins > 0 else self.course_data['metadata'].get('Carga horária', '0 minute')
        technical_duration = technical_duration.lower().replace('horas', 'hour').replace('hora', 'hour').replace('minutos', 'minute').replace('minuto', 'minute')

        meta_mapping = {'Carga horária': '_lp_duration', 'Nível': '_lp_level', 'Formador(a)': '_lp_instructor'}
        for l, v in self.course_data['metadata'].items():
            k = meta_mapping.get(l)
            if k:
                if k == '_lp_duration': v = technical_duration
                pm = etree.SubElement(course_item, "{%s}postmeta" % NS_WP)
                etree.SubElement(pm, "{%s}meta_key" % NS_WP).text = k
                etree.SubElement(pm, "{%s}meta_value" % NS_WP).text = etree.CDATA(v)

        tree = etree.ElementTree(rss)
        tree.write(self.output_path, encoding='UTF-8', xml_declaration=True, pretty_print=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("arquivo_md")
    args = parser.parse_args()
    output_f = args.arquivo_md.rsplit(".", 1)[0] + ".xml"
    gen = LearnPressGenerator(args.arquivo_md, output_f)
    gen.parse_markdown()
    gen.generate_xml()
    print(f"✅ XML Gerado com sucesso em: {output_f}")
