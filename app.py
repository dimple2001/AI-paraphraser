from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from dotenv import load_dotenv
import requests
import json
import traceback
import re

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
    text = data.get('text', '')
    mode = data.get('mode', 'fluency')
    force_local = data.get('force_local', False)
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Character limit check
    if len(text) > 1500:
        return jsonify({'error': 'Text exceeds 1500 character limit'}), 400
    
    try:
        print(f"Attempting to paraphrase: '{text}' using mode: {mode}")
        
        # Use local paraphrasing if API token is missing, debug mode is on, or force_local is true
        if not HF_API_TOKEN or os.environ.get('DEBUG_MODE', 'False').lower() == 'true' or force_local:
            print("Using local paraphrasing (no API call)")
            paraphrased = get_local_paraphrase(text, mode)
        else:
            # Try API call first, fall back to local if it fails
            try:
                paraphrased = get_paraphrase_from_api(text, mode)
                print(f"API paraphrasing result: '{paraphrased}'")
            except Exception as api_error:
                print(f"API paraphrasing failed: {str(api_error)}. Falling back to local.")
                paraphrased = get_local_paraphrase(text, mode)
            
        # Validate result - ensure we got a valid string
        if not isinstance(paraphrased, str) or not paraphrased.strip():
            print("Invalid paraphrase result, using local fallback")
            paraphrased = get_local_paraphrase(text, mode)
            
        print(f"Final paraphrased result: '{paraphrased}'")
        
        return jsonify({
            'result': paraphrased,
            'mode': mode
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Paraphrasing error: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({
            'error': f'Paraphrasing error: {str(e)}',
            'detail': error_trace
        }), 500


def get_local_paraphrase(text, mode):
    """
    Improved local paraphrasing with better text transformation
    """
    import re
    # Strip and get basic text properties
    text = text.strip()
    
    if mode == 'fluency':
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        result = []
        
        for sentence in sentences:
            # Actual transformation of sentence structure
            words = sentence.split()
            if len(words) <= 3:
                result.append(sentence)  # Keep very short sentences as is
                continue
                
            # Rearrange clauses or restructure sentence 
            if ',' in sentence:
                parts = sentence.split(',', 1)
                if len(parts) > 1:
                    # Swap clauses around commas
                    result.append(f"{parts[1].strip()}, {parts[0].strip()}")
                    continue
            
            # Substitute synonyms for common words
            synonyms = {
                'method': 'approach', 'analysis': 'examination', 'automates': 'streamlines',
                'building': 'development', 'branch': 'field', 'idea': 'concept',
                'systems': 'programs', 'learn': 'acquire knowledge', 'identify': 'recognize',
                'patterns': 'structures', 'decisions': 'determinations',
                'minimal': 'limited', 'make': 'produce', 'based on': 'founded on'
            }
            
            new_sentence = sentence
            for word, replacement in synonyms.items():
                # Only replace once to avoid over-substitution
                if word in new_sentence.lower():
                    # Case-sensitive replacement
                    pattern = re.compile(re.escape(word), re.IGNORECASE)
                    new_sentence = pattern.sub(replacement, new_sentence, 1)
                    break  # Only apply one substitution per sentence
                    
            result.append(new_sentence)
                
        return ' '.join(result)
    
    elif mode == 'academic':
        # More academic vocabulary
        academic_terms = {
            'show': 'demonstrate', 'think': 'postulate', 'use': 'utilize', 'make': 'construct',
            'find': 'determine', 'look': 'examine', 'help': 'facilitate', 'but': 'however',
            'so': 'consequently', 'give': 'provide', 'tell': 'indicate', 'end': 'conclude',
            'start': 'initiate', 'get': 'obtain', 'idea': 'concept', 'said': 'stated',
            'learn': 'acquire', 'think about': 'consider', 'method': 'methodology'
        }
        
        academic_text = text
        for common, academic in academic_terms.items():
            pattern = re.compile(r'\b' + re.escape(common) + r'\b', re.IGNORECASE)
            academic_text = pattern.sub(academic, academic_text)
        
        # Add academic sentence structure
        sentences = re.split(r'(?<=[.!?])\s+', academic_text)
        result = []
        
        for i, sentence in enumerate(sentences):
            if i == 0 and not any(sentence.lower().startswith(term) for term in ['research', 'evidence', 'studies', 'analysis']):
                sentence = f"Research indicates that {sentence[0].lower()}{sentence[1:]}"
            result.append(sentence)
            
        return ' '.join(result)
    
    elif mode == 'simple':
        # Simplify vocabulary
        simple_words = {
            'utilize': 'use', 'implementation': 'use', 'demonstrate': 'show',
            'facilitate': 'help', 'nevertheless': 'but', 'consequently': 'so',
            'subsequently': 'then', 'approximately': 'about', 'sufficient': 'enough',
            'numerous': 'many', 'initiate': 'start', 'terminate': 'end',
            'endeavor': 'try', 'ascertain': 'find out', 'comprehend': 'understand',
            'methodology': 'method', 'formulation': 'making', 'conceptualize': 'think of',
            'modification': 'change', 'prioritize': 'focus on', 'acquisition': 'getting'
        }
        
        # Replace complex words with simpler ones
        simple_text = text
        for complex_word, simple_word in simple_words.items():
            pattern = re.compile(r'\b' + re.escape(complex_word) + r'\b', re.IGNORECASE)
            simple_text = pattern.sub(simple_word, simple_text)
        
        # Simplify sentence structure
        sentences = re.split(r'(?<=[.!?])\s+', simple_text)
        simplified_sentences = []
        
        for sentence in sentences:
            if sentence.strip():
                # Apply structural simplification to each sentence
                s = sentence.strip()
                # Simplify common complex phrases
                s = s.replace("due to the fact that", "because")
                s = s.replace("in order to", "to")
                s = s.replace("for the purpose of", "for")
                s = s.replace("in the event that", "if")
                s = s.replace("on the grounds that", "because")
                
                # Break long sentences with multiple clauses
                if len(s.split()) > 15 and ("," in s or ";" in s):
                    parts = re.split(r'[,;]', s)
                    for i, part in enumerate(parts):
                        if part.strip():
                            part = part.strip()
                            if i > 0 and not any(part.lower().startswith(word) for word in ["and", "or", "but", "nor", "yet", "so"]):
                                part = f"Also, {part[0].lower()}{part[1:]}" if i == 1 else part
                            simplified_sentences.append(part)
                else:
                    simplified_sentences.append(s)
            
        result = '. '.join(simplified_sentences)
        if not result.endswith('.') and not result.endswith('!') and not result.endswith('?'):
            result += '.'
                
        return result
    
    elif mode == 'creative':
        # More interesting creative transformation
        # Add metaphors and varied sentence structures
        sentences = re.split(r'(?<=[.!?])\s+', text)
        creative_sentences = []
        
        metaphors = [
            "Like {subject} dancing through {object}",
            "{subject} weaves through {object} like a river through mountains",
            "As {subject} illuminates {object}, new understanding emerges",
            "When {subject} meets {object}, magic happens"
        ]
        
        subjects = ['knowledge', 'technology', 'science', 'learning', 'intelligence']
        objects = ['data', 'information', 'patterns', 'systems', 'concepts']
        
        # Extract potential subjects and objects from the text
        text_words = text.lower().split()
        for word in text_words:
            if len(word) > 4 and word.isalpha():
                if len(subjects) < 8:  # Limit list size
                    subjects.append(word)
                if len(objects) < 8:
                    objects.append(word)
        
        # Add a creative opening
        if len(sentences) > 0:
            # Choose random subject and object
            import random
            subj = random.choice(subjects)
            obj = random.choice(objects)
            
            # Create metaphorical opening
            metaphor = random.choice(metaphors).format(subject=subj, object=obj)
            creative_sentences.append(f"{metaphor}, {sentences[0][0].lower()}{sentences[0][1:]}")
            
            # Process remaining sentences with varied structures
            for i in range(1, len(sentences)):
                sentence = sentences[i]
                if i % 2 == 0 and sentence.strip():
                    # Invert sentence structure occasionally
                    words = sentence.split()
                    if len(words) > 5:
                        half = len(words) // 2
                        creative_sentences.append(' '.join(words[half:]) + ' ' + ' '.join(words[:half]))
                    else:
                        creative_sentences.append(sentence)
                else:
                    creative_sentences.append(sentence)
                    
            # Add a creative conclusion if original text is substantial
            if len(text) > 100:
                creative_sentences.append("This interplay of ideas creates a fascinating tapestry of possibilities.")
                
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
        params = {"temperature": 0.7, "max_new_tokens": 100}
        prepared_text = f"{text}"  # No prefix needed
    elif mode == 'academic':
        model = "facebook/bart-large-cnn"
        params = {"temperature": 0.8, "max_new_tokens": 120}
        prepared_text = f"Transform into academic language: {text}"
    elif mode == 'simple':
        model = "facebook/bart-large-xsum"
        params = {"temperature": 0.6, "max_new_tokens": 80}
        prepared_text = f"Simplify: {text}"
    elif mode == 'creative':
        model = "gpt2"
        params = {"temperature": 0.9, "max_new_tokens": 150}
        prepared_text = f"Create an imaginative version of: {text}"
    else:
        # Default to fluency
        model = "tuner007/pegasus_paraphrase"
        params = {"temperature": 0.7}
        prepared_text = f"{text}"
    
    print(f"Using model: {model} with params: {params}")
    
    # API call to Hugging Face Inference API
    API_URL = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}
    
    # Include model parameters in the payload
    payload = {
        "inputs": prepared_text,
        "parameters": params
    }
    
    print(f"Sending request to {API_URL}")
    
    response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
    
    print(f"Response status code: {response.status_code}")
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}")
    
    # Parse the API response
    result = response.json()
    
    # Extract the paraphrased text from different possible response formats
    paraphrased_text = None
    
    try:
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict):
                if "generated_text" in result[0]:
                    paraphrased_text = result[0]["generated_text"]
                elif "summary_text" in result[0]:
                    paraphrased_text = result[0]["summary_text"]
            elif isinstance(result[0], str):
                paraphrased_text = result[0]
        elif isinstance(result, dict):
            if "generated_text" in result:
                paraphrased_text = result["generated_text"]
            elif "translation_text" in result:
                paraphrased_text = result["translation_text"]
    except Exception as e:
        print(f"Error parsing API response: {e}")
        raise Exception("Failed to parse API response")
    
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
            len(paraphrased_text) < 10):
            return get_local_paraphrase(text, mode)
        
        return paraphrased_text
    
    # If we couldn't parse the result, fall back to local paraphrasing
    print("Could not extract text from API result, using local paraphrasing instead")
    return get_local_paraphrase(text, mode)


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
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Flask app on port {port}, debug={debug}")
    print(f"HF API Token present: {'Yes' if HF_API_TOKEN else 'No'}")
    print(f"Using local fallback: {'Yes' if not HF_API_TOKEN or debug else 'Only if API fails'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)