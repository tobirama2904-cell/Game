# ЭТАП 0 — ТЕХНИЧЕСКИЙ ДИЗАЙН (Technical Design)

**Автор:** техлид (Godot 4)  
**Дата:** 2026-11-02  
**Статус:** черновик  
**Ограничение:** без выдуманных API, с проверкой документации Godot 4.2/4.3.

---

## 1. Архитектура проекта (папки)

```
/project.godot
/docs/
  research.md
  game-design.md
  narrative.md
  technical-design.md
  production-plan.md
/assets/
  textures/          # AI-сгенерированные или процедурные (PNG/WebP)
  models/            # .glb / .fbx (только наши или CC0)
  sounds/            # .ogg / .wav (свободные или синтез)
  fonts/             # свободные TTF
  scenes/            # .tscn
  scripts/           # .gd
  materials/         # .tres
/scenes/
  main.tscn          # менеджер игры, загружает другие
  glade.tscn         # безопасная зона
  maze_zone_01.tscn  # первая зона Лабиринта
  griever.tscn       # префаб врага
  player.tscn        # префаб игрока
  ui.tscn            # интерфейс (здоровье, выносливость, подсказки)
  cutscene_01.tscn   # катсцена вступление
  cutscene_02.tscn   # катсцена сдвиг
  cutscene_03.tscn   # катсцена финал
/scripts/
  PlayerController.gd
  GrieverAI.gd
  DialogueManager.gd
  GameState.gd
  CutsceneController.gd
  StaminaSystem.gd
  PuzzleBlock.gd
  LevelLoader.gd
```

---

## 2. Сцены и их структура (ключевые)

### 2.1. `player.tscn` — Префаб игрока

- **Корневой узел:** `CharacterBody3D` (или `RigidBody3D` + `CharacterBody3D` если Jolt). Для среза — `CharacterBody3D` с встроенной физикой Godot (достаточно для стабильности на относительно низкой скорости).  
- **Дочерние узлы:**  
  - `MeshInstance3D` — модель тела (можно использовать простой меш — цилиндр + сфера для головы, или сгенерировать текстуру).  
  - `CollisionShape3D` — капсула (радиус ~0.4 м, высота ~1.8 м) — стандарт для CharacterBody3D.  
  - `Camera3D` — камера от третьего лица. С `SpringArm3D` (если используется) — для сглаживания движения камеры.  
  - `AnimationPlayer` — анимации: idle, run, jump, roll, interact.  
  - `RayCast3D` — для проверки поверхности под ногами (чтобы не залипать в воздухе).  
  - `AudioStreamPlayer3D` — шаги, дыхание.

- **Скрипт:** `PlayerController.gd`.  
  - `func _physics_process(delta):` — обработка ввода, движение (`move_and_slide()`), проверка столкновений.  
  - `func _process(delta):` — выносливость (если спринт), состояние страха.  
  - `func _input(event):` — взаимодействие (`interact`), пауза (`pause`).

> **TODO:** точный метод `move_and_slide()` в Godot 4 — `move_and_slide()` возвращает `Vector3` (остаточная скорость). Проверить в документации: в 4.2/4.3 сигнатура не изменилась, но `velocity` теперь управляется напрямую.

### 2.2. `griever.tscn` — Префаб врага

- **Корневой узел:** `CharacterBody3D` (для патруля и преследования) или `RigidBody3D` (если нужна физика столкновений с игроком). Для AI — `CharacterBody3D` удобнее, так как `NavigationAgent3D` работает с `CharacterBody3D`.  
- **AI-скрипт:** `GrieverAI.gd`.  
  - Состояния: `PATROL`, `CHASE`, `ATTACK`.  
  - `NavigationAgent3D` — путь до цели.  
  - `RayCast3D` — зрение (дальность ~10 м, угол ~60°).  
  - `Area3D` — зона атаки (~2 м).  
  - `AnimationPlayer` — анимации: idle, walk, run, attack, death.

---

## 3. Физика (Physics)

- **Вариант A (быстро, без плагинов):** встроенный Godot Physics.  
  - `CharacterBody3D` для игрока и Гривера.  
  - `StaticBody3D` + `CollisionShape3D` (бокс или капсула) для стен и блоков.  
  - `RigidBody3D` для предметов, которые можно толкать (камни для головоломки).  
- **Вариант B (стабильность на скорости):** Jolt Physics (`godot-jolt`).  
  - Требует установки плагина (через Asset Library или GitHub).  
  - `JoltBody3D` вместо `RigidBody3D`.  
  - `JoltCharacterBody3D` вместо `CharacterBody3D`.  
  - **Блокер:** нужно проверить, что плагин совместим с версией Godot. Если нет — остаёмся на варианте A для среза.

