import requests

def check_cdn_response(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, timeout=10, headers=headers)

    print(f"URL: {url}")
    print(f"Status Code: {response.status_code}")
    print(f"Response time: {response.elapsed.total_seconds() * 1000:.2f} ms")
    print()

    print("All headers:")
    for key, value in response.headers.items():
        print(f" {key}: {value}")
    print()

    print("CDN-specific headers:")
    cache_control = response.headers.get("Cache-Control", "Not present")
    server_timing = response.headers.get("Server-Timing", "Not present")
    print(f" Cache-Control: {cache_control}")
    print(f"Server-Timing (raw): {server_timing}")
    
    if "cdn-cache" in server_timing:
        for part in server_timing.split(","):
            if "cdn-cache" in part:
                print(f"CDN cache status: {part.strip()}")
    print("-" * 60)



urls = [
    "https://www.akamai.com/site/en/documents/",
    "https://www.zappos.com",       # Akamai customer, historically
]


for url in urls:
    check_cdn_response(url)




# response = requests.get("https://loans.zerodhacapital.com/")

# print(response.status_code) # 200
# print(response.headers) # response headers


