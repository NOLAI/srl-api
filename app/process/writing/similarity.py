import html
import re
import pandas as pd
from tortoise import connections
from app.db.models import MdlPage
import spacy

nlp = spacy.load("nl_core_news_lg")

async def run(segmented_essays, course_id):
    content, instruction, rubric = await get_texts(course_id)

    doc_content = nlp(content)
    doc_instruction = nlp(instruction)
    doc_rubric = nlp(rubric)

    results = []
    for i, essay_segment in segmented_essays.iterrows():
        text = essay_segment['segment'].strip()
        if not text:
            continue
        text_written = essay_segment['text_written'].strip()
        if not text_written:
            continue

        doc_text = nlp(text)
        doc_text_written = nlp(text_written)

        result = {
            'cluster_nr': essay_segment['cluster_nr'],
            'overlap_content_text': 0.0 if not doc_content else doc_content.similarity(doc_text),
            'overlap_content_written_text': 0.0 if not doc_content else doc_content.similarity(doc_text_written),
            'overlap_instruction_text': 0.0 if not doc_instruction else doc_instruction.similarity(doc_text),
            'overlap_instruction_written_text': 0.0 if not doc_instruction else doc_instruction.similarity(doc_text_written),
            'overlap_rubric_text': 0.0 if not doc_rubric else doc_rubric.similarity(doc_text),
            'overlap_rubric_written_text': 0.0 if not doc_rubric else doc_rubric.similarity(doc_text_written),
        }
        results.append(result)

    return pd.DataFrame(results)

async def get_texts(course_id):
    db_moodle = connections.get('moodle')
    pages = await MdlPage.all(using_db=db_moodle).filter(course=course_id).order_by('id')
    content = ""
    instruction = ""
    rubric = ""
    for page in pages:
        page_content = re.sub(r'[\n\r]+', ' ', re.sub(r'\{GENERICO:type=[^}]+\}', '', re.sub(r'<[^>]+>', '', html.unescape(page.content)))).strip()
        if page.name.lower() == "instructie":
            instruction += page_content
        elif page.name.lower() == "beoordelingstabel":
            rubric += page_content
        else:
            content += page.name + " " + page_content + " "
    return content, instruction, rubric