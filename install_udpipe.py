"""
Скрипт для установки UDPipe и загрузки модели
"""
import subprocess
import sys

print("=" * 60)
print("УСТАНОВКА UDPIPE")
print("=" * 60)

# Устанавливаем зависимости
print("\n1. Установка ufal.udpipe и conllu...")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ufal.udpipe>=1.2.0", "conllu>=4.5"])
    print("✓ Установлено успешно")
except Exception as e:
    print(f"✗ Ошибка установки: {e}")
    exit(1)

# Загружаем модель
print("\n2. Загрузка russian-syntagrus модели...")
try:
    from dependency_parser import get_parser
    parser = get_parser()
    if parser and parser.pipeline:
        print("✓ Модель загружена успешно")
    else:
        print("✗ Не удалось загрузить модель")
        exit(1)
except Exception as e:
    print(f"✗ Ошибка: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✓ ГОТОВО! Теперь можно запускать тесты")
print("=" * 60)
