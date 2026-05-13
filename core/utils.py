import os
import shutil
from datetime import datetime
import zipfile
import sys
from PIL import Image, ImageDraw, ImageFont
import textwrap

def backup_data(dest_folder):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"vnlist_backup_{now}.zip"
    zip_path = os.path.join(dest_folder, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add db
        db_path = os.path.join("data", "vnlist.db")
        if os.path.exists(db_path):
            zipf.write(db_path, os.path.join("data", "vnlist.db"))
        
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
    if score >= 91: return "91~100", TIER_COLORS["91~100"]
    if score >= 81: return "81~90", TIER_COLORS["81~90"]
    if score >= 71: return "71~80", TIER_COLORS["71~80"]
    if score >= 61: return "61~70", TIER_COLORS["61~70"]
    if score >= 51: return "51~60", TIER_COLORS["51~60"]
    if score >= 41: return "41~50", TIER_COLORS["41~50"]
    if score >= 31: return "31~40", TIER_COLORS["31~40"]
    if score >= 21: return "21~30", TIER_COLORS["21~30"]
    if score >= 11: return "11~20", TIER_COLORS["11~20"]
    return "0~10", TIER_COLORS["0~10"]

def group_games_by_tier(games):
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
            tiers[label] = {"color": color, "games": []}
        tiers[label]["games"].append(g)
    
    # Sort tiers descending
    def tier_sort_key(label):
        if '~' in label:
            return int(label.split('~')[0])
        return int(label)
        
    sorted_labels = sorted(tiers.keys(), key=tier_sort_key, reverse=True)
    return tiers, sorted_labels

def export_tier_list(games, dest_path):
    # games is a list of dicts from database
    width = 1200
    bg_color = "#1E1E1E"
    label_width = 80
    card_w, card_h = 120, 190
    padding = 20
    gap = 10
    
    # Try to load font
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
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
            draw.rectangle([x, y, x + card_w, y + card_h], fill="#333333")
            
            # Draw cover
            cover_path = g.get('cover_image_path')
            if cover_path and os.path.exists(cover_path):
                try:
                    cover_img = Image.open(cover_path).convert("RGB")
                    # Crop/Resize to fit 120x150
                    cover_img = cover_img.resize((card_w, 150), Image.Resampling.LANCZOS)
                    img.paste(cover_img, (x, y))
                except:
                    pass
            
            # Draw title background
            draw.rectangle([x, y + 150, x + card_w, y + card_h], fill="#222222")
            
            # Draw title
            title = g['title']
            wrapped = textwrap.wrap(title, width=12)
            if len(wrapped) > 2:
                wrapped = wrapped[:2]
                if len(wrapped[1]) > 2:
                    wrapped[1] = wrapped[1][:-2] + ".."
                else:
                    wrapped[1] = ".."
                    
            text_y = y + 155
            for line in wrapped:
                t_bbox = draw.textbbox((0,0), line, font=font_small)
                t_tw = t_bbox[2] - t_bbox[0]
                draw.text((x + (card_w - t_tw)/2, text_y), line, fill="#FFFFFF", font=font_small)
                text_y += 14
            
        current_y += row_h + gap
        
    img.save(dest_path, "JPEG", quality=95)
    return True
