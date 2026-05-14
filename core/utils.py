import os
import shutil
from datetime import datetime
import zipfile
import sys
from PIL import Image, ImageDraw, ImageFont
import textwrap
import re
import json

def get_language_priority(text):
    if not text:
        return 99
    c = text[0]
    # Hangul
    if '\uac00' <= c <= '\ud7af' or '\u1100' <= c <= '\u11ff' or '\u3130' <= c <= '\u318f':
        return 1
    # Japanese (Hiragana/Katakana)
    elif '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff':
        return 2
    # English/Latin
    elif '\u0041' <= c <= '\u005a' or '\u0061' <= c <= '\u007a':
        return 3
    # Kanji / CJK
    elif '\u4e00' <= c <= '\u9fff':
        return 4
    return 5

def sort_games(games, order='desc'):
    # order: 'desc' or 'asc'
    def key_func(g):
        score_val = -g['score'] if order == 'desc' else g['score']
        return (score_val, get_language_priority(g['title']), g['title'].lower())
    
    return sorted(games, key=key_func)

CONFIG_PATH = os.path.join("data", "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "colors": {},
        "language": "한국어",
        "theme": "dark",
        "title_lang": "original"
    }

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def backup_data(dest_folder):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"vnlist_backup_{now}.zip"
    zip_path = os.path.join(dest_folder, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add db
        db_path = os.path.join("data", "vnlist.db")
        if os.path.exists(db_path):
            zipf.write(db_path, os.path.join("data", "vnlist.db"))
        
        # Add config
        if os.path.exists(CONFIG_PATH):
            zipf.write(CONFIG_PATH, os.path.join("data", "config.json"))
        
        # Add covers
        covers_path = os.path.join("data", "covers")
        if os.path.exists(covers_path):
            for root, dirs, files in os.walk(covers_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, ".")
                    zipf.write(file_path, arcname)
    
    return zip_path

def restore_data(zip_path):
    # WARNING: This should overwrite data directory.
    # The warning is handled in UI.
    try:
        if os.path.exists("data"):
            shutil.rmtree("data")
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(".")
        return True
    except Exception as e:
        print(e)
        return False

# Tier colors mapped to 10-point intervals
TIER_COLORS = {
    "91~100": "#FF7043",
    "81~90": "#FFA726",
    "71~80": "#FFEE58",
    "61~70": "#66BB6A",
    "51~60": "#42A5F5",
    "41~50": "#5C6BC0",
    "31~40": "#AB47BC",
    "21~30": "#EF5350",
    "11~20": "#8D6E63",
    "0~10": "#78909C"
}

def get_tier_label_and_color(score):
    config = load_config()
    custom_colors = config.get("colors", {})
    
    def get_color(label, default):
        return custom_colors.get(label, default)

    if score >= 91: return "91~100", get_color("91~100", TIER_COLORS["91~100"])
    if score >= 81: return "81~90", get_color("81~90", TIER_COLORS["81~90"])
    if score >= 71: return "71~80", get_color("71~80", TIER_COLORS["71~80"])
    if score >= 61: return "61~70", get_color("61~70", TIER_COLORS["61~70"])
    if score >= 51: return "51~60", get_color("51~60", TIER_COLORS["51~60"])
    if score >= 41: return "41~50", get_color("41~50", TIER_COLORS["41~50"])
    if score >= 31: return "31~40", get_color("31~40", TIER_COLORS["31~40"])
    if score >= 21: return "21~30", get_color("21~30", TIER_COLORS["21~30"])
    if score >= 11: return "11~20", get_color("11~20", TIER_COLORS["11~20"])
    return "0~10", get_color("0~10", TIER_COLORS["0~10"])

def get_contrast_color(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if luminance > 0.5 else "#FFFFFF"

def group_games_by_tier(games, order='desc'):
    distinct_scores = set(g['score'] for g in games)
    use_exact_score = len(distinct_scores) <= 10
    
    tiers = {}
    for g in games:
        score = g['score']
        if use_exact_score:
            label = str(score)
            _, color = get_tier_label_and_color(score)
        else:
            label, color = get_tier_label_and_color(score)
            
        if label not in tiers:
            tiers[label] = {"color": color, "games": [], "is_range": not use_exact_score}
        tiers[label]["games"].append(g)
    
    # Sort tiers numerically
    def tier_sort_key(label):
        if '~' in label:
            return int(label.split('~')[0])
        try:
            return int(label)
        except:
            return 0
        
    sorted_labels = sorted(tiers.keys(), key=tier_sort_key, reverse=(order == 'desc'))
    return tiers, sorted_labels

def export_tier_list(games, dest_path, theme="dark"):
    # games is a list of dicts from database
    width = 1200
    bg_color = "#1E1E1E" if theme == "dark" else "#F0F2F5"
    card_bg = "#333333" if theme == "dark" else "#FFFFFF"
    title_bg = "#222222" if theme == "dark" else "#E4E7ED"
    text_color = "#FFFFFF" if theme == "dark" else "#2C3E50"
    
    label_width = 80
    card_w, card_h = 130, 200
    padding = 20
    gap = 10
    
    # Try to load font
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
    config = load_config()
    lang = config.get("language", "한국어")
    
    font_name = "NotoSansJP.otf" if lang == "日本語" else "NotoSansKR.otf"
    font_path = os.path.join(base_path, "assets", font_name)
    # Fallback to KR if JP font missing
    if not os.path.exists(font_path):
        font_path = os.path.join(base_path, "assets", "NotoSansKR.otf")
        
    try:
        font_large = ImageFont.truetype(font_path, 20)
        font_small = ImageFont.truetype(font_path, 11)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    tiers, sorted_labels = group_games_by_tier(games)
    
    # Calculate height
    row_heights = []
    cards_per_line = (width - padding*2 - label_width - padding) // (card_w + gap)
    
    for label in sorted_labels:
        n_games = len(tiers[label]["games"])
        lines = (n_games - 1) // cards_per_line + 1
        row_h = padding*2 + lines * card_h + (lines - 1) * gap
        # Minimum row height
        row_h = max(row_h, 100)
        row_heights.append(row_h)
    
    total_height = padding + sum(h + gap for h in row_heights)
    
    img = Image.new("RGB", (width, total_height), bg_color)
    draw = ImageDraw.Draw(img)
    
    current_y = padding
    
    for idx, label in enumerate(sorted_labels):
        row_h = row_heights[idx]
        color = tiers[label]["color"]
        tier_games = tiers[label]["games"]
        
        # Draw label background
        draw.rectangle([padding, current_y, padding + label_width, current_y + row_h], fill=color)
        
        # Draw label text (centered vertically)
        # Using textbbox to center text
        bbox = draw.textbbox((0,0), label, font=font_large)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = padding + (label_width - tw) / 2
        ty = current_y + (row_h - th) / 2
        draw.text((tx, ty), label, fill="#000000", font=font_large)
        
        # Draw cards
        cx, cy = padding + label_width + padding, current_y + padding
        for i, g in enumerate(tier_games):
            line_idx = i // cards_per_line
            col_idx = i % cards_per_line
            
            x = cx + col_idx * (card_w + gap)
            y = cy + line_idx * (card_h + gap)
            
            # Draw card bg
            draw.rectangle([x, y, x + card_w, y + card_h], fill=card_bg)
            
            # Draw cover
            cover_path = g.get('cover_image_path')
            if cover_path and os.path.exists(cover_path):
                try:
                    cover_img = Image.open(cover_path).convert("RGB")
                    # Crop/Resize to fit 130x160
                    cover_img = cover_img.resize((card_w, 160), Image.Resampling.LANCZOS)
                    img.paste(cover_img, (x, y))
                except:
                    pass
            
            # Draw title background
            draw.rectangle([x, y + 160, x + card_w, y + card_h], fill=title_bg)
            
            is_range = tiers[label].get("is_range", False)
            title_area_x = x
            title_area_w = card_w
            
            if is_range:
                score_str = str(g['score'])
                draw.rectangle([x + 2, y + 162, x + 30, y + 176], fill="#E53935")
                s_bbox = draw.textbbox((0,0), score_str, font=font_small)
                s_tw = s_bbox[2] - s_bbox[0]
                draw.text((x + 2 + (28 - s_tw)/2, y + 162), score_str, fill="#FFFFFF", font=font_small)
                title_area_x = x + 30
                title_area_w = card_w - 30
            
            # Draw title
            title = g['title']
            
            # Smart font selection for mixed/Japanese titles
            import re
            is_jp = bool(re.search(r'[\u3040-\u30ff]', title))
            current_font_path = os.path.join(base_path, "assets", "NotoSansJP.otf") if is_jp else font_path
            try:
                title_font = ImageFont.truetype(current_font_path, 11)
            except:
                title_font = font_small

            wrapped = textwrap.wrap(title, width=10 if is_range else 13)
            if len(wrapped) > 2:
                wrapped = wrapped[:2]
                if len(wrapped[1]) > 2:
                    wrapped[1] = wrapped[1][:-2] + ".."
                else:
                    wrapped[1] = ".."
                    
            text_y = y + 165
            for line in wrapped:
                t_bbox = draw.textbbox((0,0), line, font=title_font)
                t_tw = t_bbox[2] - t_bbox[0]
                draw.text((title_area_x + (title_area_w - t_tw)/2, text_y), line, fill=text_color, font=title_font)
                text_y += 14
            
        current_y += row_h + gap
        
    img.save(dest_path, "JPEG", quality=95)
    return True
