import json
import os

class I18n:
    def __init__(self):
        # Determine locales directory absolute path relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.locales_dir = os.path.join(base_dir, 'locales')
        self.translations = {}
        self._load_translations()

    def _load_translations(self):
        for lang in ['ru', 'uz', 'en']:
            path = os.path.join(self.locales_dir, f'{lang}.json')
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.translations[lang] = json.load(f)
                except Exception as e:
                    print(f"CRITICAL: Failed to load locale {lang}: {e}")
            else:
                print(f"WARNING: Locale file not found: {path}")

    def get(self, key: str, lang: str = 'ru', **kwargs) -> str:
        lang_data = self.translations.get(lang, self.translations.get('ru', {}))
        text = lang_data.get(key, self.translations.get('ru', {}).get(key, key))
        try:
            return text.format(**kwargs)
        except Exception as e:
            print(f"ERROR: Translation format failed for key '{key}': {e}")
            return text

i18n = I18n()
