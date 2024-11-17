import os
import requests
import cohere
import yaml
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from dotenv import load_dotenv
import time
# Load environment variables from .env file (optional)
load_dotenv()

# Initialize Cohere Client
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY environment variable not set.")
cohere_client = cohere.Client(COHERE_API_KEY)


def download_file(url, save_path='downloaded_file.pdf'):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad status
    with open(save_path, 'wb') as f:
        f.write(response.content)
    print("File downloaded successfully!")
    return save_path

def preprocess_text(text):
    """
    Preprocess text to remove unnecessary line breaks and improve context understanding.
    """
    # Remove multiple newlines and extra spaces
    text = re.sub(r'\n+', ' ', text)  # Replace multiple newlines with a single space
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces

    # Remove common headers or footers (e.g., "Page 1", "Ausschreibungsdokument", etc.)
    text = re.sub(r'Page \d+', '', text)
    text = re.sub(r'Ausschreibungsdokument.*', '', text)

    # Fix sentence-breaking by handling cases where a sentence is split across lines without a period
    text = re.sub(r'([a-z])-\s+([a-z])', r'\1\2', text)  # Fix hyphenated word breaks
    text = re.sub(r'(\S)- (\S)', r'\1\2', text)  # Handle more hyphen breaks in German
    text = re.sub(r'([a-zA-Z])\s*\n\s*([a-zA-Z])', r'\1 \2', text)  # Remove line breaks within sentences

    return text


def convert_to_vector_store(file_path):
    loader = PyPDFLoader(file_path)
    # Use an embedding model suitable for German (if available)
    embedding = CohereEmbeddings(model="embed-multilingual-v2.0")
    pages = loader.load()

    # Preprocess each page's content before saving to the database
    preprocessed_pages = []
    for page in pages:
        preprocessed_content = preprocess_text(page.page_content)
        preprocessed_pages.append(preprocessed_content)

    # Save preprocessed pages to a text file for debugging purposes
    pages_text_path = "output/pages_preprocessed.txt"
    os.makedirs(os.path.dirname(pages_text_path), exist_ok=True)

    with open(pages_text_path, 'w', encoding='utf-8') as f:
        for i, content in enumerate(preprocessed_pages):
            f.write(f"Page {i + 1}:\n")
            f.write(content)
            f.write("\n\n" + "-" * 50 + "\n\n")  # Adding a separator between pages

    print(f"Preprocessed pages content saved for debugging at {pages_text_path}")

    # Initialize the RecursiveCharacterTextSplitter
    split_text = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=10,
        length_function=len,
        is_separator_regex=False,
    )

    # Split the preprocessed pages and store them in the vector store
    split_pages = []
    for content in preprocessed_pages:
        split_pages.extend(split_text.split_text(content))  # Splitting each page individually

    # Create vector store from split pages
    db = FAISS.from_texts(split_pages, embedding=embedding)

    return db


def save_vector_store(db, save_path):
    db.save_local(folder_path=save_path)
    print(f"Vector store saved successfully at {save_path}")


def load_vector_store(save_path, embedding):
    db = FAISS.load_local(save_path, embeddings=embedding, allow_dangerous_deserialization=True)
    return db


def query_vector_store(db, query, top_k=5):
    results = db.similarity_search(query, k=top_k)
    return results