> **Решение для среза:** использовать Вариант A (встроенная физика). Это позволяет запускать проект без дополнительных зависимостей. Если Jolt установлен — переключить в `project.godot` или через скрипты.

---

## 4. AI — архитектура Гривера

**Не LLM, не нейросеть.** Классическая state machine.

```gdscript
# GrieverAI.gd — упрощённая структура
class_name GrieverAI
extends CharacterBody3D

enum STATE { PATROL, CHASE, ATTACK }
var current_state: STATE = STATE.PATROL

@onready var nav_agent: NavigationAgent3D = $NavigationAgent3D
@onready var sight_ray: RayCast3D = $SightRayCast
@onready var attack_area: Area3D = $AttackArea

func _ready():
    nav_agent.target_location = get_random_patrol_point()

func _physics_process(delta):
    match current_state:
        STATE.PATROL:
            if nav_agent.is_target_reached():
                nav_agent.target_location = get_random_patrol_point()
            # Движение к цели
            move_toward_target(delta)
            if can_see_player():
                current_state = STATE.CHASE
        STATE.CHASE:
            nav_agent.target_location = player.global_position
            move_toward_target(delta)
            if distance_to_player() > 15.0:
                current_state = STATE.PATROL
            elif distance_to_player() < 2.0:
                current_state = STATE.ATTACK
        STATE.ATTACK:
            # Анимация атаки, урон игроку
            pass
```

- **NavigationAgent3D:** требует `NavigationMap` или `NavigationRegion3D` в сцене. Для среза — создать `NavigationRegion3D` с `NavigationMesh` (сгенерированным из геометрии стены или вручную через `NavigationMeshInstance`).  
- **Пати:** для среза — 3 точки патруля в зоне. Достаточно для демонстрации.

---

## 5. Рендер (Render) — Forward+, постобработка, свет

- **Рендерер:** `RenderingServer` → `Forward+` (по умолчанию в Godot 4 для 3D).  
- **SDFGI:** `WorldEnvironment` → `SDFGI` → `Enable = true`. Влияет на освещение в коридорах — важно для атмосферы. Может быть тяжело на слабых GPU — для среза оставляем включённым, но с низким разрешением (`SDFGIProbeCount` или `SDFGICascadeCount`).  
- **Volumetric Fog:** `WorldEnvironment` → `Volumetric Fog` → `Enable = true`. Добавляет глубину в тёмных коридорах.  
- **Post Process:** `WorldEnvironment` → `Glow`, `Tonemap`, `Auto Exposure`. Для среза — минимальная постобработка: лёгкий `Glow` (для светящихся глаз Гривера), `Tonemap` (ACES или Filmic для кинематографичности).  
- **LOD:** `MeshInstance3D` → `LOD` — для моделей с высокой детализацией (если будут). Для среза — повторяющиеся блоки не требуют LOD, так как это один меш, повторённый через `GridMap` или `MultiMeshInstance3D`.  
- **Occlusion Culling:** `Viewport` → `Occlusion Culling` → `Enable = true`. В лаборатории с узкими коридорами это критично — камера не видит то, что скрыто стенами.  
- **Material:** `StandardMaterial3D` — для каменных стен, `ShaderMaterial` — для светящихся элементов Гривера или аномалий.

---

## 6. Ассеты и их источники (правила IP)

| Тип ассета | Источник для среза | Формат | Примечание |
|---|---|---|---|
| **Текстуры стен / камня** | `generate_image` (стилизованный каменный блок, серо-коричневый) или процедурный `NoiseTexture` + `GradientTexture` | PNG / WebP (1024×1024 или 512×512) | Не копируем текстуры из фильма. |
| **Модель игрока** | Простой меш (капа + цилиндр + сфера) или `generate_image` → `ImageMagick` для текстуры | `.glb` или `.fbx` | Для среза — простая геометрия, без высокого полигона. |
| **Модель Гривера** | Сгенерированная или простая геометрия (сфера + шипы) с текстурой | `.glb` | Не копируем модель из фильма. |
| **Звуки (шаги, дыхание)** | Синтез или свободные библиотеки (`freemusicarchive.org`, `opengameart.org` — только если доступно в сети; иначе — собственный синтез через Godot) | `.ogg` | Без авторских звуков из фильма. |
| **Музыка (эмбиент)** | Сгенерированная или свободная | `.ogg` | Для среза — минимальная, только события. |
| **UI / Шрифты** | Свободные шрифты (Open Sans, Roboto) или сгенерированные текстуры для заголовков | `.ttf` | Можно использовать из `google/fonts` или стандартных системных. |

