### All-in-One Command

```bash
# Initialize all data in the correct dependency order
flask init-all
```

## Command Options

All commands support the `--force` flag to recreate data even if it already exists:

```bash
# Force recreation of users
flask init-users --force

# Force recreation of all data
flask init-all --force
```

## Command Dependencies

1. `init-users` (no dependencies)
2. `init-academic-data` (no dependencies)
3. `init-pricing` (requires academic data)
4. `init-services` (requires pricing data)
5. `init-content` (requires users and services)
6. `init-blog` (no dependencies)

The `init-all` command handles these dependencies automatically.

# Initialize FAQs from default file
flask init-faqs

--replace to update existing FAQs
--backup/--no-backup to control backups
--verbose for detailed output
--dry-run for testing

# Initialize with custom file and replace existing
flask init-faqs -f custom_faqs.yaml --replace

# Dry run to see what would happen
flask init-faqs --dry-run

# List all FAQs
flask list-faqs

# List FAQs from specific category
flask list-faqs -c "Quality"

# Export FAQs as JSON
flask list-faqs --format json

# Clear all FAQs (with confirmation)
flask clear-faqs
