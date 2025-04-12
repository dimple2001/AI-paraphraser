from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from dotenv import load_dotenv
import requests
import json
import traceback
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv('api.env')

app = Flask(__name__)

# Get HF API token from environment variables
HF_API_TOKEN = os.environ.get('HF_API_TOKEN', '')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/img/<path:filename>')
def serve_images(filename):
    # Create SVG content for note-edit.svg
    if filename == 'note-edit.svg':
        svg_content = '''
        <svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="60" height="60" rx="8" fill="#F5F5F5"/>
            <path d="M44 32V42C44 43.0609 43.5786 44.0783 42.8284 44.8284C42.0783 45.5786 41.0609 46 40 46H20C18.9391 46 17.9217 45.5786 17.1716 44.8284C16.4214 44.0783 16 43.0609 16 42V18C16 16.9391 16.4214 15.9217 17.1716 15.1716C17.9217 14.4214 18.9391 14 20 14H32" stroke="#F39C12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M40 14L46 20L34 32H28V26L40 14Z" stroke="#F39C12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M24 35H36" stroke="#F39C12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        '''
        return svg_content, 200, {'Content-Type': 'image/svg+xml'}
    
    # Serve other files from the static/img directory
    try:
        return send_from_directory('static/img', filename)
    except:
        # Return a default image or error response if file not found
        return "Image not found", 404

