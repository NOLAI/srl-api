import spacy
import re
from langdetect import detect_langs
import spacy.cli
import Levenshtein

PREAMBLES = {
    'nl': ["beste", "lieve", "hallo", "hoi"],
    'en': ["dear", "hi", "hello"],
}
CLOSE_GREETINGS  = {
    'nl': ["groetjes", "groeten", "tot ziens", "fijne dag", "fijn weekend"],
    'en': ["cheers", "goodbye", "have a nice day", "have a nice weekend", "best regards"],
}
PREPOSITIONS  = {
    "nl": ["van", "in", "op", "bij", "door", "voor", "met", "over", "als", "tot", "van", "tijdens", "de", "na", "en"],
    'en': ["of", "in", "on", "at", "by", "for", "with", "about", "as", "to", "from", "during", "the", "after", "and"],
}

MODELS = {
    'en': spacy.load('en_core_web_md'),
    'nl': spacy.load('nl_core_news_md'),
}

    
def load_language_model(essay, task):
    languages = detect_langs(essay)
    languages = {lang.lang: lang.prob for lang in languages if lang.lang in task and lang.lang in MODELS}
    language_code = max(languages, key=languages.get) if languages else list(task.keys())[0]
    model = MODELS.get(language_code)
    return model


def check_header_pattern(line, nlp, manual_preposition):
    if not bool(re.search(r'[.;,:]$', line)):
        if line.isupper() or re.match(r'^\d+(\.|:)', line) or line.istitle():
            return True
        doc = nlp(line)
        words_without_prepositions = [token.text for token in doc if not token.is_punct and token.text.lower() not in manual_preposition]
        for word in words_without_prepositions:
            if not word.istitle():
                return False
        return True
    else:
        return False


def clean_paragraph(text, nlp, manual_preposition):
    lines = text.split('\n')
    processed_paragraphs = []
    headers = []

    for i in range(len(lines)):
        current_line = lines[i].strip()

        if check_header_pattern(current_line, nlp, manual_preposition) and i!=len(lines)-1:
            headers.append(current_line)
        else:
            processed_paragraphs.append(current_line)
            processed_paragraphs.append(' ')

    return ''.join(processed_paragraphs), headers



def split_text(text, nlp, manual_preposition):
    paragraphs = []
    paragraph_sentences = []
    main_headers = []
    for paragraph in re.split(r'\n\s*\n',text.strip()):
        processed_paragraph, headers = clean_paragraph(paragraph, nlp, manual_preposition)
        paragraphs.append(processed_paragraph)

        if len(headers) > 0:
            main_headers.append(headers[0])
        doc = nlp(processed_paragraph)
        sentences = [sent.text.strip() for sent in doc.sents]
        paragraph_sentences.append(sentences)

    return paragraphs, paragraph_sentences, main_headers


def check_headers(paragraphs,expected_headers):
    detected_headers = []
    for paragraph in paragraphs:
        if paragraph.isupper():
            detected_headers.append(paragraph.strip())
    if detected_headers == expected_headers:
        return True
    return False


def check_headers_in_order(expected, actual):
    idx = 0
    for expected_header in expected:
        # Check if the expected header is found in the actual headers
        found = False
        while idx < len(actual):
            if expected_header.lower() in actual[idx].lower():  # Check if the expected text is contained
                found = True
                idx += 1  # Move to next header after finding a match
                break
            idx += 1
        if not found:
            return False  # If any header isn't found, return False
    return True


def has_preamble(paragraph, preambles):
    words_in_paragraph = re.findall(r'\b\w+\b', paragraph.lower())
    found_words = [word for word in preambles if word.lower() in words_in_paragraph]
    return bool(found_words)

def has_close_greeting(paragraph,close_greetings):
    found_close_greetings = []
    for greeting in close_greetings:
        # Escape special characters in the phrase and create a regex pattern
        pattern = r'\b' + re.escape(greeting.lower()) + r'\b'  # \b ensures word boundaries
        if re.search(pattern, paragraph.lower()):  # Check if phrase matches
            found_close_greetings.append(greeting)
    return bool(found_close_greetings)

def minimum_paragraph_length(paragraph):
    words_in_paragraph = re.findall(r'\b\w+\b', paragraph.lower())
    return len(words_in_paragraph) > 5

def check_paragraph_similarity(paragraph,background_texts,sim_threshold, nlp):
    paragraph_doc = nlp(paragraph)
    for source_text in background_texts:
        source_doc = nlp(source_text)
        paragraph_similarity = paragraph_doc.similarity(source_doc)
        if paragraph_similarity > sim_threshold:
            return True
    return False


