import re
from collections import Counter, defaultdict
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from simhash import Simhash

seen_patterns = {}
seen_links = set()
visited_hashes = set()
common_words_count = Counter()
subdomain_pages = defaultdict(set)
processed_count = 0

# Global variable to store the longest page information
longest_page = {"url": "", "word_count": 0}

# Keep track of our stopwords to ignore
stopwords = [
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", 
    "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below", 
    "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", 
    "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", 
    "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", 
    "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", 
    "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", 
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", 
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", 
    "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", 
    "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", 
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", 
    "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", 
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", 
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", 
    "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", 
    "your", "yours", "yourself", "yourselves"
]

def scraper(url, resp):
    global processed_count
    print(f"Scraper called for URL: {url}")
    # Check the url being passed into scraper
    #### check if it's empty
    #### call is valid
    #### check if unique
    #### not a trap

    # Makes sure we skip already seen links
    if url in seen_links:
        return []
    
    # Checks if url and its content has a trap or if is empty, if so, skip over
    if check_trap(url) or empty_URL(resp) or not is_valid(url):
        print(f"No information or trap detected for URL {url}, skipping...")
        return []
    
    # Check if `resp.raw_response` and `resp.raw_response.content` are available
    if not resp.raw_response or not resp.raw_response.content:
        print(f"No content available for {url}, skipping...")
        return []
    
    if not has_high_textual_content(resp.raw_response.content):
        print(f"[DEBUG] Low textual content detected for URL {url}, skipping...")
        return []
    
    # Process content to evaluate similarity and information quality
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    text_content = soup.get_text(separator=' ', strip=True)
    word_count = len(re.findall(r'\b\w+\b', text_content.lower()))

    # Check if the page is similar to others seen before or if it lacks information
    if is_similar_page(text_content):
        print(f"[DEBUG] Similar or low-information page detected for URL {url}, skipping...")
        return []
    
    if resp.status == 200 and resp.raw_response and resp.raw_response.content:
        # Update the longest page if the current page has more words
        update_longest_page(url, resp.raw_response.content)
        most_common_words(resp.raw_response.content)
    
    # Otherwise, add the link to our seen set
    seen_links.add(url)
    add_to_subdomains(url)
    
    # Increment the processed counter
    processed_count += 1
    
    # Checkpoint: save subdomain info every 100 URLs processed
    if processed_count % 100 == 0:
        print("[DEBUG] Checkpoint reached. Saving subdomain information.")
        save_subdomain_info()
    

    # Extract all links found in our URL
    links = extract_next_links(url, resp)

    # Check each link thats been extracted
    for link in links:

        # call is valid and we have not added link yet
        if is_valid(link) and link not in seen_links:

            # add valid link to our seen_extracted set
            seen_links.add(link)

    print(f"[DEBUG] Unique valid links extracted from {url}: {list(seen_links)}")

    save_unique_pages()
    save_most_common_words()
    
    return list(seen_links)


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    print(f"Extracting links from: {url}")
    if resp.status != 200 or not resp.raw_response:
        return[]

    # Step 2: Check if `raw_response` and `raw_response.content` are available
    if not resp.raw_response or not resp.raw_response.content:
        print(f"No content available for {url}")
        return []

    # Parse the content of the page
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

    links = []

    for link in soup.find_all('a', href = True):
        href = link['href']
        absolute_link = urljoin(resp.raw_response.url, link['href'])

        # Removes fragments
        absolute_link = urlparse(absolute_link)._replace(fragment="").geturl()
        links.append(absolute_link)

    print(f"Total links extracted: {len(links)}")
    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    print(f"Validating URL: {url}")
    try:
        usel = urlparse(url)._replace(fragment="").geturl()
        parsed = urlparse(usel)

        if parsed.scheme not in set(["http", "https"]):
            return False

        # check if the URL belongs to allowed domains and paths
        if re.match(r"(.*\.)?(ics|cs|informatics|stat)\.uci\.edu$", parsed.netloc):
            pass
        elif parsed.netloc == "today.uci.edu" and parsed.path.startswith("/department/information_computer_sciences"):
            pass
        else:
            return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def extract_pattern(url):
    # Parse the URL
    parsed = urlparse(url)
    
    # Replace digit sequences in the path with "[digit]"
    path_pattern = re.sub(r'\d+', '[digit]', parsed.path)
    
    # Rebuild the URL pattern with the modified path
    url_pattern = f"{parsed.scheme}://{parsed.netloc}{path_pattern}"
    
    return url_pattern

def check_trap(url) -> bool:
    pattern = extract_pattern(url)  # Get the URL pattern with placeholders for digits
    
    if pattern not in seen_patterns:
        seen_patterns[pattern] = 1
    
    seen_patterns[pattern] += 1  # Increment count for this pattern
    
    # Threshold for pattern repetition (e.g., more than 10 occurrences)
    if seen_patterns[pattern] > 10:
        print(f"[DEBUG] Trap detected for pattern: {pattern}")
        return True

    return False

