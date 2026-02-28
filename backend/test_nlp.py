import sys
sys.path.append('.')
from gemini_utils import parse_search_query
query = "ex portugal colony, casino, couple"
print(parse_search_query(query))
