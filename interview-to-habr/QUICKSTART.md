# Quick Start Guide

## Setup (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key
export GEMINI_API_KEY="your-gemini-api-key"

# 3. Test installation
python main.py diagnose
```

## Usage

### Simple workflow

```bash
# Create project from file
python main.py new interview.docx --name my_interview

# Process through all stages
python main.py process ./projects/my_interview

# View result
cat ./projects/my_interview/output/final_article.md
```

### Advanced usage

```bash
# List all projects
python main.py projects

# Run specific stage
python main.py stage ./projects/my_interview 5

# Run stages 2-7 only
python main.py process ./projects/my_interview --from-stage 2 --to-stage 7

# Generate specific materials
python main.py process ./projects/my_interview \
  --from-stage 9 \
  --materials tg_vk_post \
  --materials email_announce
```

## Custom Prompts

### Global custom prompt

```bash
# Create custom format prompt
mkdir -p prompts
cat > prompts/02_format.md << 'EOF'
# Custom formatting rules

Format the transcript with these rules:
- Use **Speaker:** format
- Short paragraphs (2-3 sentences)
- Preserve all technical terms
EOF

# Next run will use this prompt automatically!
python main.py stage ./projects/my_interview 2
```

### Project-specific prompt

```bash
# Override for specific project
mkdir -p projects/my_interview/prompts
cp prompts/02_format.md projects/my_interview/prompts/
vim projects/my_interview/prompts/02_format.md  # Edit as needed
```

## Pipeline Stages

| Stage | Description | Output |
|-------|-------------|--------|
| 1 | Load file | `01_loaded.md` |
| 2 | Format transcript | `02_formatted.md` |
| 3 | Compare & correct | `03_corrected.md` |
| 4 | Create plan | `04_plan.json` |
| 5 | Write sections | `05_sections/*.md` |
| 6 | Merge sections | `06_merged.md` |
| 7 | Literary edit | `07_edited.md` |
| 8 | Marketing analysis | `08_analysis.md` |
| 9 | Select materials | (state update) |
| 10 | Generate materials | `output/materials/*.md` |

## Troubleshooting

### API Key Issues

```bash
# Check if set
echo $GEMINI_API_KEY

# Set temporarily
export GEMINI_API_KEY="your-key"

# Set permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export GEMINI_API_KEY="your-key"' >> ~/.bashrc
```

### Python Version

```bash
# Check version (needs 3.11+)
python --version

# Use specific version if needed
python3.11 main.py diagnose
```

### Missing Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install google-generativeai textual rich python-docx pyyaml click pydantic
```

## Tips

1. **Start small**: Test with a short transcript first
2. **Check each stage**: Review intermediate outputs
3. **Customize prompts**: Adjust prompts for your specific needs
4. **Save projects**: Projects are saved automatically, continue anytime
5. **Monitor tokens**: Use `python main.py projects` to see token usage

## Next Steps

- Read full documentation: `README.md`
- Explore project structure: `projects/my_interview/`
- Customize prompts: `prompts/`
- Check technical spec: See original ТЗ for architecture details
