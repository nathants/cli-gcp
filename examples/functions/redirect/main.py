#!/usr/bin/env python37

def main(request):
    body = ''
    status = 302
    headers = {'Location': 'https://www.google.com'}
    return body, status, headers