def check_essay_structure(paragraphs, main_headers, task, nlp, sim_threshold = 0.4):
    structure_rules = {"starting_with_salutation": False,
                       "introduction_on_topic": False,
                       "minimum_number_of_paragraphs":False,
                       "with_headers_in_order":False,
                       "conclusion_on_topic":False,
                       "ending_with_greetings":False}

    num_paragraphs = len(paragraphs)
    num_main_paragraphs = num_paragraphs

    if num_paragraphs == 1:
        current_paragraph = paragraphs[0]
        # check if the paragraph contains any preamble words
        if has_preamble(current_paragraph, PREAMBLES[nlp.lang]):
            structure_rules["starting_with_salutation"] = True
        if minimum_paragraph_length(current_paragraph) and has_close_greeting(current_paragraph, CLOSE_GREETINGS[nlp.lang]):
            structure_rules["ending_with_greetings"] = True
    else:
        # check if the first paragraph is the preamble paragraph
        first_paragraph = paragraphs[0]
        first_as_preamble = False
        if has_preamble(first_paragraph, PREAMBLES[nlp.lang]):
            structure_rules["starting_with_salutation"] = True
            first_as_preamble = True
        elif not minimum_paragraph_length(first_paragraph):
            # if the first paragraph contains less than 10 words, it might attempt as preamble but failed
            first_as_preamble = True

        # if first paragraph is preamble paragraph, its next paragraph is the intro
        # else first paragraph is intro
        if first_as_preamble:
            intro_paragraph = paragraphs[1]
            num_main_paragraphs = num_paragraphs - 1
        else:
            intro_paragraph = paragraphs[0]

        structure_rules["introduction_on_topic"] = not check_paragraph_similarity(intro_paragraph, task['relevant_text'], sim_threshold, nlp)

        last_paragraph = paragraphs[-1]
        last_as_close_greeting = False

        if has_close_greeting(last_paragraph, CLOSE_GREETINGS[nlp.lang]):
            structure_rules["ending_with_greetings"] = True
            last_as_close_greeting = True
        elif not minimum_paragraph_length(last_paragraph):
            # if the first paragraph contains less than 10 words, it might attempt as preamble but failed
            last_as_close_greeting = True

        if last_as_close_greeting:
            conclusion_paragraph = paragraphs[-2]
            num_main_paragraphs = num_paragraphs - 1
        else:
            conclusion_paragraph = paragraphs[-1]

        #check if conclusion paragraph is not the same as  introduction paragraph or preamble
        if not (conclusion_paragraph == intro_paragraph or conclusion_paragraph == first_paragraph):
            structure_rules["conclusion_on_topic"] = not check_paragraph_similarity(conclusion_paragraph, task['relevant_text'], sim_threshold, nlp)

        if check_headers_in_order(task['expected_headers'], main_headers):
            structure_rules["with_headers_in_order"] = True

        if num_main_paragraphs >= task['minimum_number_of_paragraphs']:
            structure_rules["minimum_number_of_paragraphs"] = True

    return [{'name': k, 'completed': v} for k, v in structure_rules.items()]

def check_keywords(sentence, keywords_list):
    pattern = '|'.join(re.escape(keyword) for keyword in keywords_list)
    if re.search(pattern,sentence,re.IGNORECASE):
        return True
    return False


def check_paragraph_relevance(paragraphs, paragraph_sentences, task, nlp, sim_threshold = 0.4):
    # main_paragraph indicate the paragraphs that should be checked for relevance
    main_paragraphs = paragraphs
    main_paragraph_sentences = paragraph_sentences
    num_paragraphs = len(paragraphs)
    if num_paragraphs < 1:
        return []
    elif num_paragraphs == 1:
        current_paragraph = paragraphs[0]
        if minimum_paragraph_length(current_paragraph):
            num_main_paragraphs = 1
        else:
            num_main_paragraphs = 0
    else:
        first_paragraph = paragraphs[0]
        if has_preamble(first_paragraph, PREAMBLES[nlp.lang]) or not minimum_paragraph_length(first_paragraph):
            # when the first paragraph has Preambles, we treat its next as the first main paragraph
            # when the first paragraph has no Preambles but less than 10 words
            # it might indicate an attempt of preamble, in this case, we treat its next as the first main paragraph
            main_paragraphs = main_paragraphs[1:]
            main_paragraph_sentences = main_paragraph_sentences[1:]

        last_paragraph = main_paragraphs[-1]
        if has_close_greeting(last_paragraph, CLOSE_GREETINGS[nlp.lang]) or not minimum_paragraph_length(last_paragraph):
            if len(main_paragraphs) > 1:
                main_paragraphs = main_paragraphs[:-2]
                main_paragraph_sentences = main_paragraph_sentences[:-2]
            else:
                return []

        num_main_paragraphs = len(main_paragraph_sentences)

    if num_main_paragraphs > 0:
        paragraph_relevance = [False]*num_main_paragraphs
        for k in range(num_main_paragraphs):
            sentences = main_paragraph_sentences[k]
            num_sentences = len(sentences)
            sentence_relevance = [False]*num_sentences
            for i in range(num_sentences):
                sentence = sentences[i]
                if any(keyword.lower() in (sentence.text if hasattr(sentence, 'text') else sentence).lower() for keyword in task['keywords']):
                    sentence_relevance[i] = True
                else:
                    sent_doc = nlp(sentence)
                    for source_text in task["relevant_text"]:
                        source_doc = nlp(source_text)
                        if sent_doc.has_vector and source_doc.has_vector:
                            # Calculate similarity
                            sent_sim = sent_doc.similarity(source_doc)
                            # Check if similarity is above the threshold
                            if sent_sim > sim_threshold:
                                sentence_relevance[i] = True
                                break  # No need to check further source_texts if one similarity is sufficient
            relevance_count = sentence_relevance.count(True)
            if relevance_count >= num_sentences/2:
                paragraph_relevance[k] = True

        return paragraph_relevance
    return []

