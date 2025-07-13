import json

# Quick taxonomy analysis
taxonomy_path = "/Users/sander.vandenberg/src/marktplaatser/taxonomy-mpnl.json"

print(f"📁 Checking taxonomy file: {taxonomy_path}")

try:
    with open(taxonomy_path, 'r') as f:
        # Read just the beginning to understand structure
        content = f.read(2000)  # First 2KB
        print("📄 First 2000 characters:")
        print("=" * 60)
        print(content)
        print("=" * 60)
        
except Exception as e:
    print(f"❌ Error: {e}")

print("✅ Quick check complete")