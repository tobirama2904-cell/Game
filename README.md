# Как запустить / проверить (Godot 4.3, Android / Poco F4)

## 1. Скачай Godot 4.3 Stable

Официальная страница релиза (открывай в браузере телефона или ПК):
https://github.com/godotengine/godot/releases/tag/4.3-stable

- **Для ПК (Windows / Linux / macOS):** скачай `Godot_v4.3-stable_win64.exe` или `.zip` (Linux). Распакуй, запусти.
- **Для Android (если хочешь редактировать на телефоне):** в roj be на Google Play / GitHub есть `Godot Editor` APK, но для сборки .apk лучше использовать ПК.

> Если ссылка не открывается — используй `https://godotengine.org/download/windows/` или `https://godotengine.org/download/linux/`

## 2. Открой проект

Копируй папку `/home/user/Game` (или всё содержимое: `docs/`, `scenes/`, `scripts/`, `assets/`, `project.godot`) на свой ПК.

Запуск:
```bash
# Linux / Mac
./Godot_v4.3-stable_linux.x86_64 /путь/к/Game/project.godot
# Или просто открой editor и выбери папку Game
```

В редакторе нажми **F5** (или Ctrl+F5 для запуска без отладки).

## 3. Что тестировать в срезе (вертикальный срез)

Запусти сцену `scenes/main.tscn` или `scenes/player.tscn`.

Проверь:
- [ ] Игрок движется (WASD / тач-драг) и прыгает.
- [ ] Камера следует, не ломается.
- [ ] Вход в Глейд (`glade.tscn`) работает.
- [ ] `intro_cutscene.tscn` запускается, пропускается (Space / Esc).
- [ ] В `maze_zone_01.tscn` — блоки на месте, Griever патрулирует.
- [ ] Головоломка (`scenes/puzzle_3blocks.tscn`) — блоки можно толкать.
- [ ] Возврат (`triggers/return_to_glade.tscn`) срабатывает.

## 4. Сборка APK для Poco F4

В редакторе (когда проект открыт):
```
Project → Export → Android
(проект уже настроен: package/name = com.mazerunner.fan)
```
Нажми **Export Project** → сохрани `maze_fan.apk`.

На Poco F4:
- Передай APK (USB / Telegram / облако)
- Установи (разреши «Неизвестные источники» в настройках Android)
- Запусти — тестируй управление, патруль Гривера, катсцену.

## 5. Если что-то сломалось в сцене

Не переписывай всё. В редакторе:
- Открой `.tscn` → исправь позицию узла, текстуру или скрипт.
- Если ресурс не найден — Godot предложит пересоздать или указать путь.
- `GrieverAI.gd` требует `NavigationAgent3D` + `NavigationRegion3D` в лабиринте — уже добавлено в `maze_zone_01.tscn`.

## 6. Быстрые команды для разработки (если настроишь Godot на ПК)

```bash
# Проверка синтаксиса скрипта без визуала (если нужно)
godot --headless --script scripts/PlayerController.gd 2>&1 | head -20
# Но лучше просто открыть в редакторе.
```

---
**Важно:** проект использует `project.godot` с `config_version=5`. Не открывай в Godot 3.x — будет ошибка.
