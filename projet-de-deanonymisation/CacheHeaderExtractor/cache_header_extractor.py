#!/usr/bin/env python3
"""
CacheHeaderExtractor - Extraction des en-têtes de cache via Cloudflare

Ce script permet d'interroger une URL et d'extraire les en-têtes
"cf-ray" et "cf-cache-status" renvoyés par Cloudflare.
"""

import requests

def extract_cache_headers(url):
    """
    Envoie une requête GET à l'URL spécifiée et renvoie les en-têtes
    "cf-ray" et "cf-cache-status".

    :param url: URL de la ressource à analyser
    :return: tuple (cf_ray, cf_cache_status)
    """
    try:
        response = requests.get(url, timeout=5)
        cf_ray = response.headers.get("cf-ray", "Inconnu")
        cf_cache_status = response.headers.get("cf-cache-status", "Inconnu")
        return cf_ray, cf_cache_status
    except Exception as e:
        print(f"Erreur lors de la requête : {e}")
        return None, None

if __name__ == '__main__':
    url = input("Entrez l'URL à analyser (ex. https://www.namecheap.com/favicon.ico) : ")
    cf_ray, cf_cache_status = extract_cache_headers(url)
    print(f"cf-ray : {cf_ray}")
    print(f"cf-cache-status : {cf_cache_status}")
