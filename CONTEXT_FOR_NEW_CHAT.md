# Контекст проекта для нового чата

## Что уже сделано

### ✅ Создана полная документация проекта (12 файлов)

**Структура:**
```
cs2-demo-input-viewer/
├── docs/
│   ├── 00_PROJECT_OVERVIEW.md      - Обзор проекта, цели, архитектура
│   ├── 01_ARCHITECTURE.md          - SOLID принципы, интерфейсы, DI
│   ├── 02_DATA_LAYER.md            - ETL pipeline, demoparser2, кэш
│   ├── 03_NETWORK_LAYER.md         - Asyncio telnet, sync, prediction
│   ├── 04_UI_LAYER.md              - PyQt6 overlay, детальные layouts
│   ├── 05_CORE_LOGIC.md            - Orchestrator, интеграция
│   ├── DEVELOPMENT_PLAN.md         - Пошаговый план разработки
│   ├── USER_GUIDE.md               - Инструкция для пользователей
│   └── README.md                   - Индекс документации
├── src/                            - Директории созданы (пустые)
│   ├── domain/
│   ├── interfaces/
│   ├── mocks/
│   ├── parsers/
│   ├── network/
│   ├── ui/
│   └── core/
├── tests/                          - Создана
├── cache/                          - Создана
├── demos/                          - Создана
├── requirements.txt                - Python зависимости
├── .gitignore                      - Git ignore файл
├── config.example.json             - Пример конфигурации
└── README.md                       - Оригинальный README с ТЗ
```

**Git статус:**
- Commit: `67afa66` - "Add complete project documentation and structure"
- Branch: `claude/review-readme-plan-012gXGeEVQE8xdfdWJrRwEug`
- Статус: Закоммичено локально, но НЕ запушено (проблемы с git сервером 504/503)

---

## Исходное ТЗ (из README.md)

### Основные требования:

**Цель:** Визуализация инпутов игрока при просмотре CS2 демок

**Архитектура:** Hybrid (ETL + Real-time Runtime)
- **Phase A (Offline):** .dem file → demoparser2 → Transform → cache.json
- **Phase B (Runtime):** CS2 Telnet ← Sync Engine ← Prediction → PyQt6 Overlay

**Технологии:**
- Python 3.10-3.12 (НЕ 3.13, т.к. telnetlib удален)
- PyQt6 для UI
- demoparser2 для парсинга
- asyncio для telnet (НЕ telnetlib!)
- Subtick precision обязательна

**CS2 параметры запуска:**
```bash
-netconport 2121 -insecure
```

**Извлекаемые поля:**
```python
fields = [
    "m_nButtonDownMaskPrev",  # Битовая маска кнопок
    "subtick_moves",          # Subtick timing (0.0-1.0)
    "m_steamID"               # Идентификация игрока
]
```

**Button Masks (Source 2):**
```python
IN_ATTACK = 1      # Mouse1
IN_JUMP = 2        # Space
IN_DUCK = 4        # Ctrl
IN_FORWARD = 8     # W
IN_BACK = 16       # S
IN_MOVELEFT = 512  # A
IN_MOVERIGHT = 1024 # D
IN_ATTACK2 = 2048  # Mouse2
IN_SPEED = 131072  # Shift
```

**Sync Strategy:**
- Polling: 2-4 Hz (250-500ms)
- Telnet команда: `demo_info`
- Regex: `r"Currently playing (\d+) of \d+ ticks"`
- Prediction: 64 Hz (CS2 tickrate)

---

## UI Спецификация (детальная)

### Визуальный стиль:
- **Прозрачный фон** (WA_TranslucentBackground)
- **Черные контуры** (wireframe, только обводка)
- **Подсветка при нажатии** (красный полупрозрачный)
- **Click-through** (WA_TransparentForMouseEvents)
- **Поверх всех окон** (WindowStaysOnTopHint)

### Клавиатура (5 рядов):

**Параметры:**
- W = 40px (ширина клавиши)
- H = 40px (высота клавиши)
- Gx = 4px (горизонтальный зазор)
- Gy = 4px (вертикальный зазор)
- KX0, KY0 = 20, 20 (origin точка)

**Ряды:**
1. **Ряд 0** (y=KY0): ~, 1, 2, 3, 4, 5
2. **Ряд 1** (сдвиг S≈0.4W влево): TAB, Q, W, E, R, T
3. **Ряд 2** (сдвиг S2≈S+0.3W влево): A, S, D, F, G
4. **Ряд 3** (сдвиг S3≈S2+0.2W влево): **SHIFT** (вертикальный, 90°), Z, X, C, V, B
5. **Ряд 4**: CTRL, ALT, **SPACE** (ширина ≈3W)

