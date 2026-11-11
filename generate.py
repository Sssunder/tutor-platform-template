#!/usr/bin/env python3
"""
TUTOR PLATFORM GENERATOR CLI
Generates a complete, production-grade interactive landing page & booking platform
for a tutor or teacher from a simple JSON configuration.
"""

import os
import sys
import json
import argparse
import re

def validate_config(config):
    required = ["teacher", "contacts", "admin"]
    for req in required:
        if req not in config:
            raise ValueError(f"Missing required config section: '{req}'")
            
    t = config["teacher"]
    for field in ["name", "subject", "subtitle"]:
        if field not in t:
            raise ValueError(f"Missing required teacher field: '{field}'")
            
    c = config["contacts"]
    for field in ["phone", "maxUrl", "telegramUrl"]:
        if field not in c:
            raise ValueError(f"Missing required contact field: '{field}'")
            
    a = config["admin"]
    if "pinCode" not in a:
        raise ValueError("Missing admin.pinCode")

def generate_site(config_path, output_path, template_path=None):
    if not template_path:
        template_path = os.path.join(os.path.dirname(__file__), "template.html")
        
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    validate_config(config)
    
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    t = config["teacher"]
    c = config["contacts"]
    a = config["admin"]
    
    replacements = {
        "{{TEACHER_NAME}}": t.get("name", "Преподаватель"),
        "{{TEACHER_SHORT_NAME}}": t.get("shortName", t.get("name", "").split()[0]),
        "{{TEACHER_SUBTITLE}}": t.get("subtitle", "Репетитор высшей категории"),
        "{{TEACHER_HEADLINE}}": t.get("headline", t.get("subtitle", "")),
        "{{PAGE_TITLE}}": f"{t.get('name')} — {t.get('subject', 'Репетитор')} | {t.get('targetAudience', 'ОГЭ')}",
        "{{PHONE_FORMATTED}}": c.get("phone", ""),
        "{{PHONE_RAW}}": c.get("phoneRaw", re.sub(r"[^\d+]", "", c.get("phone", ""))),
        "{{MAX_URL}}": c.get("maxUrl", "https://max.ru/"),
        "{{TG_HANDLE}}": c.get("telegramHandle", ""),
        "{{TG_URL}}": c.get("telegramUrl", "https://t.me/"),
        "{{PIN_CODE}}": str(a.get("pinCode", "1234")),
    }
    
    for token, val in replacements.items():
        html = html.replace(token, val)
        
    # Check for unresolved tokens
    unresolved = re.findall(r"\{\{[A-Z0-9_]+\}\}", html)
    if unresolved:
        print(f"Warning: Found unresolved tokens: {set(unresolved)}")
        
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"✓ Production site successfully generated at: {os.path.abspath(output_path)}")
    print(f"  Teacher: {t.get('name')}")
    print(f"  Contacts: {c.get('phone')}, MAX: {c.get('maxUrl')}, TG: {c.get('telegramHandle')}")
    print(f"  Admin PIN: {a.get('pinCode')}")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tutor Platform Generator")
    parser.add_argument("--config", "-c", default=os.path.join(os.path.dirname(__file__), "config.example.json"), help="Path to config JSON")
    parser.add_argument("--output", "-o", default=os.path.join(os.path.dirname(__file__), "dist", "index.html"), help="Path to output HTML")
    parser.add_argument("--template", "-t", default=None, help="Path to custom template.html")
    args = parser.parse_args()
    
    try:
        generate_site(args.config, args.output, args.template)
    except Exception as e:
        print(f"Error generating site: {e}", file=sys.stderr)
        sys.exit(1)
