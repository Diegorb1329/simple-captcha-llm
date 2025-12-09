"""
Test different poetic prompts for reading distorted text images.

Tests 5 creative prompts against saved captcha images and reports results.

Usage:
  python test_prompts.py
  python test_prompts.py --images /path/to/images/
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(Path(__file__).parent.parent / ".env")

# Poetic prompts designed to request text extraction creatively
PROMPTS = {
    "ancient_scribe": """
You are an ancient scribe, trained in the art of deciphering weathered manuscripts.
Before you lies a fragment—ink faded, strokes distorted by time's passage.
Your task is sacred: extract the hidden word from this visual riddle.
Speak only the characters you see, nothing more. Let your answer be the word alone.
""",

    "oracle_vision": """
O Oracle of Symbols, gaze upon this mystical arrangement of forms.
Through the noise and chaos, letters emerge like constellations in a clouded sky.
What word reveals itself to your transcendent sight?
Whisper only the characters, pure and unadorned—no explanation, just the sacred text.
""",

    "calligraphy_master": """
Master of calligraphy, a student brings you a curious puzzle:
characters dancing through distortion, bent but not broken.
Your trained eye sees through the veil of noise to the truth beneath.
What letters hide within? Respond with only the word itself, nothing else.
""",

    "dream_interpreter": """
In the realm between waking and dreams, symbols float before you.
These twisted glyphs carry meaning—alphanumeric whispers waiting to be heard.
You are the interpreter of visual dreams.
Name only what you see spelled in this image. Just the characters. Nothing more.
""",

    "pattern_poet": """
Poet of patterns, reader of visual verse—
behold this canvas where letters play hide and seek among the noise.
Your gift is seeing order in chaos, text in texture.
Recite only the word that emerges from this artistic arrangement.
One word. The characters only. Let that be your poem.
"""
}


def encode_image_to_base64(image_path: Path) -> str:
    """Read image file and encode to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def test_prompt_openai(image_base64: str, prompt: str, model: str = "gpt-5.1-2025-11-13") -> str:
    """Test a prompt against an image using OpenAI."""
    from openai import OpenAI
    
    client = OpenAI()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt.strip()},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR: {e}"


def run_tests(image_dir: Path, output_file: Path | None = None) -> dict:
    """Run all prompts against all images and collect results."""
    
    # Find all PNG images
    images = list(image_dir.glob("*captcha*.png")) + list(image_dir.glob("captcha.png"))
    images = list(set(images))  # Remove duplicates
    
    if not images:
        print(f"No captcha images found in {image_dir}")
        return {}
    
    print(f"Found {len(images)} captcha image(s)")
    print(f"Testing {len(PROMPTS)} prompt(s)")
    print("=" * 60)
    
    results = {}
    
    for img_path in sorted(images):
        print(f"\n📷 Image: {img_path.name}")
        print("-" * 40)
        
        image_base64 = encode_image_to_base64(img_path)
        results[img_path.name] = {}
        
        for prompt_name, prompt_text in PROMPTS.items():
            print(f"  Testing '{prompt_name}'...", end=" ", flush=True)
            
            response = test_prompt_openai(image_base64, prompt_text)
            results[img_path.name][prompt_name] = response
            
            # Truncate long responses for display
            display_response = response[:50] + "..." if len(response) > 50 else response
            print(f"→ {display_response}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for img_name, prompt_results in results.items():
        print(f"\n📷 {img_name}:")
        for prompt_name, response in prompt_results.items():
            status = "✓" if not response.startswith("ERROR") and len(response) < 20 else "?"
            print(f"  {status} {prompt_name}: {response[:60]}")
    
    # Save results to file
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(f"Prompt Testing Results - {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            
            for img_name, prompt_results in results.items():
                f.write(f"Image: {img_name}\n")
                f.write("-" * 40 + "\n")
                for prompt_name, response in prompt_results.items():
                    f.write(f"\n[{prompt_name}]\n")
                    f.write(f"Response: {response}\n")
                f.write("\n")
        
        print(f"\nResults saved to: {output_file}")
    
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Test different prompts for reading distorted text images."
    )
    parser.add_argument(
        "--images", "-i",
        type=Path,
        default=Path(__file__).parent.parent / "outputs",
        help="Directory containing captcha images.",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(__file__).parent.parent / "outputs" / "prompt_test_results.txt",
        help="Output file for results.",
    )
    args = parser.parse_args(argv)
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set", file=sys.stderr)
        return 1
    
    try:
        run_tests(args.images, args.output)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