### Мышь (справа от клавиатуры, отступ DM):

**Компоненты:**
- **Верхний блок:** LMB | MWHEEL | RMB
- **Нижний блок:** Корпус мыши
- **Боковые кнопки:** 2 кнопки слева (M4, M5)

---

## Обсуждение с пользователем

### Вопрос 1: Python версия?
**Ответ:** "как будет лучше?" → **Решение: 3.10-3.12** (избегаем 3.13)

### Вопрос 2: Демо-файлы?
**Ответ:** Брать из интернета, ~400MB

### Вопрос 3: Button masks для Source 2?
**Ответ:** Надо проверить экспериментально (могут отличаться от Source 1)

### Вопрос 4: Subtick precision?
**Ответ:** "давай сразу нормально сделаем" → **Обязательна с первой версии**

### Вопрос 5: UI layout?
**Ответ:** "знаешь как дефолтно html layout в obs" → Но потом дал детальную спецификацию (см. выше)

### Вопрос 6: Определение игрока?
**Ответ:** "смотря за каким игроком мы смотрим в самой КС" → **Динамически из CS2**, не хардкод

### Ключевое требование:
> "мы как бы пишем абстракцию. то есть сначала пишем продукт, потом только будет тест. надо с учетом этого."

> "я бы хотел в будущем расширить функционал. может добавить просмотр гранат, еще чего то. это я к тому что бы писать надо реально с абстракцией и солид принципами."

---

## Архитектурные решения

### SOLID принципы:
- **Single Responsibility:** Каждый модуль делает одно
- **Open/Closed:** Расширяем через интерфейсы
- **Liskov Substitution:** Mock ↔ Real без изменений
- **Interface Segregation:** Узкие интерфейсы
- **Dependency Inversion:** Зависим от абстракций

### Ключевые интерфейсы:

```python
# 1. ITickSource - источник текущего тика
class ITickSource(ABC):
    async def connect() -> bool
    async def disconnect() -> None
    def is_connected() -> bool
    async def get_current_tick() -> int

# 2. IDemoRepository - доступ к кэшу инпутов
class IDemoRepository(ABC):
    def load_demo(demo_path: str) -> bool
    def get_inputs(tick: int, player_id: str) -> Optional[InputData]
    def get_tick_range() -> tuple[int, int]

# 3. IPlayerTracker - отслеживание текущего игрока
class IPlayerTracker(ABC):
    async def get_current_player() -> Optional[str]
    async def update() -> None

# 4. IInputVisualizer - отрисовка оверлея
class IInputVisualizer(ABC):
    def render(data: InputData) -> None
    def show() -> None
    def hide() -> None
    def set_position(x: int, y: int) -> None
```

### Mock-First Development:

**Workflow:**
1. Создаем интерфейс
2. Создаем Mock реализацию
3. Разрабатываем UI/логику на моках
4. Заменяем на реальную реализацию

**Пример:**
```python
# Dev mode
orchestrator = Orchestrator(
    tick_source=MockTickSource(),
    demo_repo=MockDemoRepository(),
    player_tracker=MockPlayerTracker()
)

# Prod mode
orchestrator = Orchestrator(
    tick_source=CS2TelnetClient(),
    demo_repo=RealDemoParser(),
    player_tracker=CS2PlayerTracker()
)
```

---

## План разработки (6 фаз)

### Phase 1: Foundation (2-3 дня)
- [ ] Создать domain models (InputData, PlayerInfo, DemoMetadata)
- [ ] Создать все интерфейсы (4 файла)
- [ ] Реализовать все моки (3 класса)
- [ ] Написать unit tests

### Phase 2: Data Layer (3-4 дня)
- [ ] Button decoder (decode_buttons)
- [ ] Mock data generator
- [ ] MockDemoRepository
- [ ] Real ETL pipeline с demoparser2

### Phase 3: UI Layer (3-4 дня)
- [ ] Layouts (KeyboardLayout, MouseLayout)
- [ ] Renderers (KeyboardRenderer, MouseRenderer)
- [ ] Main overlay (CS2InputOverlay)
- [ ] Тестирование с моками

### Phase 4: Network Layer (2-3 дня)
- [ ] Asyncio Telnet client
- [ ] Sync engine
- [ ] Prediction engine
- [ ] Player tracker

### Phase 5: Integration (2-3 дня)
- [ ] Main orchestrator
- [ ] Config system
- [ ] Entry point (main.py)
- [ ] CLI аргументы

### Phase 6: Polish (3-5 дней)
- [ ] Integration tests
- [ ] Performance optimization (<2% CPU)
- [ ] User documentation
- [ ] Packaging

