import json
import os
import logging
import requests
from langchain.tools import tool

class SearchTools():
    @staticmethod
    @tool("Search the internet")
    def search_internet(query):
        """Useful to search the internet about a given topic and return relevant results."""
        top_result_to_return = 4
        url = "https://google.serper.dev/search"
        
        # Handle different query formats
        try:
            if isinstance(query, dict):
                if 'query' in query and isinstance(query['query'], dict):
                    query = query['query'].get('description', '')
                else:
                    query = str(query)
            elif not isinstance(query, str):
                query = str(query)
                
            payload = json.dumps({"q": query})
            headers = {
                'X-API-KEY': os.environ['SERPER_API_KEY'],
                'content-type': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            
            results = response.json().get('organic', [])
            
            if not results:
                return "No search results found for the query."
            
            formatted_results = []
            for result in results[:top_result_to_return]:
                try:
                    formatted_results.append('\n'.join([
                        f"Title: {result['title']}", 
                        f"Link: {result['link']}",
                        f"Snippet: {result['snippet']}", 
                        "\n-----------------"
                    ]))
                except KeyError as e:
                    logging.warning(f"Missing field in result: {e}")
                    continue
            
            return '\n'.join(formatted_results) if formatted_results else "No valid results found."
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            return f"Search API error: {str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return f"An unexpected error occurred: {str(e)}"