def check_phrase_in_doc(doc, phrase):
    """
    Check if a whole phrase exists in the doc.
    """
    # We will match the phrase as a whole (case-insensitive)
    return bool(re.search(re.escape(phrase), doc.text, flags=re.IGNORECASE)) 

def check_term_in_doc_fuzzy(doc, term):
    """
    Check if a single term exists in the doc.
    """
    # We will match the term in the document (case-insensitive)
    if(check_phrase_in_doc(doc, term)):
        return True

    doc_words = [token.text.lower for token in doc if not token.is_punct]
    min_distance = float('inf')
    for word in doc_words:
        distance = Levenshtein.distance(word, term.lower())
        if distance < min_distance:
            min_distance = distance
    if min_distance > 3:
        return False
    return True

def check_phrase_in_doc_fuzzy(doc, phrase):
    """
    Check if a whole phrase exists in the doc, accept typos.
    """
    if(check_phrase_in_doc(doc, phrase)): 
        return True

    # Extract words (tokens) from the doc
    doc_words = [token.text.lower() for token in doc if not token.is_punct]

    # Set the window size equal to the length of the query phrase (in words)
    window_size = len(phrase.split())  # split query_phrase into words to determine window size

    # Iterate over words and apply sliding window
    min_distance = float('inf')

    for i in range(len(doc_words) - window_size + 1):
        # Create window from words
        window = ' '.join(doc_words[i:i + window_size])

        # Compare window with query phrase using Levenshtein distance
        distance = Levenshtein.distance(window, phrase.lower())

        # Track the best match (with the minimum distance)
        if distance < min_distance:
            min_distance = distance

    if min_distance > 3: 
        return False
    return True




def check_multi_conditions(doc, condition):
    """
       Checks if a given condition is met in the provided SpaCy doc.
       Condition could be a phrase like "Blokkade van Berlijn" or a logical expression with AND/OR.
       """
    # Condition example: "Blokkade van Berlijn OR (Blokkade AND Berlijn)"
    # Step 1: Split by 'OR' (case-insensitive) and recursively process
    or_conditions = [sub_condition.strip() for sub_condition in re.split(r'\s+OR\s+', condition, flags=re.IGNORECASE)]

    for or_condition in or_conditions:
        if or_condition.startswith("(") and or_condition.endswith(")"):
            or_condition = or_condition[1:-1].strip()
        # Step 2: Handle each OR condition (it could be a single phrase or something with AND)

        # If there's an AND condition (like (Blokkade AND Berlijn)), split and check both terms.
        and_conditions = [sub_condition.strip() for sub_condition in
                          re.split(r'\s+AND\s+', or_condition, flags=re.IGNORECASE)]

        # Step 3: If there is no and in the current condition
        if len(and_conditions) == 1:
            # Check if the phrase as a whole exists in the document
            if check_phrase_in_doc_fuzzy(doc, and_conditions[0]):
                return True
        else:
            # Step 4: If it's multiple conditions joined by AND (like Blokkade AND Berlijn)
            if all(check_phrase_in_doc_fuzzy(doc, phrase) for phrase in and_conditions):
                return True

    return False