> **Важно:** `generate_image` — это AI-генерация. Результаты могут быть несовершенными. Для текстур стен — лучше использовать процедурный подход (`NoiseTexture` + `GradientTexture` в Godot). Для ключевых артов (текстура лица Чака или Гривера) — `generate_image` с конкретным промптом.

---

## 7. Сохранения (Save / Load) — для среза

- **Не полноценное сохранение в файл** — это не RPG с прогрессией. Для среза — только **чекпоинты** (спавн при смерти в тот же момент или в начало зоны).  
- **Для будущего расширения:** `FileAccess` + `JSON` или `ConfigFile` для сохранения прогресса (открытые зоны, найденные подсказки, состояние диалогов).  
- **Для среза:** нет необходимости в `save.gd` — достаточно `GameState.gd` с переменной `current_zone`.

---

## 8. Тесты (QA / Manual Checklist)

**Автоматизированные (если возможно через скрипт):**
- [ ] `PlayerController.gd` загружается без ошибок (`_ready()` не падает).  
- [ ] `Physics` не вызывает ошибку коллизий (`RigidBody3D` не проваливается в пол).  
- [ ] `NavigationAgent3D` не выдаёт ошибку `Target location not on navigation mesh`.  
- [ ] `CutsceneController.gd` запускает `AnimationPlayer` без падения.

**Ручные (для среза):**
- [ ] Открытие проекта в Godot 4 без ошибок (`.godot` корректен, `project.godot` не содержит неизвестных ключей).  
- [ ] Запуск из редактора (`F5`) — не падает через 10 минут.  
- [ ] Игрок может двигаться, прыгать, подкатиться, взаимодействовать.  
- [ ] Гривер патрулирует, видит игрока, преследует, атакует, умирает (если добавлена смерть).  
- [ ] Головоломка решается (3 блока в правильном порядке).  
- [ ] Сдвиг срабатывает, игрок может пройти или умереть.  
- [ ] Катсцены запускаются, пропускаются, не ломают камеру.  
- [ ] Нет «розовых» материалов (все текстуры загружены), нет красных ошибок в консоли (`Output` в Godot).  
- [ ] FPS не падает ниже 30 (в sandbox — проверяем отсутствием лагов в сцене с небольшим количеством объектов).

---

## 9. Риски и резервы (Risk Register)

| Риск | Вероятность | Воздействие | Митигатор |
|---|---|---|---|
| Jolt Plugin не совместим с версией Godot | Средняя | Высокое | Используем встроенную физику (Вариант A) для среза. |
| `generate_image` даёт плохой результат для моделей | Высокая | Среднее | Используем процедурные текстуры для стен; AI — только для ключевых артов. |
| AI Гривера застревает или ведёт себя хаотично | Средняя | Высокое | Простой state machine с ограниченным числом состояний; тестируем в isolated сцене. |
| Сдвиг секции ломает коллизии (игрок проваливается) | Средняя | Высокое | Используем `AnimationPlayer` только для перемещения `MeshInstance3D`, не для `StaticBody3D` (коллизии не двигаются вместе с мешем — нужно либо двигать всю сцену, либо использовать `GridMap` с анимацией блоков). |
| Сцена среза слишком большая (больше 15 мин) | Низкая | Среднее | Строго следуем сценарию среза; не добавляем дополнительные механики. |
| Нет Godot Editor в sandbox | Высокая | Среднее | Пишем `.gd` и `.tscn` в текстовом виде; проверяем синтаксис через `godot --script` или `godot --headless`; устанавливаем редактор как первый шаг. |

---

## 10. Следующие минимальные шаги (после согласования)

1. Установить Godot 4.2/4.3, создать `project.godot`, проверить запуск.  
2. Создать `player.tscn` и `PlayerController.gd` с базовым движением.  
3. Создать `glade.tscn` — визуально простую сцену с блоками.  
4. Создать `maze_zone_01.tscn` с повторяющимися блоками.  
5. Написать `GrieverAI.gd` с `NavigationAgent3D`.  
6. Протестировать в изоляции (без катсцен, без головоломки) — только движение и AI.  
7. Добавить катсцены и головоломку.  

> **Блокер для старта кода:** точная версия Godot (4.2 vs 4.3) и способ установки в этом окружении. **Также:** нужно ли в срезе включать `NavigationAgent3D` или использовать простой `look_at()` для Гривера? (Для демонстрации AI — лучше `NavigationAgent3D`, но если `NavigationMesh` сложно строить — можно временно использовать `look_at()` + `move_toward()` с ограничением по расстоянию.)
