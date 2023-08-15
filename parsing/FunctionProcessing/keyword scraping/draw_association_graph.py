import requests
from bs4 import BeautifulSoup
import networkx as nx
import matplotlib.pyplot as plt
from tqdm import tqdm
from multiprocessing import Pool
import scipy 
# Read article names from the text file
with open('/home/ubuntu/Bio-Code-Eval/Bio-Code-Eval-new/2-filter-and-annotate/dictionary.txt', 'r') as f:
    article_names = [line.strip() for line in f.readlines()]

# Scrape Wikipedia articles and references
def get_references(article_name):
    url = f'https://en.wikipedia.org/wiki/{article_name}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    reference_list = soup.find_all('span', class_='reference-text')
    return [ref.text for ref in reference_list]

def parallel_get_references(article_names, num_workers):
    with Pool(num_workers) as pool:
        results = list(tqdm(pool.imap(get_references, article_names), total=len(article_names), desc="Scraping Wikipedia articles"))
    return dict(zip(article_names, results))

num_workers = 32
article_references = parallel_get_references(article_names, num_workers)

# Create association graph
def create_association_graph(article_references):
    graph = nx.DiGraph()
    
    for article, references in article_references.items():
        graph.add_node(article)
        for ref in references:
            if ref in graph:
                if (article, ref) in graph.edges:
                    graph.edges[article, ref]['weight'] += 1
                else:
                    graph.add_edge(article, ref, weight=1)
    return graph

association_graph = create_association_graph(article_references)

# Draw association graph
def draw_association_graph(graph):
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, node_size=2000, font_size=10)
    edge_labels = {(u, v): d['weight'] for u, v, d in graph.edges(data=True)}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
    plt.show()

draw_association_graph(association_graph)

# Create hierarchical graph
def create_hierarchical_graph(graph):
    in_degrees = dict(graph.in_degree())
    sorted_nodes = sorted(graph.nodes, key=lambda x: in_degrees[x], reverse=True)
    hierarchical_graph = nx.DiGraph()
    for node in sorted_nodes:
        hierarchical_graph.add_node(node, level=in_degrees[node])
        for successor in graph.successors(node):
            hierarchical_graph.add_edge(node, successor)
    return hierarchical_graph

hierarchical_graph = create_hierarchical_graph(association_graph)

# Draw hierarchical graph
def draw_hierarchical_graph(graph):
    pos = nx.multipartite_layout(graph, subset_key="level")
    nx.draw(graph, pos, with_labels=True, node_size=2000, font_size=10)
    plt.show()

draw_hierarchical_graph(hierarchical_graph)
