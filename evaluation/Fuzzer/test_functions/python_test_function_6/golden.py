def encode_url_query(uniprot_query):

    def replace_all(text, replace_dict):
        for i, j in replace_dict.items():
            text = text.replace(i, j)
        return text
    encoding_dict = {' ': '+', ':': '%3A', '(': '%28', ')': '%29', '"':
        '%22', '=': '%3D'}
    return replace_all(uniprot_query, encoding_dict)