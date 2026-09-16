from pathlib import Path
import subprocess

OUTPUT = Path("matchwire_test_short.mp4")

WIDTH = 1080
HEIGHT = 1920
DURATION = 30

cmd = [
    "ffmpeg",
    "-y",
    "-f", "lavfi",
    "-i", f"color=c=0x0b1014:s={WIDTH}x{HEIGHT}:d={DURATION}:r=30",
    "-vf",
    (
        "drawbox="
        "x=70:y=650:w=940:h=620:"
        "color=0x151d23@1:"
        "t=fill,"
        "drawbox="
        "x=70:y=650:w=940:h=8:"
        "color=0x00d4aa@1:"
        "t=fill,"
        "drawtext="
        "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        "text='MATCHWIRE':"
        "fontcolor=white:"
        "fontsize=86:"
        "x=(w-text_w)/2:"
        "y=760,"
        "drawtext="
        "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='FOOTBALL NEWS ALERTS':"
        "fontcolor=0x00d4aa:"
        "fontsize=42:"
        "x=(w-text_w)/2:"
        "y=875,"
        "drawtext="
        "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='FAST  |  RELIABLE  |  SOURCE-LINKED':"
        "fontcolor=white:"
        "fontsize=30:"
        "x=(w-text_w)/2:"
        "y=970"
    ),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    str(OUTPUT),
]

print("🎬 Creating improved Matchwire Short...")

subprocess.run(cmd, check=True)

print("\n✅ Improved Short created!")
print(f"📁 File: {OUTPUT}")
print(f"📐 Size: {WIDTH}x{HEIGHT}")
print(f"⏱️ Duration: {DURATION} seconds")
