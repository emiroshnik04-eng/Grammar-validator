#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test for genitive case fix"""

from check_catalog import normalize_other_pattern

# Test case 1: "Тип плюшевой игрушки"
print("=" * 60)
print("Test 1: Tip plyushevoi igrushki (genitive)")
param_name = "Тип плюшевой игрушки"
value = "Другой Тип плюшевой игрушка"  # Wrong: игрушка

result = normalize_other_pattern(param_name, value)

if result:
    old, new = result
    print(f"CORRECTION: '{old}' -> '{new}'")

    expected = "Другой тип плюшевой игрушки"  # Correct: игрушки (genitive)
    if new == expected:
        print("PASS: Genitive case preserved!")
    else:
        print(f"FAIL: Expected '{expected}', got '{new}'")
else:
    print("ERROR: No correction returned")

print()

# Test case 2: "марка машинки" (from earlier fix)
print("=" * 60)
print("Test 2: marka mashinki (genitive)")
param_name2 = "марка машинки"
value2 = "Другой марка машинки"

result2 = normalize_other_pattern(param_name2, value2)

if result2:
    old2, new2 = result2
    print(f"CORRECTION: '{old2}' -> '{new2}'")

    expected2 = "Другая марка машинки"
    if new2 == expected2:
        print("PASS: Gender and case correct!")
    else:
        print(f"FAIL: Expected '{expected2}', got '{new2}'")
else:
    print("ERROR: No correction returned")
