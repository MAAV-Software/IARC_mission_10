import ssl
import urllib.request

print(ssl.get_default_verify_paths())
urllib.request.urlopen("https://pypi.org")
print("SSL OK")
