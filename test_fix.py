#!/usr/bin/env python3
"""Quick test for the morph fix"""

from check_catalog import normalize_other_pattern

# Test case from test_cases.csv
param_name = "марка машинки"
value = "Другой марка машинки"

print("=" * 60)
print("Testing normalize_other_pattern():")
print(f"  param_name: '{param_name}'")
print(f"  value:      '{value}'")
print("=" * 60)

result = normalize_other_pattern(param_name, value)

if result:
    old, new = result
    print(f"\n✓ CORRECTION FOUND:")
    print(f"  Old: '{old}'")
    print(f"  New: '{new}'")
    print(f"\n  Expected: 'Другая марка машинки'")
    print(f"  Match: {new == 'Другая марка машинки'}")

    if new == 'Другая марка машинки':
        print("\n✅ TEST PASSED!")
    else:
        print("\n❌ TEST FAILED!")
else:
    print("\n❌ ERROR: No correction returned!")
