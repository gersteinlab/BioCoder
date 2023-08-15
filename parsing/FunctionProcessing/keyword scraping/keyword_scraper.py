import requests
from tqdm import tqdm
from multiprocessing import Pool

API_URL = "https://en.wikipedia.org/w/api.php"

def search_wikipedia(query, search_info=True):
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srnamespace": 0,
        "srlimit": 50,
    }
    if search_info:
        params["srinfo"] = "totalhits"
    
    response = requests.get(API_URL, params=params)
    return response.json()

def get_article_links(title):
    params = {
        "action": "query",
        "format": "json",
        "prop": "linkshere",
        "titles": title,
        "lhnamespace": 0,
        "lhlimit": 500,
    }
    response = requests.get(API_URL, params=params)
    return response.json()

def is_bioinformatics_related(title):
    linked_articles = get_article_links(title)
    for _, page_data in linked_articles["query"]["pages"].items():
        if len(page_data.get("linkshere", [])) >= 10:
            return True
    return False

def find_recursive_linked_articles(titles, depth=1):
    if depth <= 0:
        return titles

    linked_articles = set()
    for title in tqdm(titles, desc=f"Processing depth {depth}"):
        linked_articles_data = get_article_links(title)
        for _, page_data in linked_articles_data["query"]["pages"].items():
            linked_titles = [link["title"] for link in page_data.get("linkshere", [])]
            linked_articles.update(linked_titles)
    
    return titles | find_recursive_linked_articles(linked_articles, depth-1)

def parallel_is_bio_related(titles):
    with Pool(8) as p:
        results = list(tqdm(p.imap(is_bioinformatics_related, titles), total=len(titles), desc="Filtering terms"))
    return results

def find_bioinformatics_terms(queries, search_info=True, recursive_depth=1):
    bioinformatics_related_terms = set()

    for query in queries:
        search_results = search_wikipedia(query, search_info)
        for result in search_results["query"]["search"]:
            title = result["title"]
            bioinformatics_related_terms.add(title)

    bioinformatics_related_terms = find_recursive_linked_articles(
        bioinformatics_related_terms, recursive_depth
    )

    parallel_results = parallel_is_bio_related(bioinformatics_related_terms)
    
    filtered_terms = {term for term, result in zip(bioinformatics_related_terms, parallel_results) if result}

    return filtered_terms

expanded_queries = [
    "bioinformatics",
    "genomics",
    "proteomics",
    "transcriptomics",
    "metabolomics",
    "phylogenetics",
    "sequence alignment",
    "gene prediction",
    "molecular modeling",
    "FASTA",
    "FASTQ",
    "SAM",
    "BAM",
    "VCF",
]

# Set recursive_depth to control how many levels of linked articles to explore
recursive_depth = 1
bioinformatics_terms = find_bioinformatics_terms(expanded_queries, recursive_depth=recursive_depth)

print("Bioinformatics-related terms:")
for term in bioinformatics_terms:
    print("-", term)