@app.route('/paraphrase', methods=['POST'])
def paraphrase():
    data = request.json
    text = data.get('text', '').strip()
    mode = data.get('mode', 'fluency')
    force_local = data.get('force_local', False)
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Character limit check
    if len(text) > 1500:
        return jsonify({'error': 'Text exceeds 1500 character limit'}), 400
    
    try:
        logging.info(f"Attempting to paraphrase: '{text[:50]}...' using mode: {mode}")
        
        # Use local paraphrasing if API token is missing, debug mode is on, or force_local is true
        if not HF_API_TOKEN or os.environ.get('DEBUG_MODE', 'False').lower() == 'true' or force_local:
            logging.info("Using local paraphrasing (no API call)")
            paraphrased = get_local_paraphrase(text, mode)
        else:
            # Try API call first, fall back to local if it fails
            try:
                paraphrased = get_paraphrase_from_api(text, mode)
                logging.info(f"API paraphrasing result: '{paraphrased[:50]}...'")
            except Exception as api_error:
                logging.warning(f"API paraphrasing failed: {str(api_error)}. Falling back to local.")
                paraphrased = get_local_paraphrase(text, mode)
            
        # Validate result - ensure we got a valid string
        if not isinstance(paraphrased, str) or not paraphrased.strip():
            logging.warning("Invalid paraphrase result, using local fallback")
            paraphrased = get_local_paraphrase(text, mode)
            
        # Clean and format text - modified to avoid NLTK issues
        paraphrased = clean_and_format_text(paraphrased)
        
        # Final quality check
        if len(paraphrased) < 5 or paraphrased == text:
            logging.warning("Final result invalid or identical to input, using fallback")
            paraphrased = get_local_paraphrase(text, mode)
            paraphrased = clean_and_format_text(paraphrased)
            
        logging.info(f"Final paraphrased result: '{paraphrased[:50]}...'")
        
        return jsonify({
            'result': paraphrased,
            'mode': mode,
            'source': 'api' if not force_local and HF_API_TOKEN else 'local'
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        logging.error(f"Paraphrasing error: {str(e)}")
        logging.error(f"Traceback: {error_trace}")
        
        # Last resort fallback - if everything else fails
        try:
            emergency_result = get_local_paraphrase(text, 'fluency')  # Default to fluency mode
            return jsonify({
                'result': emergency_result,
                'mode': mode,
                'source': 'emergency_fallback'
            })
        except:
            return jsonify({
                'error': f'Paraphrasing error: {str(e)}',
                'detail': error_trace
            }), 500

def clean_and_format_text(text):
    """
    Clean and format text without using NLTK to avoid dependency issues
    """
    if not text:
        return ""
    
    # Simple sentence splitting using regex
    sentences = re.split(r'([.!?]+\s+)', text)
    
    # Rejoin sentences with proper capitalization
    result = ""
    for i in range(0, len(sentences), 2):
        if i < len(sentences):
            sentence = sentences[i].strip()
            if sentence:
                # Capitalize first letter
                sentence = sentence[0].upper() + sentence[1:] if sentence and len(sentence) > 0 else ""
                result += sentence
                
                # Add ending punctuation if available
                if i + 1 < len(sentences):
                    result += sentences[i + 1]
                elif not result.endswith(('.', '!', '?')):
                    result += '.'
    
    # Handle case where the split didn't work as expected
    if not result:
        result = text.strip()
        if result and not result[-1] in '.!?':
            result += '.'
    
    # Fix common grammatical issues
    result = re.sub(r'\s+([.,;:!?])', r'\1', result)  # Remove spaces before punctuation
    result = re.sub(r'\.{2,}', '...', result)  # Standardize ellipses
    result = re.sub(r'\s{2,}', ' ', result)  # Remove extra spaces
    
    return result.strip()

def get_local_paraphrase(text, mode):
    """
    Improved local paraphrasing with better text transformation
    """
    import re
    import random
    
    # Strip and get basic text properties
    text = text.strip()
    
    if mode == 'fluency':
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        result = []
        
        # Enhanced word replacement dictionary
        synonyms = {
            'method': ['approach', 'technique', 'procedure', 'strategy'],
            'analysis': ['examination', 'assessment', 'evaluation', 'study'],
            'automates': ['streamlines', 'simplifies', 'mechanizes', 'expedites'],
            'building': ['development', 'construction', 'creation', 'formation'],
            'branch': ['field', 'area', 'domain', 'sector'],
            'idea': ['concept', 'notion', 'principle', 'theory'],
            'systems': ['programs', 'frameworks', 'structures', 'arrangements'],
            'learn': ['acquire knowledge', 'gain understanding', 'comprehend', 'grasp'],
            'identify': ['recognize', 'detect', 'pinpoint', 'discover'],
            'patterns': ['structures', 'arrangements', 'configurations', 'frameworks'],
            'decisions': ['determinations', 'conclusions', 'judgments', 'choices'],
            'minimal': ['limited', 'minor', 'slight', 'negligible'],
            'make': ['produce', 'generate', 'create', 'form'],
            'based on': ['founded on', 'grounded in', 'derived from', 'rooted in'],
            'allows': ['enables', 'permits', 'facilitates', 'makes possible'],
            'important': ['significant', 'crucial', 'essential', 'vital'],
            'shows': ['demonstrates', 'indicates', 'reveals', 'illustrates'],
            'uses': ['utilizes', 'employs', 'applies', 'leverages']
        }
        
        linking_phrases = [
            ", moreover, ", 
            ". Additionally, ", 
            ". Furthermore, ", 
            "; consequently, ", 
            ". As a result, "
        ]
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            # Actual transformation of sentence structure
            words = sentence.split()
            if len(words) <= 3:
                result.append(sentence)  # Keep very short sentences as is
                continue
                
            # Rearrange clauses or restructure sentence
            modified_sentence = sentence
            
            # Apply different transformations based on sentence complexity
            if ',' in sentence:
                parts = sentence.split(',', 1)
                if len(parts) > 1:
                    # 50% chance to swap clauses around commas
                    if random.random() > 0.5:
                        modified_sentence = f"{parts[1].strip()}, {parts[0].strip()}"
            
            # Replace words with synonyms (improved version)
            for word, replacements in synonyms.items():
                if word in modified_sentence.lower():
                    # Get word with correct capitalization from original text
                    pattern = re.compile(re.escape(word), re.IGNORECASE)
                    matches = pattern.finditer(modified_sentence)
                    
                    for match in matches:
                        # Only 70% chance to replace to avoid over-substitution
                        if random.random() > 0.3:
                            original = match.group(0)
                            replacement = random.choice(replacements)
                            
                            # Maintain original capitalization
                            if original[0].isupper():
                                replacement = replacement[0].upper() + replacement[1:]
                                
                            # Replace just this instance
                            modified_sentence = modified_sentence[:match.start()] + replacement + modified_sentence[match.end():]
                            break  # Limit to one replacement per word type per sentence
            
            # For longer text, sometimes combine consecutive short sentences
            if i < len(sentences) - 1 and len(modified_sentence.split()) < 8 and len(sentences[i+1].split()) < 8:
                if random.random() > 0.7:  # 30% chance to combine
                    next_sent = sentences[i+1] if i+1 < len(sentences) else ""
                    if next_sent:
                        linking = random.choice(linking_phrases)
                        # Skip this sentence and combine with next
                        modified_sentence = modified_sentence.rstrip('.!?') + linking + next_sent.lstrip()
                        sentences[i+1] = ""  # Mark next sentence as processed
            
            result.append(modified_sentence)
                
        return ' '.join(result)
    
    elif mode == 'academic':
        # More academic vocabulary with multiple alternatives
        academic_terms = {
            'show': ['demonstrate', 'indicate', 'illustrate', 'elucidate'],
            'think': ['postulate', 'hypothesize', 'theorize', 'conceptualize'],
            'use': ['utilize', 'employ', 'implement', 'apply'],
            'make': ['construct', 'formulate', 'develop', 'synthesize'],
            'find': ['determine', 'ascertain', 'identify', 'establish'],
            'look': ['examine', 'investigate', 'analyze', 'scrutinize'],
            'help': ['facilitate', 'enhance', 'contribute to', 'enable'],
            'but': ['however', 'nevertheless', 'nonetheless', 'conversely'],
            'so': ['consequently', 'therefore', 'thus', 'hence'],
            'give': ['provide', 'furnish', 'offer', 'present'],
            'tell': ['indicate', 'communicate', 'convey', 'articulate'],
            'end': ['conclude', 'finalize', 'terminate', 'culminate'],
            'start': ['initiate', 'commence', 'begin', 'instigate'],
            'get': ['obtain', 'acquire', 'procure', 'attain'],
            'idea': ['concept', 'notion', 'hypothesis', 'proposition'],
            'said': ['stated', 'articulated', 'asserted', 'posited'],
            'learn': ['acquire knowledge', 'assimilate information', 'comprehend', 'apprehend'],
            'think about': ['consider', 'contemplate', 'deliberate on', 'reflect upon'],
            'method': ['methodology', 'approach', 'framework', 'paradigm']
        }
        
        academic_phrases = [
            "It is evident that ", 
            "Research indicates that ",
            "It can be observed that ", 
            "This analysis demonstrates that ",
            "The evidence suggests that ",
            "It is important to note that ",
            "Studies have shown that ",
            "Current scholarship emphasizes that "
        ]
        
        connectors = [
            "Furthermore, ", 
            "Moreover, ", 
            "In addition, ", 
            "Subsequently, ", 
            "Nevertheless, ", 
            "Consequently, "
        ]
        
        academic_text = text
        
        # Replace common words with academic alternatives
        for common, academic_list in academic_terms.items():
            pattern = re.compile(r'\b' + re.escape(common) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(academic_text))
            
            # Process matches in reverse to avoid position shifting
            for match in reversed(matches):
                if random.random() > 0.3:  # 70% chance to replace
                    original = match.group(0)
                    replacement = random.choice(academic_list)
                    
                    # Maintain original capitalization
                    if original[0].isupper():
                        replacement = replacement[0].upper() + replacement[1:]
                    
                    academic_text = academic_text[:match.start()] + replacement + academic_text[match.end():]
        
        # Split into sentences for structural changes
        sentences = re.split(r'(?<=[.!?])\s+', academic_text)
        result = []
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            modified = sentence
            
            # Add academic framing to some sentences
            if i == 0 or random.random() > 0.7:  # First sentence or 30% chance
                if not any(sentence.lower().startswith(term.lower()) for term in academic_phrases + connectors):
                    prefix = random.choice(academic_phrases if i == 0 else connectors)
                    modified = prefix + sentence[0].lower() + sentence[1:]
            
            result.append(modified)
            
        return ' '.join(result)
    
    elif mode == 'simple':
        # Simplify vocabulary with multiple alternatives
        simple_words = {
            'utilize': ['use', 'work with'],
            'implementation': ['use', 'putting to work'],
            'demonstrate': ['show', 'prove'],
            'facilitate': ['help', 'make easier'],
            'nevertheless': ['but', 'still'],
            'consequently': ['so', 'because of this'],
            'subsequently': ['then', 'after that'],
            'approximately': ['about', 'around'],
            'sufficient': ['enough', 'plenty'],
            'numerous': ['many', 'lots of'],
            'initiate': ['start', 'begin'],
            'terminate': ['end', 'stop'],
            'endeavor': ['try', 'attempt'],
            'ascertain': ['find out', 'learn'],
            'comprehend': ['understand', 'get'],
            'methodology': ['method', 'way'],
            'formulation': ['making', 'creating'],
            'conceptualize': ['think of', 'imagine'],
            'modification': ['change', 'fix'],
            'prioritize': ['focus on', 'put first'],
            'acquisition': ['getting', 'buying']
        }
        
        # Replace complex words with simpler ones
        simple_text = text
        for complex_word, simple_alternatives in simple_words.items():
            pattern = re.compile(r'\b' + re.escape(complex_word) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(simple_text))
            
            for match in reversed(matches):
                original = match.group(0)
                replacement = random.choice(simple_alternatives)
                
                # Maintain original capitalization
                if original[0].isupper():
                    replacement = replacement[0].upper() + replacement[1:]
                    
                simple_text = simple_text[:match.start()] + replacement + simple_text[match.end():]
        
        # Simplify common complex phrases
        phrase_replacements = [
            ("due to the fact that", "because"),
            ("in order to", "to"),
            ("for the purpose of", "for"),
            ("in the event that", "if"),
            ("on the grounds that", "because"),
            ("in spite of the fact that", "although"),
            ("with regard to", "about"),
            ("in the neighborhood of", "about"),
            ("it is crucial that", "we need to"),
            ("it is necessary that", "we need to"),
            ("under circumstances in which", "when"),
            ("in the final analysis", "finally"),
            ("with the exception of", "except for")
        ]
        
        for complex_phrase, simple_phrase in phrase_replacements:
            simple_text = re.sub(r'\b' + re.escape(complex_phrase) + r'\b', simple_phrase, simple_text, flags=re.IGNORECASE)
        
        # Break down long sentences
        sentences = re.split(r'(?<=[.!?])\s+', simple_text)
        simplified_sentences = []
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            s = sentence.strip()
            
            # Break long sentences with multiple clauses
            if len(s.split()) > 12 and ("," in s or ";" in s or "and" in s or "but" in s):
                parts = re.split(r'[,;]|(?<=\w)\s+(?:and|but|or)\s+(?=\w)', s)
                for i, part in enumerate(parts):
                    if part.strip():
                        part = part.strip()
                        if i > 0 and not any(part.lower().startswith(word) for word in ["and", "or", "but", "nor", "yet", "so"]):
                            # Add simple connector to fragments
                            if random.random() > 0.5:
                                part = f"Also, {part[0].lower()}{part[1:]}" if part else ""
                            elif random.random() > 0.5:
                                part = f"Then, {part[0].lower()}{part[1:]}" if part else ""
                        
                        # Ensure the sentence has proper punctuation
                        if not part.endswith(('.', '!', '?')):
                            part += '.'
                        
                        simplified_sentences.append(part)
            else:
                # Ensure the sentence has proper punctuation
                if not s.endswith(('.', '!', '?')):
                    s += '.'
                simplified_sentences.append(s)
            
        return ' '.join(simplified_sentences)
    
    elif mode == 'creative':
        # More interesting creative transformation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        creative_sentences = []
        
        # Creative transformation patterns
        metaphors = [
            "Like {subject} dancing through {object}",
            "{subject} weaves through {object} like a river through mountains",
            "As {subject} illuminates {object}, new understanding emerges",
            "When {subject} meets {object}, magic happens",
            "The {subject} that intertwines with {object} creates a tapestry of insight",
            "{subject} and {object} blend together in a symphony of ideas",
            "Just as stars guide travelers, {subject} guides us through the maze of {object}"
        ]
        
        descriptive_adjectives = [
            "fascinating", "illuminating", "intricate", "profound", "mesmerizing", 
            "thought-provoking", "insightful", "captivating", "remarkable", "exquisite"
        ]
        
        subjects = ['knowledge', 'technology', 'science', 'learning', 'intelligence', 'wisdom', 'understanding']
        objects = ['data', 'information', 'patterns', 'systems', 'concepts', 'discoveries', 'innovations']
        
        # Extract potential subjects and objects from the text
        text_words = text.lower().split()
        for word in text_words:
            if len(word) > 4 and word.isalpha():
                if len(subjects) < 10:  # Limit list size
                    subjects.append(word)
                if len(objects) < 10:
                    objects.append(word)
        
        # Add a creative opening
        if len(sentences) > 0:
            # Choose random subject and object
            subj = random.choice(subjects)
            obj = random.choice(objects)
            
            # Create metaphorical opening
            metaphor = random.choice(metaphors).format(subject=subj, object=obj)
            creative_sentences.append(f"{metaphor}, {sentences[0][0].lower()}{sentences[0][1:]}")
            
            # Process remaining sentences with varied structures
            for i in range(1, len(sentences)):
                sentence = sentences[i]
                if not sentence.strip():
                    continue
                    
                modified = sentence
                
                # Apply different creative transformations
                transform_type = random.randint(0, 3)
                
                if transform_type == 0 and len(sentence.split()) > 5:
                    # Invert sentence structure
                    words = sentence.split()
                    half = len(words) // 2
                    modified = ' '.join(words[half:]) + ' ' + ' '.join(words[:half])
                    
                elif transform_type == 1:
                    # Add descriptive adjectives
                    adj = random.choice(descriptive_adjectives)
                    words = sentence.split()
                    if len(words) > 3:
                        insert_pos = random.randint(1, min(3, len(words)-1))
                        words.insert(insert_pos, adj)
                        modified = ' '.join(words)
                        
                elif transform_type == 2 and "," in sentence:
                    # Add rhetorical flourish after comma
                    parts = sentence.split(",", 1)
                    rhetorical = random.choice([
                        " like a hidden gem,",
                        " unfolding with elegance,",
                        " revealing its secrets,",
                        " dancing with possibilities,"
                    ])
                    modified = parts[0] + rhetorical + parts[1] if len(parts) > 1 else parts[0]
                
                creative_sentences.append(modified)
                    
            # Add a creative conclusion if original text is substantial
            if len(text) > 100:
                conclusions = [
                    "This interplay of ideas creates a fascinating tapestry of possibilities.",
                    "Such insights open doors to worlds previously unimagined.",
                    "In this dance of concepts, we discover new horizons of understanding.",
                    "The beauty lies in how these elements harmonize into a greater whole."
                ]
                creative_sentences.append(random.choice(conclusions))
                
            return ' '.join(creative_sentences)
        else:
            return text
    
    # Default transformation if mode is not recognized
    return text

def get_paraphrase_from_api(text, mode):
    """
    Improved API function for better integration with models
    """
    # Model selection based on mode
    if mode == 'fluency':
        model = "tuner007/pegasus_paraphrase"
        params = {"temperature": 0.7, "max_length": 150}  # Changed max_new_tokens to max_length
        prepared_text = f"{text}"  # No prefix needed
    elif mode == 'academic':
        model = "facebook/bart-large-cnn"
        params = {"temperature": 0.8, "max_length": 150}  # Changed parameter
        prepared_text = f"Transform into academic language: {text}"
    elif mode == 'simple':
        model = "facebook/bart-large-xsum"
        params = {"temperature": 0.6, "max_length": 120}  # Changed parameter
        prepared_text = f"Simplify: {text}"
    elif mode == 'creative':
        model = "gpt2"
        params = {"temperature": 0.9, "max_length": 200}  # Changed parameter
        prepared_text = f"Create an imaginative version of: {text}"
    else:
        # Default to fluency
        model = "tuner007/pegasus_paraphrase"
        params = {"temperature": 0.7, "max_length": 150}  # Changed parameter
        prepared_text = f"{text}"
    
    logging.info(f"Using model: {model} with params: {params}")
    
    # API call to Hugging Face Inference API
    API_URL = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}
    
    # Include model parameters in the payload
    payload = {
        "inputs": prepared_text,
        "parameters": params,
        "options": {"wait_for_model": True}  # Added to wait for model to load if needed
    }
    
    logging.info(f"Sending request to {API_URL} (attempt 1/3)")
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)  # Increased timeout
            
            # Handle the case when model is still loading
            if response.status_code == 503 and "loading" in response.text.lower():
                if attempt < max_retries:
                    logging.info(f"Model is loading. Waiting before retry {attempt+1}/3...")
                    import time
                    time.sleep(10)  # Longer wait for model loading
                    continue
            
            if response.status_code == 200:
                break
            
            if attempt < max_retries:
                logging.warning(f"Attempt {attempt} failed with status {response.status_code}. Retrying...")
                import time
                time.sleep(2)  # Wait before retry
            else:
                logging.error(f"API request failed with status code {response.status_code}: {response.text[:200]}")
                raise Exception(f"API request failed with status code {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                logging.warning(f"Request exception on attempt {attempt}: {str(e)}. Retrying...")
                import time
                time.sleep(2)  # Wait before retry
            else:
                logging.error(f"All API request attempts failed: {str(e)}")
                raise Exception(f"API connection error: {str(e)}")
    
    # Parse the API response
    try:
        result = response.json()
        logging.info(f"API response format: {type(result).__name__}")
    except json.JSONDecodeError:
        logging.error(f"Failed to parse JSON response: {response.text[:200]}")
        raise Exception("Failed to parse API response")
    
    # Better handling of different API response formats
    paraphrased_text = None
    
    try:
        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], dict):
                    # Handle pegasus_paraphrase format
                    if "generated_text" in result[0]:
                        paraphrased_text = result[0]["generated_text"]
                    # Handle bart format
                    elif "summary_text" in result[0]:
                        paraphrased_text = result[0]["summary_text"]
                    # Handle other potential formats
                    elif "translation" in result[0]:
                        paraphrased_text = result[0]["translation"]
                    elif "text" in result[0]:
                        paraphrased_text = result[0]["text"]
                elif isinstance(result[0], str):
                    paraphrased_text = result[0]
        elif isinstance(result, dict):
            # Handle dictionary response format
            if "generated_text" in result:
                paraphrased_text = result["generated_text"]
            elif "translation_text" in result:
                paraphrased_text = result["translation_text"]
            elif "output" in result:
                paraphrased_text = result["output"]
            elif "text" in result:
                paraphrased_text = result["text"]
        
        # If it's still None, check for other nested formats
        if paraphrased_text is None and isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, dict) and "text" in value:
                    paraphrased_text = value["text"]
                    break
    except Exception as e:
        logging.error(f"Error parsing API response: {e}")
        logging.error(f"Response content: {str(result)[:500]}")
        raise Exception(f"Failed to parse API response: {str(e)}")
    
    # If we got a valid result, return it after cleaning
    if paraphrased_text:
        # Clean up the result - remove any prefix instructions
        common_prefixes = [
            "paraphrase:", "Paraphrase:", 
            "Transform into academic language:", 
            "Simplify:", "Create an imaginative version of:"
        ]
        for prefix in common_prefixes:
            if paraphrased_text.startswith(prefix):
                paraphrased_text = paraphrased_text[len(prefix):].strip()
        
        # If result is just a greeting or very short, replace with a better paraphrase
        if (paraphrased_text.lower().startswith(("hi", "hello", "greetings")) or 
            len(paraphrased_text) < 10 or
            len(paraphrased_text.split()) < 3):
            logging.warning("API returned too short response, falling back to local")
            return get_local_paraphrase(text, mode)
        
        # If the result is overly similar to the input, try local paraphrasing
        if paraphrased_text.lower() == text.lower() or similarity_score(text, paraphrased_text) > 0.9:
            logging.warning("API returned nearly identical text, falling back to local")
            return get_local_paraphrase(text, mode)
            
        return paraphrased_text
    
    # If we couldn't parse the result, fall back to local paraphrasing
    logging.warning("Could not extract text from API result, using local paraphrasing instead")
    return get_local_paraphrase(text, mode)


