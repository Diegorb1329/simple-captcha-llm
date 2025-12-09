# SAT Certificate Lookup

Automates SAT (Mexican Tax Authority) certificate recovery using LLM-based CAPTCHA solving.

This project was created as a test implementation for research on poetic prompts and LLM behavior (inspired by "Adversarial Poetry as a Universal Single-Turn Jailbreak Mechanism in Large Language Models"). It was built to experiment with different prompt styles for CAPTCHA solving, but **this project is not actively maintained** and is provided as-is for reference.

## Quick Start

1. Install dependencies:
```bash
pip install selenium beautifulsoup4 python-dotenv openai anthropic
```

2. Set API key in `.env`:
```bash
OPENAI_API_KEY=your_key_here
# OR
ANTHROPIC_API_KEY=your_key_here
```

3. Add RFCs to `input/rfcs.csv` (one per line):
```csv
rfc,id
ABC123456XYZ,1
```
**Note:** Add your RFCs to this file before running. The file must have a `rfc` header.

4. Run:
```bash
python src/main.py
```

## Output Structure

Each run creates a folder:
```
outputs/run_TIMESTAMP/
├── captchas/          # Captcha images
├── resultados.csv     # Certificate results
└── run.log           # Execution log
```

## Usage

```bash
python src/main.py --input input/rfcs.csv --output outputs/
```

## Features

- Automated CAPTCHA solving with GPT-4 Vision or Claude
- Batch processing from CSV
- Retry logic for failed attempts
- Complete run logs and debug output

## Requirements

- Python 3.8+
- Chrome/Chromium + ChromeDriver
- OpenAI or Anthropic API key

## Project Structure

```
src/
├── main.py                    # CLI entry point
├── config.py                  # Configuration
├── captcha_solver.py          # LLM captcha solving
└── sat_certificate_lookup.py  # Core lookup logic
```

## License

GNU General Public License v3.0

This project is licensed under the GNU General Public License v3.0. See the LICENSE file for details.