def check_main_points_addressed(essay, paragraphs, paragraph_sentences, task, nlp, sim_threshold=0.8):
    main_points_addressed = { main_point["topic"]: {'name': main_point["topic"], 'completed': False} for main_point in task['main_points']}

    main_paragraphs = paragraphs
    main_paragraph_sentences = paragraph_sentences
    num_paragraphs = len(paragraphs)
    if num_paragraphs < 1:
        return main_points_addressed
    elif num_paragraphs == 1:
        current_paragraph = paragraphs[0]
        if minimum_paragraph_length(current_paragraph):
            num_main_paragraphs = 1
        else:
            num_main_paragraphs = 0

    else:
        first_paragraph = paragraphs[0]

        if has_preamble(first_paragraph, PREAMBLES[nlp.lang]) or not minimum_paragraph_length(first_paragraph):
            # when the first paragraph has Preambles, we treat its next as the first main paragraph
            # when the first paragraph has no Preambles but less than 10 words
            # it might indicate an attempt of preamble, in this case, we treat its next as the first main paragraph
            main_paragraphs = main_paragraphs[1:]
            main_paragraph_sentences = main_paragraph_sentences[1:]

        last_paragraph = main_paragraphs[-1]
        if has_close_greeting(last_paragraph, CLOSE_GREETINGS[nlp.lang]):
            if len(main_paragraphs)>1:
                main_paragraphs = main_paragraphs[:-2]
                main_paragraph_sentences = main_paragraph_sentences[:-2]
            else:
                if not minimum_paragraph_length(last_paragraph):
                    return list(main_points_addressed.values())
        else:
            # # when the last paragraph has no greetings but less than 10 words
            # it might indicate an attempt of close greetings, in this case, we treat its previous one as the last main paragraph
            if not minimum_paragraph_length(last_paragraph):
                if len(main_paragraphs) > 1:
                    main_paragraphs = main_paragraphs[:-2]
                    main_paragraph_sentences = main_paragraph_sentences[:-2]
                else:
                    return list(main_points_addressed.values())


        num_main_paragraphs = len(main_paragraphs)

    if num_main_paragraphs > 0:
        sentence_dict = {}
        for i, sentences in enumerate(main_paragraph_sentences):
            for k, sentence in enumerate(sentences):
                sentence_dict["%d-%d"%(i,k)] = sentence

        doc_essay = nlp(essay)
        for main_point_item in task['main_points']:
            topic = main_point_item["topic"]
            keywords_main_point = main_point_item["keywords"]
            sentences_main_point = main_point_item["sentences"]

            keywords_covered = []
            for each_word in keywords_main_point:
                if check_multi_conditions(doc_essay, each_word):
                    keywords_covered.append(each_word)
            keywords_ratio = len(keywords_covered) / len(keywords_main_point) if len(keywords_main_point) > 0 else 1

            sentences_covered = []
            for sent_main_point in sentences_main_point:
                sent_main_point_nlp = nlp(sent_main_point)
                for sentence in sentence_dict.values():
                    sent_nlp = nlp(sentence)
                    sim_sent = sent_main_point_nlp.similarity(sent_nlp)
                    if sim_sent > sim_threshold:
                        sentences_covered.append(sent_main_point)
            sentences_ratio = len(sentences_covered) / len(sentences_main_point) if len(sentences_main_point) > 0 else 1

            if keywords_ratio >= 0.75 and sentences_ratio >= 1:
                main_points_addressed[topic]['completed'] = True

    return list(main_points_addressed.values())


def init_nlp(essay, task):
    nlp = load_language_model(essay, task)
    task = task[nlp.lang]

    nlp.Defaults.infixes += [r"’"]  # Add apostrophe to infixes to avoid splitting contractions
    # Apply custom tokenizer (SpaCy will use updated infixes)
    nlp.tokenizer = spacy.tokenizer.Tokenizer(nlp.vocab)

    return nlp, task

def process_essay(essay_content, task, nlp, sim_threshold=0.8):
    paragraphs, paragraph_sentences, main_headers = split_text(essay_content, nlp, PREPOSITIONS[nlp.lang])

    paragraph_relevance = check_paragraph_relevance(paragraphs, paragraph_sentences, task, nlp, sim_threshold)
    main_points_addressed = check_main_points_addressed(essay_content, paragraphs, paragraph_sentences, task, nlp, sim_threshold)
    structure_rules = check_essay_structure(paragraphs, main_headers, task, nlp, sim_threshold)

    return {
        'relevance': paragraph_relevance,
        'main_points': main_points_addressed,
        'structure': structure_rules,
    }

def process_essays(essays, task, sim_threshold=0.8):
    nlp, task = init_nlp(essays[-1]['content'], task)
    return [essay | process_essay(essay['content'], task, nlp, sim_threshold) for essay in essays]