def assess_factors(retrieved_text):
    """
    Assess five factors from the retrieved text and assign score labels along with a verification sentence.
    Verification sentences must be a maximum of 20 words.
    """

    # Optionally summarize the retrieved_text to keep the prompt concise
    retrieved_text_summary = retrieved_text[:1500]  # Increased limit to 1500 characters

    # Define the prompt
    prompt = f"""
Using the following tender text, assess each factor below and provide:

- A rating (choose from the provided options).
- A verification sentence (max 20 words) explaining why you chose this rating.

Tender Text:
{retrieved_text_summary}

Factors:

1. **Complexity**
   - **Ratings:** [Low], [Moderate], [High], [Not Available]
   - **Description:** Evaluate the overall complexity of the requested solution.

2. **Scalability**
   - **Ratings:** [Low], [Moderate], [High], [Not Available]
   - **Description:** Assess the ability of the solution to handle future growth.

3. **Integration Requirements**
   - **Ratings:** [Low], [Moderate], [High], [Not Available]
   - **Description:** Evaluate the complexity of integrating with existing systems.

4. **Time Feasibility**
   - **Ratings:** [Unfeasible], [Somehow Feasible], [Feasible], [Not Available]
   - **Description:** Consider the feasibility of the proposed timeline.

5. **Days Left to Submit the Proposal**
   - **Provide the number of days left or [Not Available] if not specified.

Provide your response in the following format:

Complexity:
Ratings: [Rating]
Verification Sentence: [Your verification sentence]

Scalability:
Ratings: [Rating]
Verification Sentence: [Your verification sentence]

Integration Requirements:
Ratings: [Rating]
Verification Sentence: [Your verification sentence]

Time Feasibility:
Ratings: [Rating]
Verification Sentence: [Your verification sentence]

Days Left to Submit the Proposal: [Number of days left] or [Not Available]
"""
    # Generate the response using Cohere
    try:
        response = cohere_client.generate(
            model='command-xlarge-nightly',
            prompt=prompt,
            max_tokens=700,  # Increased max_tokens
            temperature=0.3,
            k=0
        )
        generated_text = response.generations[0].text.strip()

        # Debugging: Print the generated text (optional)
        # print("\nGenerated Text:")
        # print(generated_text)

        # Initialize the factors dictionary
        factors = {}

        # Adjust regex patterns to match the expected format with case insensitivity and flexible spacing
        factor_patterns = {
            'Complexity': r'Complexity:\s*Ratings?:\s*([^\n]+)\s*Verification\s+Sentence:\s*(.*?)(?=\n\S|\Z)',
            'Scalability': r'Scalability:\s*Ratings?:\s*([^\n]+)\s*Verification\s+Sentence:\s*(.*?)(?=\n\S|\Z)',
            'Integration Requirements': r'Integration\s*Requirements:\s*Ratings?:\s*([^\n]+)\s*Verification\s+Sentence:\s*(.*?)(?=\n\S|\Z)',
            'Time Feasibility': r'Time\s*Feasibility:\s*Ratings?:\s*([^\n]+)\s*Verification\s+Sentence:\s*(.*?)(?=\n\S|\Z)',
            'Days Left to Submit the Proposal': r'Days\s*Left\s*to\s*Submit\s*the\s*Proposal:\s*(.*)'
        }

        for factor, pat in factor_patterns.items():
            print(generated_text)
            match = re.search(pat, generated_text, re.DOTALL)
            if match:
                if factor != 'Days Left to Submit the Proposal':
                    rating = match.group(1).strip()
                    verification_sentence = match.group(2).strip()
                    # Ensure verification sentence is maximum 20 words
                    word_count = len(verification_sentence.split())
                    if word_count > 20:
                        verification_sentence = "Verification sentence exceeds 20 words."
                    factors[factor] = {
                        'Rating': rating,
                        'Verification Sentence': verification_sentence
                    }
                else:
                    factors[factor] = match.group(1).strip()
            else:
                if factor != 'Days Left to Submit the Proposal':
                    factors[factor] = {
                        'Rating': 'Not Available',
                        'Verification Sentence': 'Not Available'
                    }
                else:
                    factors[factor] = 'Not Available'

        # Return the factors dictionary
        print(factors)
        return factors

    except Exception as e:
        print(f"Error generating assessment labels: {e}")
        return {}









def save_yaml_to_file(structured_data, output_path):
    """
    Save structured YAML data to a file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            yaml.dump(structured_data, file, allow_unicode=True, sort_keys=False, indent=4)
        print(f"Structured YAML saved to {output_path}")
    except Exception as e:
        print(f"Error saving structured YAML to file: {e}")

def get_assesment(file_path):
    embedding = CohereEmbeddings(model="embed-multilingual-v2.0")
    save_path = "store/vectorstore"
    
    # Check if db is available else wait for it to be available
    db = None
    while db is None:
        try:
            db = load_vector_store(save_path, embedding)
        except Exception as e:
            print(f"Database not available yet. Waiting... Error: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying

    query = "What are the important points in the tender?"
    results = query_vector_store(db, query, top_k=5)
    
    # Combine retrieved texts
    retrieved_text = "\n".join([doc.page_content for doc in results])
    # print(retrieved_text)

    # Assess the factors
    factors = assess_factors(retrieved_text)
    print(factors)

    # Print and save the factors
    if factors:
        print("\nFinal Output:")
        print(yaml.dump(factors, allow_unicode=True, sort_keys=False, indent=4))

        # Save the factors to a YAML file
        output_yaml_path = "uploads/assessment_labels.yaml"
        save_yaml_to_file(factors, output_yaml_path)
    else:
        print("Failed to generate assessment labels.")

    return factors
    

# Example usage
if __name__ == "__main__":
    file_path = r"CPQ_Ausschreibung2.pdf"
    get_assesment(file_path)
