#!/usr/bin/env python3
"""Debug script for normalize_other_pattern issue"""

import pymorphy3

morph = pymorphy3.MorphAnalyzer()

def _first_parse(word: str):
    """Get first parse result"""
    parses = morph.parse(word)
    return parses[0] if parses else None

def extract_head_noun(phrase: str) -> str:
    """Extract grammatical head (main noun) from a phrase."""
    words = phrase.split()
    if not words:
        return phrase

    # First, try to find the first noun in nominative case
    for word in words:
        p = _first_parse(word)
        if p and "NOUN" in p.tag and "nomn" in p.tag:
            return word

    # If no nominative noun, take first noun (any case)
    for word in words:
        p = _first_parse(word)
        if p and "NOUN" in p.tag:
            return word

    # Fallback to first word
    return words[0]

# TEST: марка машинки
param_name = "марка машинки"
param_value = "Другой марка машинки"

print("=" * 60)
print(f"Testing: param_name='{param_name}', value='{param_value}'")
print("=" * 60)

# Step 1: Extract head noun
head = extract_head_noun(param_name)
print(f"\n1. Head noun: '{head}'")

# Step 2: Parse head noun (with ALL parses)
print(f"2. All parses for '{head}':")
all_parses = morph.parse(head)
for i, p in enumerate(all_parses):
    print(f"   [{i}] {p.tag} | normal: {p.normal_form}")

# Select best parse (prefer nomn + non-Name)
best_parse = None
for p in all_parses:
    if "NOUN" in p.tag and "nomn" in p.tag and "Name" not in p.tag:
        best_parse = p
        print(f"\n   OK Selected parse [nomn, non-Name]: {p.tag}")
        break

if not best_parse:
    for p in all_parses:
        if "NOUN" in p.tag and "nomn" in p.tag:
            best_parse = p
            print(f"\n   OK Selected parse [nomn]: {p.tag}")
            break

if not best_parse:
    best_parse = all_parses[0]
    print(f"\n   OK Selected first parse: {best_parse.tag}")

if best_parse:
    print(f"\n   Gender: ", end="")
    if "masc" in best_parse.tag:
        print("MASCULINE")
        gender = "masc"
    elif "femn" in best_parse.tag:
        print("FEMININE")
        gender = "femn"
    elif "neut" in best_parse.tag:
        print("NEUTER")
        gender = "neut"
    else:
        print("UNKNOWN")
        gender = "masc"
else:
    print("2. ERROR: Could not parse head noun")
    gender = "masc"

# Step 3: Inflect "другой" to match gender
print(f"\n3. Inflecting 'другой' to {gender}:")
base = _first_parse("другой")
if base:
    print(f"   Original: {base.word} [{base.tag}]")
    grammemes = {gender, "sing", "nomn"}
    inflected = base.inflect(grammemes)
    if inflected:
        print(f"   Inflected: {inflected.word} [{inflected.tag}]")
        other_word = inflected.word.capitalize()
        print(f"   Capitalized: '{other_word}'")
    else:
        print("   ERROR: Could not inflect")
        other_word = "Другой"
else:
    print("   ERROR: Could not parse 'другой'")
    other_word = "Другой"

# Step 4: Build final result
correct = f"{other_word} {param_name}"
print(f"\n4. Final result: '{correct}'")
print(f"   Expected: 'Другая марка машинки'")
print(f"   Match: {correct == 'Другая марка машинки'}")

print("\n" + "=" * 60)
print("TESTING ALL WORDS IN param_name:")
print("=" * 60)
for word in param_name.split():
    p = _first_parse(word)
    if p:
        print(f"\nWord: '{word}'")
        print(f"  Tag: {p.tag}")
        print(f"  Normal form: {p.normal_form}")
