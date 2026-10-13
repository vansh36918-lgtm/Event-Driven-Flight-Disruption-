import httpx
import os

images_to_download = {
    "hero_jet_main.png": "https://framerusercontent.com/images/W0fE3vD6CNnkdiHpYGHM2uqaSjo.png?scale-down-to=2048",
    "jet_section_flying.png": "https://framerusercontent.com/images/9pjT93c3achHZiVib2t6EXVMfBo.png?scale-down-to=2048",
    "jet_banking_turn.png": "https://framerusercontent.com/images/CF1WxVcNAoxMtZrh7GWtbZHywQ.png?scale-down-to=2048",
    "jet_front_altitude.png": "https://framerusercontent.com/images/fdKUhlWFwWEInD1vo7mOQR4naE.png?scale-down-to=2048",
    "jet_angled_side.png": "https://framerusercontent.com/images/UegMg3elB2kI1vKzQOyY5sfeM.png?scale-down-to=2048",
    "clouds_mist.png": "https://framerusercontent.com/images/1FAvhAKn2ZlFufwll3MA2qKVdE.png?scale-down-to=2048",
    "hero_bg_cosmic.jpeg": "https://framerusercontent.com/images/XU6GL9LwDQlYz5y3cNwyiCchjw.jpeg?width=2000"
}

out_dir = os.path.join("app", "static", "images")
os.makedirs(out_dir, exist_ok=True)

with httpx.Client(timeout=30.0) as client:
    for filename, url in images_to_download.items():
        out_path = os.path.join(out_dir, filename)
        if not os.path.exists(out_path):
            print(f"Downloading {filename}...")
            r = client.get(url)
            if r.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                print(f"  [OK] Saved {filename} ({len(r.content):,} bytes)")
            else:
                print(f"  [FAIL] HTTP {r.status_code} for {url}")
        else:
            print(f"Already exists: {filename}")

print("All Framer Let's Fly 3D assets ready!")
