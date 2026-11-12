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

DEFAULT_SUPABASE_URL = "https://ngsonqwylcwcziwxurkc.supabase.co"
DEFAULT_SUPABASE_KEY = "sb_publishable_yW45_DoFX6OHfZHYYNcStA_tRDiM_z_"
VALID_THEMES = ("cozy-cat", "sakura", "artek", "cyber")
DEFAULT_WEEKLY_OPEN_SLOTS = {
    "0": [],
    "1": ["14:00", "15:00", "16:00", "17:00", "18:00"],
    "2": ["14:00", "15:00", "16:00", "17:00", "18:00"],
    "3": ["14:00", "15:00", "16:00", "17:00", "18:00"],
    "4": ["14:00", "15:00", "16:00", "17:00", "18:00"],
    "5": ["14:00", "15:00", "16:00", "17:00", "18:00"],
    "6": ["11:00", "12:00", "13:00", "14:00"]
}

def _parse_duration_minutes(raw_val, default=60):
    if isinstance(raw_val, (int, float)):
        return max(15, int(raw_val))
    m = re.search(r"\d+", str(raw_val or ""))
    return max(15, int(m.group(0))) if m else default

def _slugify(value):
    cyr = {
        "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z","и":"i",
        "й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t",
        "у":"u","ф":"f","х":"h","ц":"ts","ч":"ch","ш":"sh","щ":"sch","ъ":"","ы":"y","ь":"",
        "э":"e","ю":"yu","я":"ya"
    }
    translit = "".join(cyr.get(ch, ch) for ch in str(value or "").lower())
    slug = re.sub(r"[^a-z0-9]+", "-", translit).strip("-")
    return slug or "tutor-site"

def _normalize_programs(raw_programs):
    default_icons = ["👥", "⚡", "🎯", "🎓"]
    out = []
    for idx, p in enumerate(raw_programs or []):
        out.append({
            "id": str(p.get("id") or f"prog_{idx+1}"),
            "title": str(p.get("title") or "Занятие"),
            "desc": str(p.get("desc") or ""),
            "benefit": str(p.get("benefit") or ""),
            "price": int(p.get("price") or 0),
            "duration": _parse_duration_minutes(p.get("duration"), 60),
            "icon": str(p.get("icon") or default_icons[idx % len(default_icons)]),
            "badge": p.get("badge"),
            "hidden": bool(p.get("hidden", False))
        })
    return out

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
    s = config.get("site", {})
    th = config.get("theme", {}) if isinstance(config.get("theme"), dict) else {}

    teacher_name = t.get("name", "Преподаватель")
    teacher_short = t.get("shortName", teacher_name.split()[0] if teacher_name else "Преподаватель")
    teacher_subtitle = t.get("subtitle", "Репетитор высшей категории")
    teacher_headline = t.get("headline", teacher_subtitle)
    hero_desc = t.get("heroDescription", teacher_headline)
    phone_fmt = c.get("phone", "")
    phone_raw = c.get("phoneRaw", re.sub(r"[^\d+]", "", phone_fmt))
    max_url = c.get("maxUrl", "https://max.ru/")
    tg_handle = c.get("telegramHandle", "")
    tg_url = c.get("telegramUrl", "https://t.me/")
    avito_url = c.get("avitoUrl", "")
    reviews_channel_url = c.get("reviewsChannelUrl", "")
    raw_default_theme = str(th.get("default") or s.get("defaultTheme") or "cozy-cat").strip()
    default_theme = raw_default_theme if raw_default_theme in VALID_THEMES else "cozy-cat"
    site_slug = s.get("slug") or _slugify(teacher_name)
    supabase_url = s.get("supabaseUrl") or DEFAULT_SUPABASE_URL
    supabase_key = s.get("supabaseKey") or DEFAULT_SUPABASE_KEY
    programs = _normalize_programs(config.get("programs", []))
    
    replacements = {
        "{{TEACHER_NAME}}": teacher_name,
        "{{TEACHER_SHORT_NAME}}": teacher_short,
        "{{TEACHER_SUBTITLE}}": teacher_subtitle,
        "{{TEACHER_HEADLINE}}": teacher_headline,
        "{{HERO_DESC}}": hero_desc,
        "{{PAGE_TITLE}}": f"{teacher_name} — {t.get('subject', 'Репетитор')} | {t.get('targetAudience', 'ОГЭ')}",
        "{{PHONE_FORMATTED}}": phone_fmt,
        "{{PHONE_RAW}}": phone_raw,
        "{{MAX_URL}}": max_url,
        "{{TG_HANDLE}}": tg_handle,
        "{{TG_URL}}": tg_url,
        "{{AVITO_URL}}": avito_url,
        "{{SITE_SLUG_JS}}": json.dumps(site_slug, ensure_ascii=False),
        "{{SUPABASE_URL_JS}}": json.dumps(supabase_url, ensure_ascii=False),
        "{{SUPABASE_KEY_JS}}": json.dumps(supabase_key, ensure_ascii=False),
        "{{TEACHER_NAME_JS}}": json.dumps(teacher_name, ensure_ascii=False),
        "{{TEACHER_SHORT_NAME_JS}}": json.dumps(teacher_short, ensure_ascii=False),
        "{{TEACHER_SUBTITLE_JS}}": json.dumps(teacher_subtitle, ensure_ascii=False),
        "{{TEACHER_HEADLINE_JS}}": json.dumps(teacher_headline, ensure_ascii=False),
        "{{HERO_DESC_JS}}": json.dumps(hero_desc, ensure_ascii=False),
        "{{PHONE_FORMATTED_JS}}": json.dumps(phone_fmt, ensure_ascii=False),
        "{{PHONE_RAW_JS}}": json.dumps(phone_raw, ensure_ascii=False),
        "{{MAX_URL_JS}}": json.dumps(max_url, ensure_ascii=False),
        "{{TG_HANDLE_JS}}": json.dumps(tg_handle, ensure_ascii=False),
        "{{TG_URL_JS}}": json.dumps(tg_url, ensure_ascii=False),
        "{{AVITO_URL_JS}}": json.dumps(avito_url, ensure_ascii=False),
        "{{REVIEWS_CHANNEL_URL_JS}}": json.dumps(reviews_channel_url, ensure_ascii=False),
        "{{DEFAULT_THEME_JS}}": json.dumps(default_theme, ensure_ascii=False),
        "{{PROGRAMS_JSON}}": json.dumps(programs, ensure_ascii=False, indent=12),
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
    print(f"  Site slug: {site_slug}")
    print(f"  Supabase:  {supabase_url}")
    print(f"  Teacher:   {teacher_name}")
    print(f"  Contacts:  {phone_fmt}, MAX: {max_url}, TG: {tg_handle}")
    print("  Reminder:  Seed site_slug & bcrypt PIN in Supabase before publishing (PIN is NOT stored in HTML).")
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
