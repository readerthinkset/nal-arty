import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Gorgeous Nail Art Tutorial You Need to Try 💅",
        "Simple Manicure Ideas for Short Nails",
        "How to Do French Tips Perfectly Every Time",
        "5 Easy Nail Art Designs for Beginners",
        "Chrome Nails Trend 2025 - Step by Step ✨",
        "Beautiful Gel Nails at Home - DIY Manicure",
        "Nail Art Compilation - Satisfying Designs 🎨",
        "Ombre Nails Tutorial - Easy Gradient Effect",
        "Tiny Nail Art - Cute Designs for Short Nails",
        "Nail Care Routine for Strong & Healthy Nails",
        "The Cutest Spring Nail Art Ideas 🌸",
        "1 Minute Nail Art - Quick & Easy Designs",
        "Glitter Nails That Will Make You Shine ✨",
        "Nail Transformation - Before and After Manicure",
        "Acrylic Nails vs Gel Nails - Which is Better?",
    ]

    fallback_descriptions = [
        "Ready for some nail inspiration? 💅 Watch this satisfying nail art tutorial that will transform your hands! From simple designs to intricate patterns — there's something for everyone. Which nail style is your favorite? Comment below! Don't forget to save this for your next nail appointment! 📌 #nailart #nails #manicure #nailtutorial #naildesigns #nailinspo #gelnails #acrylicnails #diynails #nailsoftheday",
        "You don't need long nails to have beautiful nail art! 💕 These cute designs are perfect for short nails and super easy to do at home. Whether you like minimal or bold looks, these ideas will inspire you. Tag a friend who loves nails as much as you do! 👇 #shortnails #nailartideas #manicure #diynails #nailtutorial #cutenails #nails #nailinspo #easynailart #naildesigns",
        "French tips will never go out of style! 🤍 Learn how to get the perfect French manicure at home with this step-by-step tutorial. No expensive salon visits needed! From classic white tips to colorful variations — we cover it all. Save this for your next DIY manicure day! 💅 #frenchtips #frenchmanicure #nailtutorial #diynails #classicnails #manicure #nails #nailart",
        "Chrome nails are taking over 2025! ✨ Watch how to achieve this mirror-like finish at home. The metallic effect is absolutely stunning and surprisingly easy to do. Which color chrome would you try? Comment your fave! 🔮 #chromenails #nailtrends2025 #nailart #mirrornails #metallicnails #gelnails #nailtutorial #nailinspo",
        "Gel nails at home — yes, it's possible! 🌟 This complete guide walks you through everything from prep to cure. Say goodbye to expensive salon trips and hello to salon-quality nails from your own bathroom. Like if you prefer DIY nails! 💪 #gelnails #diynails #gelnailtutorial #nails #manicure #nailart #gelpolish #nailsathome",
        "The most satisfying nail art compilation you'll watch today 🎨 Watch mesmerizing designs come to life — from marble patterns to hand-painted florals. Each design is a tiny masterpiece. This is ASMR for nail lovers! Which one would you wear? Tell us! 🗣️ #satisfyingnails #nailartcompilation #naildesigns #nailart #asmrnails #satisfying #manicure",
        "Ombre nails made EASY 🌈 Follow this simple gradient technique to create stunning fade effects. Whether you love soft pastels or bold neons, the ombre look works for every style. Pin this for your next nail session! 📍 #ombrenails #gradientnails #nailarttutorial #diynails #colorfulnails #nailinspo #nails #manicure #easynailart",
        "Small nails, BIG style! 💖 Just because your nails are short doesn't mean you can't have fun. These tiny nail art designs are proof that less is more. Clean, elegant, and so cute. Follow for more short nail inspiration! ✨ #shortnails #cutenaildesigns #minimalnails #nailartideas #diynails #nails #manicure #tinyart",
        "Healthy nails are beautiful nails 🌿 Here's my complete nail care routine for growing strong, long, and healthy nails. From cuticle oil to the right filing technique — these tips will transform your nails. Start your nail journey today! Like to save for later! 💚 #nailcare #healthynails #nailgrowth #nailroutine #cuticleoil #nails #manicure #nailsupplies",
        "Spring is in the air! 🌸 These nail art ideas will have you ready for the season of blooms and pastels. From floral patterns to soft pink gradients — spring nails hit different. Which design screams 'spring' to you? Comment below! 🌷 #springnails #floralnails #pastelnails #nailartideas #seasonalnails #nails #manicure #nailinspo",
        "Need nail art in a rush? ⏰ These 1-minute designs are perfect for when you're short on time but still want cute nails. Quick, easy, and gorgeous — what more could you want? Tag a friend who's always running late but loves nails! 🏃‍♀️ #quicknails #easynailart #1minutenails #diynails #nailtutorial #simple #nails #manicure",
        "Glitter is always the answer! ✨ These sparkly nail designs will make your hands the center of attention. Perfect for parties, holidays, or just because you deserve some shine. The more glitter, the better! Drop a ✨ if you're a glitter nail lover! #glitternails #sparklenails #nailart #glamnails #partyready #holidaynails #nails #manicure",
        "The nail transformation you didn't know you needed 🔄 Watch this incredible before and after — from broken, damaged nails to a gorgeous manicure. Nails can heal and grow stronger with the right care. Don't give up on your nail journey! Share your progress pics below! 📸 #nailtransformation #beforeandafter #nailgrowth #nailcare #nails #manicure #nailjourney",
        "Acrylic vs Gel — which one should you choose? 🤔 We break down the pros and cons of both so you can make the right decision for your nails. From durability to removal process, we cover it all. Which do you prefer? Comment A for acrylic or G for gel! 💬 #acrylicvsgel #nailtypes #nails #acrylicnails #gelnails #nailcare #manicure #nailtips",
        "Your nails deserve the best cuticle care! 🧴 Learn how to properly care for your cuticles to make your manicure last longer and your nails look healthier. This simple routine makes a HUGE difference. Save this for your next self-care day! 🧖‍♀️ #cuticlecare #nailhealth #manicuretips #nailcare #nails #diynails #selfcare #nailroutine",
        "Nail art is for EVERYONE 💅 Whether you're a beginner or a pro, these designs will inspire your next manicure. Experiment with colors, patterns, and textures. Your nails are your canvas! Which design will you try first? Comment below! 🎨 #nailartforall #nails #manicure #naildesigns #nailartideas #diynails #nailinspo #creative",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "creative and inspiring — spark new nail art ideas for viewers",
        "calming and satisfying — make nail art feel relaxing and therapeutic",
        "educational and helpful — teach practical techniques anyone can use",
        "trendy and fresh — showcase the latest nail trends and styles",
        "encouraging and supportive — motivate beginners to try nail art",
        "fun and playful — keep it light and enjoyable for nail lovers",
        "professional and polished — share expert-level tips and tricks",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Nail Artsy'. "
        f"The page is all about nail art, manicures, and nail care — featuring tutorials, design ideas, nail trends, product reviews, and satisfying nail transformations. "
        f"It's creative, inspiring, and perfect for anyone who loves beautiful nails. "
        f"Speak as a passionate nail artist who loves sharing tips, tricks, and inspiration with fellow nail enthusiasts. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), engaging, and focused on nail art and beauty. "
        f"Include engagement calls-to-action such as: "
        f"- Like if you love this nail design! "
        f"- Comment your favorite nail style! "
        f"- Share with a friend who needs nail inspo! "
        f"- Follow Nail Artsy for more nail ideas! "
        f"Include relevant hashtags in ALL LOWERCASE such as #nailart #nails #manicure #nailtutorial #naildesigns #nailinspo #gelnails #acrylicnails #diynails #nailsoftheday #nailideas #nailcare. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["nailart", "nails", "manicure", "nailtutorial", "naildesigns", "nailinspo", "gelnails", "acrylicnails", "diynails", "nailideas", "nailcare", "nailarttutorial", "cutenails", "nailsoftheday"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