def similarity_score(text1, text2):
    """Simple similarity check between two texts"""
    # Convert to lowercase
    text1 = text1.lower()
    text2 = text2.lower()
    
    # Simple word overlap measure
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    # Calculate Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0
        
    return len(intersection) / len(union)

@app.route('/modes', methods=['GET'])
def get_modes():
    """Return available paraphrasing modes"""
    modes = [
        {"id": "fluency", "name": "Fluency", "description": "Improve flow and natural language"},
        {"id": "academic", "name": "Academic", "description": "Transform to scholarly and formal style"},
        {"id": "simple", "name": "Simple", "description": "Convert to clear, easy-to-understand language"},
        {"id": "creative", "name": "Creative", "description": "Add expressive flair and imaginative elements"}
    ]
    return jsonify(modes)


@app.route('/api-status', methods=['GET'])
def api_status():
    """Check if the API token is configured correctly"""
    has_token = bool(HF_API_TOKEN)
    return jsonify({
        "api_configured": has_token,
        "using_local_fallback": not has_token or os.environ.get('DEBUG_MODE', 'False').lower() == 'true'
    })


if __name__ == '__main__':
    # Download NLTK resources - removed dependency on punkt_tab
    try:
        import nltk
        nltk.download('punkt')
    except Exception as e:
        logging.warning(f"Failed to download NLTK resources: {e}")
    
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logging.info(f"Starting Flask app on port {port}, debug={debug}")
    logging.info(f"HF API Token present: {'Yes' if HF_API_TOKEN else 'No'}")
    logging.info(f"Using local fallback: {'Yes' if not HF_API_TOKEN or debug else 'Only if API fails'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)