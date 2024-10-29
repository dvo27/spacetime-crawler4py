import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

seen_patterns = {}
seen_links = set()

def scraper(url, resp):
    print(f"Scraper called for URL: {url}")

    # Makes sure we skip already seen links
    if url in seen_links:
        return []

    # Otherwise, add the link to our seen set
    seen_links.add(url)

    # Extract all links found in our URL
    links = extract_next_links(url, resp)

    # Return list of valid only links found in current URL
    valid_links = [link for link in links if is_valid(link)]

    print(seen_links)
    return valid_links

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

def detect_pattern(url):
    pattern = extract_pattern(url)  # Get the URL pattern with placeholders for digits
    visited_patterns[pattern] += 1  # Increment count for this pattern
    
    # Threshold for pattern repetition (e.g., more than 10 occurrences)
    if visited_patterns[pattern] > 10:
        print(f"[DEBUG] Trap detected for pattern: {pattern}")
        return True
    
    return False
    
