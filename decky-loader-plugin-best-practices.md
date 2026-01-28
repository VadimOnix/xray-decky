# Лучшие практики разработки плагинов Decky Loader

> Документ создан на основе анализа официальной документации, шаблонов и сообщества разработчиков Decky Loader (январь 2026)

## Содержание

1. [Структура проекта](#структура-проекта)
2. [Метаданные плагина](#метаданные-плагина)
3. [Frontend разработка (TypeScript/React)](#frontend-разработка-typescriptreact)
4. [Backend разработка (Python)](#backend-разработка-python)
5. [Сборка и распространение](#сборка-и-распространение)
6. [Безопасность и производительность](#безопасность-и-производительность)
7. [Рекомендации по обновлениям](#рекомендации-по-обновлениям)

---

## Структура проекта

### Базовая структура плагина

```
pluginname/
├── assets/              # Изображения и другие ресурсы
├── defaults/            # Конфигурационные файлы и шаблоны (опционально)
├── backend/             # Backend код (если используется)
│   ├── src/            # Исходный код backend
│   └── out/            # Скомпилированные бинарники (создается при сборке)
├── py_modules/         # Python модули (если используются)
├── src/                # Frontend TypeScript код
│   └── index.tsx       # Главная точка входа
├── main.py             # Backend Python код (если используется)
├── plugin.json         # Метаданные плагина [ОБЯЗАТЕЛЬНО]
├── package.json        # Метаданные для pnpm [ОБЯЗАТЕЛЬНО]
├── README.md           # Описание проекта (рекомендуется)
├── LICENSE(.md)        # Лицензия [ОБЯЗАТЕЛЬНО]
└── tsconfig.json       # Конфигурация TypeScript
```

### Быстрый старт

1. Используйте официальный [Decky Plugin Template](https://github.com/SteamDeckHomebrew/decky-plugin-template)
2. Нажмите "Use this Template" на GitHub для создания нового репозитория
3. Клонируйте созданный репозиторий

---

## Метаданные плагина

### plugin.json

Обязательный файл для каждого плагина. Содержит:

```json
{
  "name": "Название плагина",
  "author": "Ваше имя",
  "flags": [
    "debug", // Включает авто-перезагрузку и отладку
    "root" // Запуск от root (ИСПОЛЬЗУЙТЕ ТОЛЬКО ПРИ НЕОБХОДИМОСТИ!)
  ],
  "publish": {
    "tags": ["tag1", "tag2"],
    "description": "Краткое описание плагина",
    "image": "https://example.com/plugin-image.png" // Должно быть PNG!
  }
}
```

**Важные замечания:**

- Флаг `"root"` следует использовать только когда это действительно необходимо
- Изображение для store должно быть в формате PNG
- Теги помогают пользователям находить ваш плагин

### package.json

Обязательный файл для каждого плагина. Содержит:

```json
{
  "name": "plugin-name", // Только lowercase с дефисами
  "version": "1.0.0", // Обновляйте перед каждым PR
  "remote_binary": {
    // Опционально, для больших бинарников
    "name": "binary-name",
    "url": "https://direct-download-url",
    "sha256hash": "sha256-hash-here"
  }
}
```

**Важные замечания:**

- `name` должен быть в lowercase с дефисами (например: `donkey-farm`, не `Donkey Farm`)
- `version` необходимо обновлять перед каждым PR с обновлениями
- `remote_binary` используется для больших бинарных файлов, чтобы избежать проблем с размером zip-архивов

---

## Frontend разработка (TypeScript/React)

### Требования

- **Node.js**: v16.14 или выше
- **pnpm**: версия 9 (обязательно!)
- **@decky/ui**: библиотека React компонентов для Steam Deck UI

### Установка зависимостей

```bash
# Установка pnpm v9 (рекомендуется через npm)
sudo npm i -g pnpm@9

# Установка зависимостей проекта
pnpm i

# Сборка проекта
pnpm run build
```

### Структура frontend кода

Главная точка входа - `src/index.tsx`:

```typescript
import { definePlugin } from 'decky-frontend-lib'

export default definePlugin((serverAPI: ServerAPI) => {
  return {
    title: <div>Название плагина</div>,
    content: <Content serverAPI={serverAPI} />,
    icon: <Icon />,
  }
})
```

### Взаимодействие с Backend

Используйте `ServerAPI` для вызова backend функций:

```typescript
// Вызов backend функции
serverAPI!.callPluginMethod('my_backend_function', {
  parameter_a: 'Hello',
  parameter_b: 'World',
})
```

### Компоненты UI

Используйте компоненты из `@decky/ui` для соответствия дизайну Steam Deck:

- Компоненты основаны на React UI Steam Deck
- Документация доступна в [decky-frontend-lib](https://github.com/SteamDeckHomebrew/decky-frontend-lib)
- Примеры использования можно найти в шаблоне плагина

### Обновление библиотек

Если возникают ошибки сборки из-за устаревших библиотек:

```bash
pnpm update @decky/ui --latest
```

### Пересборка после изменений

**Важно:** После каждого изменения frontend кода необходимо пересобирать:

```bash
pnpm run build
```

Или используйте задачи VSCode/VSCodium: `setup`, `build`, `deploy`

---

## Backend разработка (Python)

### Структура backend кода

Все функции плагина определяются в классе `Plugin`:

```python
class Plugin:
    # Backend функция, вызываемая из frontend
    async def my_backend_function(self, parameter_a, parameter_b):
        print(f"{parameter_a} {parameter_b}")
        return {"result": "success"}

    # Долгоживущий код, работает все время жизни плагина
    async def _main(self):
        pass

    # Очистка при выгрузке плагина
    async def _unload(self):
        pass
```

### SettingsManager

Используйте `SettingsManager` для сохранения настроек в JSON файлы:

```python
from settings import SettingsManager
import os

# Получение директории настроек из переменной окружения
settingsDir = os.environ["DECKY_PLUGIN_SETTINGS_DIR"]
settings = SettingsManager(name="settings", settings_directory=settingsDir)
settings.read()

class Plugin:
    async def settings_read(self):
        return settings.read()

    async def settings_commit(self):
        return settings.commit()

    async def settings_getSetting(self, key: str, defaults):
        return settings.getSetting(key, defaults)

    async def settings_setSetting(self, key: str, value):
        settings.setSetting(key, value)
```

**Важно:** Не используйте `localStorage` напрямую в React - используйте SettingsManager через backend.

### Backend с бинарниками

Если ваш плагин использует собственный backend с бинарниками:

1. **Расположение исходного кода**: `backend/src/`
2. **Выходные бинарники**: `backend/out/` (создается при сборке)
3. **CI автоматически создает папку `out`**, но рекомендуется создавать её в процессе сборки

Пример Makefile:

```makefile
hello:
    mkdir -p ./out
    gcc -o ./out/hello ./src/main.c
```

**Критически важно:** Бинарники должны быть в `backend/out/`, иначе они не будут включены в дистрибутив.

### Использование defaults/ для дополнительных файлов

Папка `defaults/` используется для включения файлов, не являющихся частью стандартной сборки:

- Python библиотеки
- Конфигурационные файлы
- Другие ресурсы, необходимые плагину

**Примечание:** Это временное решение. В будущем планируется добавить whitelist в `plugin.json`.

---

## Сборка и распространение

### Структура zip-архива для распространения

```
pluginname-v1.0.0.zip
│
└── pluginname/
    ├── bin/              # Опционально: бинарники
    │   └── binary
    ├── dist/             # [ОБЯЗАТЕЛЬНО]
    │   └── index.js      # [ОБЯЗАТЕЛЬНО]
    ├── package.json      # [ОБЯЗАТЕЛЬНО]
    ├── plugin.json       # [ОБЯЗАТЕЛЬНО]
    ├── main.py           # [ОБЯЗАТЕЛЬНО, если используется Python backend]
    ├── README.md         # Рекомендуется
    └── LICENSE(.md)      # [ОБЯЗАТЕЛЬНО]
```

### Требования к лицензии

- Лицензия **обязательна** для публикации в Plugin Store
- Если лицензия требует включения текста, он должен быть в корне репозитория
- Стандартная практика: ваша лицензия сверху, оригинальная лицензия шаблона снизу

### Публикация в Plugin Store

1. Следуйте инструкциям в [decky-plugin-database](https://github.com/SteamDeckHomebrew/decky-plugin-database)
2. Откройте Pull Request, добавив ваш плагин как submodule
3. Убедитесь, что все обязательные файлы присутствуют
4. Проверьте, что версия в `package.json` обновлена

### Установка через URL

Плагины можно устанавливать через URL к zip-файлу:

- URL должен указывать на прямой доступ к zip-файлу
- Установка через URL работает только в Desktop Mode (не в Game Mode)

---

## Безопасность и производительность

### Безопасность

1. **Установка плагинов:**

   - Устанавливайте только из доверенных источников
   - Используйте официальный Plugin Store
   - Проверяйте отзывы перед установкой

2. **Разработка:**

   - Избегайте использования флага `"root"` без необходимости
   - Валидируйте все пользовательские входные данные
   - Используйте SettingsManager вместо прямого доступа к файловой системе

3. **Распространение:**
   - Включайте лицензию в репозиторий
   - Используйте `remote_binary` для больших файлов
   - Указывайте SHA256 хеши для удаленных бинарников

### Производительность

1. **Оптимизация кода:**

   - Минимизируйте количество вызовов backend функций
   - Используйте асинхронные операции где возможно
   - Избегайте блокирующих операций в `_main()`

2. **Размер плагина:**

   - Используйте `remote_binary` для файлов > 10MB
   - Оптимизируйте изображения и ресурсы
   - Удаляйте неиспользуемые зависимости

3. **UI/UX:**
   - Используйте компоненты из `@decky/ui` для нативного вида
   - Следуйте дизайн-паттернам Steam Deck UI
   - Тестируйте на реальном устройстве

---

## Рекомендации по обновлениям

### Обновление Decky Loader и плагинов

**Критически важно:**

- **Всегда обновляйте Decky Loader и плагины ПЕРЕД обновлением Steam**
- Обновления Steam могут сломать совместимость
- Если используете Steam beta, используйте Decky prerelease для тестирования

### Версионирование

1. Обновляйте `version` в `package.json` перед каждым PR
2. Используйте семантическое версионирование (SemVer)
3. Включайте changelog в описании обновлений

### Тестирование

1. Тестируйте на реальном Steam Deck, а не только в эмуляторе
2. Проверяйте совместимость с последней версией Decky Loader
3. Тестируйте обновления перед публикацией

---

## Дополнительные ресурсы

- [Официальный шаблон плагина](https://github.com/SteamDeckHomebrew/decky-plugin-template)
- [Документация Decky Loader Wiki](https://wiki.deckbrew.xyz/en/plugin-dev/getting-started)
- [decky-frontend-lib (@decky/ui)](https://github.com/SteamDeckHomebrew/decky-frontend-lib)
- [Plugin Database](https://github.com/SteamDeckHomebrew/decky-plugin-database)
- [Decky Loader Repository](https://github.com/SteamDeckHomebrew/decky-loader)

---

## Чеклист перед публикацией

- [ ] Все обязательные файлы присутствуют (`plugin.json`, `package.json`, `LICENSE`)
- [ ] Версия в `package.json` обновлена
- [ ] Плагин протестирован на реальном Steam Deck
- [ ] Backend бинарники (если есть) находятся в `backend/out/`
- [ ] Лицензия включена в репозиторий
- [ ] README.md содержит описание и инструкции
- [ ] Изображение для store в формате PNG
- [ ] Все зависимости актуальны (`pnpm update @decky/ui --latest`)
- [ ] Код соответствует стандартам сообщества
- [ ] Плагин не требует root без необходимости

---

**Последнее обновление:** Январь 2026  
**Источники:** Официальная документация Decky Loader, шаблоны плагинов, сообщество разработчиков