def empty_URL(resp):
    """
    Checks for if the URL works, but has no content

    Args:
        resp (Response): The response object for the given URL content
        
    Returns:
        bool: True if URL is empty but connects (200 status), false if otherwise
    """

    if resp.status == 200:
        # Check if resonse has content
        if resp.raw_response:
            # Check if the content length == zero
            if len(resp.raw_response.content) == 0:
                return True  # Empty URL
        else:
            return True  # Empty URL
    return False  # Not empty URL

def has_high_textual_content(content):
    """
    Determines if a page has high textual information content based on the text-to-HTML ratio
    and the presence of meaningful keywords.

    Args:
        content (bytes): The raw HTML content of the page.

    Returns:
        bool: True if the page is deemed to have high textual information, otherwise False.
    """
    if not content:
        print("Debug: No content provided.")
        return False
    
    # Parse the page content using BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    print("Debug: Parsed HTML content with BeautifulSoup.")

    # Extract text content from the HTML
    text_content = soup.get_text(separator=' ', strip=True)
    print("Debug: Extracted text content.")
    
    # Count the number of words
    words = re.findall(r'\b\w+\b', text_content.lower())
    word_count = len(words)
    print(f"Debug: Word count = {word_count}")

    # Check if word count meets threshold
    if word_count < 100:
        print("Debug: Page does not have significant textual content.")
        return False
    else:
        print("Debug: Page has significant textual content.")
        return True
    
    
def is_similar_page(content):
    """
    Detects if a page is similar to previously seen pages by comparing SimHash values.

    Args:
        content (str): The text content of the page.

    Returns:
        bool: True if the page is similar to existing pages, False otherwise.
    """
    # Generate SimHash for the content
    current_hash = Simhash(content)
    current_hash_value = current_hash.value  # Get the integer representation of the Simhash

    for existing_hash_value in visited_hashes:
        # Create a Simhash object from the stored integer value to compare distances
        existing_hash = Simhash(existing_hash_value)
        # Check for similarity using SimHash's Hamming distance
        if current_hash.distance(existing_hash) < 5:  # threshold of 5 can be adjusted
            print("[DEBUG] Similar page detected, skipping...")
            return True

    # If not similar, add the integer hash to visited_hashes
    visited_hashes.add(current_hash_value)
    return False

def save_unique_pages():
    with open('unique_pages.txt', 'w') as file:
        file.write(f"Total Unique Pages: {len(seen_links)}\n")


# def update_longest_page(url, word_count):
#     global longest_page
#     if word_count > longest_page["word_count"]:
#         longest_page["url"] = url
#         longest_page["word_count"] = word_count
#         print(f"[DEBUG] New longest page found: {url} with {word_count} words.")
        
#         # Save the longest page information to a file
#         with open("longest_page.txt", "w") as file:
#             file.write(f"Longest Page URL: {url}\n")
#             file.write(f"Word Count: {word_count}\n")


def update_longest_page(url, html_content):
    global longest_page
    
    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted tags like <script>, <style>, <nav>, <footer>, <header>, and <aside>
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()
    
    # Extract the visible text content
    text_content = soup.get_text(separator=' ', strip=True)
    
    # Count the number of words using a regular expression
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text_content.lower())  # Words of 3 or more letters
    word_count = len(words)
    
    # Update the longest page if the current page has more words
    if word_count > longest_page["word_count"]:
        longest_page["url"] = url
        longest_page["word_count"] = word_count
        print(f"[DEBUG] New longest page found: {url} with {word_count} words.")
        
        # Save the longest page information to a file
        with open("longest_page.txt", "w") as file:
            file.write(f"Longest Page URL: {url}\n")
            file.write(f"Word Count: {word_count}\n")


def most_common_words(html_content):
    word_counts = count_words_in_content(html_content)
    common_words_count.update(word_counts)


def count_words_in_content(html_content):
    """
    Returns a counter object of every word in the content and its count, filtering out stop words
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    words = re.findall(r'\b\w+\b', text.lower())
    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
    return Counter(filtered_words)

def save_most_common_words():
    with open('common_words.txt', 'w') as file:
        file.write("Most Common Words:\n")
        for word, count in common_words_count.most_common(50):
            file.write(f"{word}: {count}\n")
            
def add_to_subdomains(url):
    parsed_url = urlparse(url)
    if parsed_url.netloc.endswith("uci.edu"):
        subdomain = parsed_url.netloc  # Get the full subdomain, e.g., "vision.ics.uci.edu"
        subdomain_pages[subdomain].add(url)  # Add unique URL to the set
        
def save_subdomain_info():
    with open('subdomains.txt', 'w') as file:
        for subdomain, urls in sorted(subdomain_pages.items()):
            if urls:
                example_url = next(iter(urls))
                parsed_url = urlparse(example_url)
                scheme = parsed_url.scheme
                netloc = parsed_url.netloc

                formatted_subdomain = f"{scheme}://{netloc}"
                file.write(f"{formatted_subdomain}, {len(urls)}\n")
                