**Общий срок:** 3-4 недели

---

## Что делать дальше

### Следующий шаг: Phase 1, Task 1.1

**Создать файл:** `src/domain/models.py`

**Код:**
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class InputData:
    """Player input state for a single tick."""
    tick: int
    keys: List[str]           # ["W", "A", "SPACE"]
    mouse: List[str]          # ["MOUSE1"]
    subtick: dict            # {"W": 0.0, "MOUSE1": 0.5}
    timestamp: Optional[float] = None

@dataclass
class PlayerInfo:
    """Player identification."""
    steam_id: str
    name: str
    entity_id: Optional[int] = None

@dataclass
class DemoMetadata:
    """Demo file metadata."""
    file_path: str
    player_id: str
    player_name: str
    tick_range: tuple[int, int]
    tick_rate: int
    duration_seconds: float
```

**Критерии завершения:**
- [ ] Все dataclasses определены
- [ ] Type hints полные
- [ ] Docstrings добавлены
- [ ] Импорты работают

### После Task 1.1:

**Task 1.2:** Создать интерфейсы (4 файла в `src/interfaces/`)
**Task 1.3:** Создать моки (3 файла в `src/mocks/`)
**Task 1.4:** Написать unit tests

Подробный план каждой задачи есть в `docs/DEVELOPMENT_PLAN.md`

---

## Текущие проблемы

### ❌ Git Push не работает
- Ошибки: 503, 504 (Gateway Timeout)
- Попытки: 4+ с exponential backoff
- Статус: Все закоммичено локально (commit 67afa66)
- Решение: Нужно запушить вручную или подождать восстановления сервера

**Команда для ручного push:**
```bash
git push -u origin claude/review-readme-plan-012gXGeEVQE8xdfdWJrRwEug
```

---

## Важные детали для нового чата

### 1. Технологический стек:
- Python 3.10-3.12 (обязательно!)
- PyQt6 (не Tkinter/Pygame)
- demoparser2 (единственная библиотека с subtick)
- asyncio (не telnetlib!)

### 2. Архитектура:
- Hybrid ETL + Runtime
- SOLID + DI
- Mock-first development

### 3. UI:
- Wireframe style (черные контуры)
- Детальная спецификация layouts в docs/04_UI_LAYER.md
- Вертикальный SHIFT (90°)
- SPACE ширина = 3W

### 4. Extensibility:
- Планируется добавить: гранаты, траектории, аналитику
- Архитектура позволяет легко расширять

### 5. Пользовательские требования:
- Демки ~400MB из интернета
- Subtick обязателен
- Динамическое определение игрока
- Абстракция и тестируемость критичны

---

## Вопросы для нового чата

1. **С чего начать?** → Phase 1, Task 1.1 (domain models)
2. **Где документация?** → `docs/` папка, начни с `docs/README.md`
3. **Какой план?** → `docs/DEVELOPMENT_PLAN.md`
4. **Что с git?** → Закоммичено, но не запушено. Пользователь может запушить вручную

---

## Команды для старта

```bash
# 1. Проверить что все на месте
ls -la docs/
ls -la src/

# 2. Создать виртуальное окружение
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Начать Phase 1
# Создать src/domain/models.py (см. код выше)
```

---

## Файлы для чтения

**Обязательные:**
1. `docs/00_PROJECT_OVERVIEW.md` - обзор
2. `docs/01_ARCHITECTURE.md` - архитектура
3. `docs/DEVELOPMENT_PLAN.md` - пошаговый план

**По необходимости:**
4. `docs/02_DATA_LAYER.md` - ETL
5. `docs/03_NETWORK_LAYER.md` - Network
6. `docs/04_UI_LAYER.md` - UI
7. `docs/05_CORE_LOGIC.md` - Core

---

## Саммари для нового ИИ

**Задача:** Разработать CS2 Input Visualizer - overlay для визуализации инпутов игрока при просмотре демок.

**Текущий статус:** Фаза документирования завершена (12 файлов создано). Готовы к началу Phase 1: Foundation.

**Архитектура:** Hybrid (ETL offline + Runtime real-time), SOLID принципы, Mock-first development.

**Технологии:** Python 3.10-3.12, PyQt6, demoparser2, asyncio.

**Проблема:** Git push не работает (504 ошибки), но все закоммичено локально.

**Следующий шаг:** Начать Phase 1 - создать domain models в `src/domain/models.py`.

**Документация:** Полная, в папке `docs/`. Начни с `docs/README.md` для навигации.

---

Конец контекста. Удачи новому ИИ! 🚀
