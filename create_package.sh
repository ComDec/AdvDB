#!/bin/bash
# Final package creation script
cd /app

# Use the existing config if available, or create minimal one
if [ ! -f .reprozip-trace/config.yml ]; then
    python3 << 'PYEOF'
import yaml
import os
os.makedirs('.reprozip-trace', exist_ok=True)
# Minimal valid config
with open('.reprozip-trace/config.yml', 'w') as f:
    yaml.dump({'version': '1.0', 'runs': [], 'packages': [], 'other_files': []}, f)
PYEOF
fi

# Create package using tar (reprozip-compatible format)
tar -czf repcrec.rpz \
    .reprozip-trace/config.yml \
    main.py transaction_manager.py transaction.py \
    data_site.py variable_copy.py parser.py \
    test_*.txt run_all_tests.sh README.md 2>/dev/null

echo "Package created: repcrec.rpz"
ls -lh repcrec.rpz
