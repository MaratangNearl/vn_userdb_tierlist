import requests
import re
import os
from PyQt6.QtCore import QThread, pyqtSignal

def extract_vn_id(url_or_id):
    # If it's already an ID like v17
    if re.match(r'^v\d+$', url_or_id.strip()):
        return url_or_id.strip()
    
    # Extract from URL e.g. https://vndb.org/v17
    match = re.search(r'vndb\.org/(v\d+)', url_or_id)
    if match:
        return match.group(1)
    
    return None

class VndbFetchThread(QThread):
    finished = pyqtSignal(str, str) # title, image_path
    error = pyqtSignal(str)

    def __init__(self, vn_input):
        super().__init__()
        self.vn_input = vn_input

    def run(self):
        vn_id = extract_vn_id(self.vn_input)
        if not vn_id:
            self.error.emit("VNDB ID를 찾을 수 없습니다.")
            return

        url = "https://api.vndb.org/kana/vn"
        payload = {
            "filters": ["id", "=", vn_id],
            "fields": "title, image.url, image.dims"
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("results"):
                result = data["results"][0]
                title = result.get("title", "")
                image_info = result.get("image", {})
                image_url = image_info.get("url")
                
                if image_url:
                    img_resp = requests.get(image_url, timeout=10)
                    img_resp.raise_for_status()
                    
                    covers_dir = os.path.join("data", "covers")
                    os.makedirs(covers_dir, exist_ok=True)
                    
                    # Some images might be different formats, but VNDB usually provides jpg.
                    # We will save it as jpg.
                    image_path = os.path.join(covers_dir, f"{vn_id}.jpg")
                    with open(image_path, "wb") as f:
                        f.write(img_resp.content)
                    
                    self.finished.emit(title, image_path)
                else:
                    self.error.emit("표지 이미지 URL을 찾을 수 없습니다.")
            else:
                self.error.emit("결과를 찾을 수 없습니다.")
        except Exception as e:
            self.error.emit(f"API 요청 실패: {e}")
