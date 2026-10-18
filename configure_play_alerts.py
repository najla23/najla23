#!/usr/bin/env python3
"""Configure a public FormSubmit destination; never use an API secret here.

Run before install_ion_game.py, or pass --html /path/to/docs/index.html.
The default endpoint is blank, so the delivered game sends nothing yet.
"""
import argparse
from html import escape
from pathlib import Path
import re


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--token', help='FormSubmit invisible-email identifier from your verification email')
    group.add_argument('--email', help='Recipient email; this will be visible in your public HTML until replaced with a token')
    group.add_argument('--disable', action='store_true')
    parser.add_argument('--html', type=Path, default=Path(__file__).resolve().parent/'docs/index.html')
    args=parser.parse_args()
    destination=args.token or args.email or ''
    if args.token and not re.fullmatch(r'[A-Za-z0-9_-]{8,200}',destination):
        parser.error('Use only the FormSubmit identifier, not a URL or secret API key.')
    if args.email and not re.fullmatch(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}',destination):
        parser.error('Enter a valid email address.')
    endpoint='https://formsubmit.co/ajax/'+destination if destination else ''
    text=args.html.read_text(encoding='utf-8')
    pattern=r'<meta name="nh-play-alert-endpoint" content="[^"]*">'
    if len(re.findall(pattern,text))!=1:
        parser.error('Expected exactly one play-alert configuration tag; no changes made.')
    updated=re.sub(pattern,lambda _:f'<meta name="nh-play-alert-endpoint" content="{escape(endpoint,quote=True)}">',text)
    backup=args.html.with_name(args.html.name+'.before-alerts.bak')
    backup.write_text(text,encoding='utf-8')
    args.html.write_text(updated,encoding='utf-8')
    print('Play alerts disabled.' if args.disable else 'Destination configured. Email delivery still requires recipient verification and publication.')
    if args.email:print('Your address is present in the HTML. Use --token after FormSubmit sends your invisible-email identifier.')
    print('Local backup:',backup)


if __name__=='__main__':
    main()
