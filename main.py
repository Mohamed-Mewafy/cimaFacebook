import os
import sys
import json
import requests
from yt_dlp import YoutubeDL

# =================CONFIGURATION================
# قراءة المفاتيح بأمان من البيئة (سواء جهازك أو جيت هاب)
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "cebc63c38c381423c4ba63134d073a93")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
PAGE_ID = "401289663059335"
SITE_URL = "https://cimaspace.site"

HISTORY_FILE = "posted_movies.json"
FAILED_FILE = "failed_movies.json"
# ==============================================
def load_list(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_list(filename, data_list):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

def get_next_unposted_media():
    history = load_list(HISTORY_FILE)
    failed = load_list(FAILED_FILE)
    
    url_en = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}&language=en-US"
    
    try:
        response_en = requests.get(url_en).json().get('results', [])
        
        for movie in response_en:
            movie_id = movie.get('id')
            title_en = movie.get('title') or movie.get('name')
            
            if not title_en or title_en in history or title_en in failed:
                continue
                
            url_details_ar = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=ar"
            details_ar = requests.get(url_details_ar).json()
            
            overview_ar = details_ar.get('overview', '')
            if not overview_ar or len(overview_ar) < 20:
                overview_ar = movie.get('overview', 'لا توجد قصة متاحة.')
                
            release_date = details_ar.get('release_date') or movie.get('release_date', '')
            vote_average = round(details_ar.get('vote_average') or movie.get('vote_average', 0), 1)
            
            return title_en, overview_ar, release_date, vote_average
                
    except Exception as e:
        print(f"[-] خطأ في الاتصال بـ TMDB: {e}")
        
    return None, None, None, None

def download_trailer(media_title):
    print(f"[*] جاري البحث وتحميل التريلر لـ: {media_title} ...")
    output_filename = "trailer.mp4"
    
    if os.path.exists(output_filename):
        os.remove(output_filename)
        
    ydl_opts = {
        'format': 'best[height<=720]',
        'outtmpl': output_filename,
        'noplaylist': True,
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android']}}
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch1:{media_title} official trailer"
            ydl.download([search_query])
            
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
            print("[+] تم تحميل التريلر بنجاح!")
            return output_filename
    except Exception as e:
        print(f"[-] خطأ في التحميل من يوتيوب: {e}")
    return None

def post_to_facebook(video_path, title, overview, release_date, vote_average):
    print("[*] جاري النشر على الفيسبوك...")
    url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/videos"
    
    year = release_date.split("-")[0] if release_date else "جديد"
    
    caption = (
        f"🔥 حصريا علي سيما سبيس\n"
        f"🎬 {title} ({year})\n\n"
        f"⭐ التقييم العالمي: {vote_average} / 10\n"
        f"📖 قصة الفيلم: {overview}\n\n"
        f"🍿 اتفرج على الفيلم كامل وبأعلى جودة حصرياً عبر منصتنا:\n"
        f"🔗 {SITE_URL}\n\n"
        f"📢 انضم لقناة التليجرام عشان يوصلك كل جديد أول بأول:\n"
        f"🔗 https://t.me/cimaspace_site\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"#CimaSpace  #سيما_سبيس  #أفلام_جديدة  #افلام_اجنبية  #اكسبلور  #سينما  #افلام_اكشن  #موقع_سيما  #تريند_السنة  #Movies  #BoxOffice  #Cinema"
    )

    payload = {
        'description': caption,
        'access_token': PAGE_ACCESS_TOKEN
    }
    
    try:
        with open(video_path, 'rb') as video_file:
            files = {'source': video_file}
            response = requests.post(url, data=payload, files=files)
            result = response.json()
            
            if 'id' in result:
                print(f"[+] تم نشر التريلر بنجاح برقم ID: {result['id']}")
                return True
            else:
                print(f"[-] فشل النشر: {result}")
    except Exception as e:
        print(f"[-] حدث خطأ أثناء الاتصال بـ Graph API: {e}")
    return False

def cleanup(files):
    for f in files:
        if os.path.exists(f):
            try:
                os.path.remove(f)
            except:
                pass

if __name__ == "__main__":
    print("=== تنفيذ مهمة نشر فيلم واحد (CimaSpace Bot) ===")
    
    title, overview, release_date, vote_average = get_next_unposted_media()
    if not title:
        print("[-] لا توجد أفلام جديدة متاحة حالياً.")
        sys.exit(0)
        
    print(f"[+] الفيلم المستهدف: {title}")
    
    raw_video = download_trailer(title)
    if not raw_video:
        print("[-] خطأ في التحميل، تسجيل في القائمة السوداء...")
        failed_list = load_list(FAILED_FILE)
        if title not in failed_list:
            failed_list.append(title)
            save_list(FAILED_FILE, failed_list)
        sys.exit(0)
        
    is_published = post_to_facebook(raw_video, title, overview, release_date, vote_average)
    
    if is_published:
        history = load_list(HISTORY_FILE)
        history.append(title)
        save_list(HISTORY_FILE, history)
        print("[+] تم الحفظ وتحديث السجل بنجاح.")
        
    cleanup([raw_video])
    print("=== انتهت المهمة وأغلق السكربت بنجاح ===")