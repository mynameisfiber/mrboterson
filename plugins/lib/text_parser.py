import re


def get_channels(text):
    return re.findall(r'<#(?P<channel>[^>]+)>', text)
