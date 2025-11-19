# ВИЗУАЛЬНЫЙ АНАЛИЗ И РЕКОМЕНДОВАННЫЕ ФИКСЫ

## ЧАСТЬ 1: ДИАГРАММА ПРОБЛЕМЫ

### Текущая (НЕПРАВИЛЬНАЯ) архитектура:
```
CS2 netcon
    │
    ├─ "demo_pause" → "paused" (просто уведомление о паузе)
    │                   ❌ НЕ содержит информацию о тике
    │
    └─ telnet_client.py::force_sync_tick()
        │
        ├─ regex = r"(?:paused|unpaused) on tick (\d+)"
        │           ❌ Этот паттерн НЕ БУДЕТ найден
        │
        ├─ regex = r"tick\s+(\d+)"
        │           ❌ Слишком общий, может найти мусор
        │
        ├─ regex = r"Demo tick:\s*(\d+)"
        │           ❌ Этот паттерн НЕ БУДЕТ найден
        │
        └─ Если ничего не найдено → return self._current_tick
            │
            └─ ❌ self._current_tick = 0 (по умолчанию)
                │
                └─ SyncEngine.get_last_tick() = 0
                    │
                    └─ PredictionEngine.get_current_tick()
                        │
                        ├─ if server_tick == 0:
                        │      return 0
                        │
                        └─ _tick_history = [0, 0, 0, ...]
                            │
                            └─ _is_paused() = True
                                │
                                └─ "[Prediction] Pause detected"
                                    │
                                    └─ Overlay не обновляется
```

### Правильная архитектура (предложенная):
```
CS2 netcon
    │
    ├─ "demo_info" → "Currently playing 12500 of 160000 ticks"
    │                ✓ СОДЕРЖИТ информацию о тике
    │
    └─ telnet_client.py::force_sync_tick()
        │
        └─ get_demo_info() (используем существующий рабочий метод)
            │
            ├─ regex = r"Currently playing (\d+) of \d+ ticks"
            │           ✓ ЭТОТ ПАТТЕРН РАБОТАЕТ (используется в get_demo_info)
            │
            ├─ tick = 12500 ✓
            │
            └─ self._current_tick = 12500
                │
                └─ SyncEngine.get_last_tick() = 12500
                    │
                    └─ PredictionEngine.get_current_tick()
                        │
                        ├─ if server_tick == 0:
                        │      ... (не срабатывает)
                        │
                        ├─ predicted = 12500 + elapsed_ticks
                        │
                        └─ _tick_history = [12500, 12501, 12502, ...]
                            │
                            ├─ _is_paused() = False ✓
                            │
                            └─ Overlay обновляется нормально ✓
```

## ЧАСТЬ 2: ТАБЛИЦА СРАВНЕНИЯ МЕТОДОВ

| Аспект | demo_pause/resume | demo_info |
|--------|-------------------|-----------|
| **Команда** | `demo_pause` + `demo_resume` | `demo_info` |
| **Ответ содержит тик** | ❌ Нет | ✓ Да |
| **Regex patterns** | Неизвестные | r"Currently playing (\d+) of" |
| **Работает в коде** | ❌ Нет | ✓ Да (уже 90+ строк) |
| **Побочные эффекты** | Паузирует playback | Нет |
| **Влияние на sync событий** | ❌ Может сбить | ✓ Безопасно |
| **Надежность** | ❌ Ненадежно | ✓ Надежно |
| **Простота реализации** | ❌ Сложная | ✓ Простая |

## ЧАСТЬ 3: ЦЕПЬ ОШИБОК

```
┌─────────────────────────────────────────────────────────────────┐
│ ОШИБКА 1: Неправильный regex в force_sync_tick()               │
├─────────────────────────────────────────────────────────────────┤
│ ❌ Ищем: r"(?:paused|unpaused) on tick (\d+)"                  │
│ ✓ Должны: r"Currently playing (\d+) of \d+ ticks"             │
│                                                                  │
│ Последствие: current_tick = None                                │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ ОШИБКА 2: Fallback на нулевой тик                              │
├─────────────────────────────────────────────────────────────────┤
│ ❌ if current_tick:                                             │
│        return current_tick                                       │
│    else:                                                         │
│        return self._current_tick  # = 0                         │
│                                                                  │
│ ✓ Должны: Использовать get_demo_info()                        │
│                                                                  │
│ Последствие: force_sync_tick() = 0                              │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ ОШИБКА 3: SyncEngine не валидирует результат                   │
├─────────────────────────────────────────────────────────────────┤
│ ❌ self._last_tick = 0  (без проверки)                         │
│                                                                  │
│ ✓ Должны: Проверить if tick > 0 перед сохранением             │
│                                                                  │
│ Последствие: SyncEngine.get_last_tick() = 0                     │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ ОШИБКА 4: PredictionEngine не различает "не синхронизировано"  │
├─────────────────────────────────────────────────────────────────┤
│ ❌ if server_tick == 0:                                         │
│        return 0  (без разницы - нет синхи или действительно 0) │
│                                                                  │
│ ✓ Должны: Использовать флаг "is_synced"                        │
│                                                                  │
│ Последствие: predicted_tick = 0                                 │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ ОШИБКА 5: Ложное обнаружение паузы                             │
├─────────────────────────────────────────────────────────────────┤
│ ❌ _tick_history = [0, 0, 0, ...]                              │
│    _is_paused() = True  (потому что все одинаковые!)           │
│                                                                  │
│ ✓ Должны: Проверить if server_tick > 0 перед добавлением      │
│                                                                  │
│ Последствие: "Pause detected" каждый кадр!                     │
└─────────────────────────────────────────────────────────────────┘
```

## ЧАСТЬ 4: РЕКОМЕНДУЕМАЯ РЕАЛИЗАЦИЯ ФИКСА

### Шаг 1: Исправить telnet_client.py::force_sync_tick()

**Текущий код (НЕПРАВИЛЬНЫЙ)**:
```python
async def force_sync_tick(self) -> int:
    """Force synchronization by actively pausing/resuming demo."""
    if not self._connected:
        print("[Telnet] Not connected, cannot force sync")
        return self._current_tick

    try:
        print("[Telnet] Force syncing tick...")
        
        # Send demo_pause to trigger tick output
        self.writer.write(b"demo_pause\n")  # ❌ Неправильная команда
        await self.writer.drain()

        # Read response
        response = await asyncio.wait_for(
            self._read_with_buffer(4096),
            timeout=1.0
        )
        response_text = response.decode('utf-8', errors='ignore')

        # Send demo_resume immediately to continue playback
        self.writer.write(b"demo_resume\n")
        await self.writer.drain()
        
        # Try multiple patterns as CS2 format might vary
        patterns = [
            re.compile(r"(?:paused|unpaused) on tick (\d+)"),  # ❌ Не найдется
            re.compile(r"tick\s+(\d+)"),                        # ❌ Общий
            re.compile(r"Demo tick:\s*(\d+)"),                  # ❌ Не найдется
        ]
        
        print(f"[Telnet] Response text: {repr(response_text[:200])}")
        
        current_tick = None
        for pattern in patterns:
            match = pattern.search(response_text)
            if match:
                current_tick = int(match.group(1))
                break

        if current_tick:
            self._current_tick = current_tick
            print(f"[Telnet] Force sync successful: tick {current_tick}")
            return current_tick
        else:
            print(f"[Telnet] Force sync failed to parse tick from response")
            print(f"[Telnet] Full response: {repr(response_text)}")
            return self._current_tick  # ❌ ВОЗВРАЩАЕТ 0!

    except Exception as e:
        print(f"[Telnet] Force sync error: {e}")
        import traceback
        traceback.print_exc()
        return self._current_tick
```

**Новый код (ПРАВИЛЬНЫЙ)**:
```python
async def force_sync_tick(self) -> int:
    """Force synchronization using demo_info command.
    
    Uses demo_info instead of demo_pause/resume to get the current tick
    without interrupting playback. The demo_pause/resume approach doesn't
    work reliably because the response doesn't contain tick information.
    
    Returns:
        int: Current tick number (validated > 0), or last known tick if error
    """
    if not self._connected:
        print("[Telnet] Not connected, cannot force sync")
        return self._current_tick

    try:
        print("[Telnet] Force syncing tick via demo_info...")
        
        # Use the existing, proven get_demo_info() method
        info = await self.get_demo_info()
        tick = info.get("current_tick", 0)
        
        # ✓ Validate tick (must be > 0)
        if tick > 0:
            # ✓ Update internal state
            self._current_tick = tick
            print(f"[Telnet] Force sync successful: tick {tick}")
            return tick
        else:
            # Demo not loaded or error occurred
            print(f"[Telnet] Force sync: got invalid tick {tick} (demo not loaded?)")
            return self._current_tick
            
    except Exception as e:
        print(f"[Telnet] Force sync error: {e}")
        import traceback
        traceback.print_exc()
        return self._current_tick
```

### Шаг 2: Улучшить orchestrator.py::SyncEngine

**Добавить в SyncEngine.update()**:
```python
async def update(self, force: bool = False):
    """Update tick from source.

    Args:
        force: If True, forces a sync via force_sync_tick
        
    Raises:
        Exception: If tick source update fails
    """
    try:
        current_time = time.time()
        
        # Check if we need to force sync
        should_sync = force or (current_time - self._last_sync_time >= self.sync_interval)
        
        if should_sync and hasattr(self.tick_source, 'force_sync_tick'):
            # Do force sync
            tick = await self.tick_source.force_sync_tick()
            self._last_sync_time = current_time
            
            # ✓ Validate tick (warn if invalid)
            if tick == 0:
                print(f"[SyncEngine] ⚠️  WARNING: force_sync returned tick=0")
                print(f"[SyncEngine]    This might indicate a parse error or demo not loaded")
            
            print(f"[SyncEngine] Synced to tick {tick}")
        else:
            # Just get passive tick (no polling)
            tick = await self.tick_source.get_current_tick()
        
        self._last_tick = tick
        self._last_update_time = current_time

    except Exception as e:
        print(f"[SyncEngine] Update error: {e}")
        raise
```

### Шаг 3: Улучшить prediction_engine.py

**Добавить состояние в SmoothPredictionEngine**:
```python
class SmoothPredictionEngine(PredictionEngine):
    def __init__(self, sync_engine: 'SyncEngine', tick_rate: int = 64, smoothing_window: int = 5):
        super().__init__(sync_engine, tick_rate)
        self.smoothing_window = smoothing_window
        self._tick_history: list[int] = []
        self._is_synced = False  # ✓ Добавить флаг синхронизации
```

**Улучшить get_current_tick()**:
```python
def get_current_tick(self) -> int:
    """Get smoothed predicted tick.

    Applies smoothing and detects anomalies like jumps and pauses.

    Returns:
        int: Smoothed predicted tick
    """
    # Get base prediction
    predicted = super().get_current_tick()
    
    # ✓ Track synchronization state
    if predicted > 0 and not self._is_synced:
        self._is_synced = True
        print(f"[Prediction] ✓ Initial sync complete at tick {predicted}")

    # Add to history only if synced
    if self._is_synced:
        self._tick_history.append(predicted)

        # Keep only recent history
        if len(self._tick_history) > self.smoothing_window:
            self._tick_history.pop(0)

        # Detect jump (user pressed Shift+F2 to jump to tick)
        if len(self._tick_history) >= 2:
            jump_size = abs(self._tick_history[-1] - self._tick_history[-2])

            if jump_size > 100:  # Large jump detected (>100 ticks = ~1.5 seconds)
                print(f"[Prediction] Jump detected ({jump_size} ticks)")
                # Clear history and accept new tick
                self._tick_history = [predicted]
                return predicted

        # Detect pause
        if self._is_paused():
            print("[Prediction] Pause detected")
            return self._tick_history[-1] if self._tick_history else 0

    return predicted
```

## ЧАСТЬ 5: ОПТИМАЛЬНЫЕ ПАРАМЕТРЫ

### В src/core/config.py - добавить:
```python
@dataclass
class AppConfig:
    # ... existing fields ...
    
    # NEW: Sync interval for force_sync_tick
    sync_interval: float = 0.0  # 0 = disabled (recommended)
```

### В src/core/factory.py - использовать:
```python
# Во время создания Orchestrator:
orchestrator = Orchestrator(
    tick_source=tick_source,
    demo_repository=demo_repo,
    player_tracker=player_tracker,
    visualizer=visualizer,
    polling_interval=config.polling_interval,      # 0.25 sec = 4 Hz
    render_fps=config.render_fps,                 # 60 FPS
    tick_rate=config.tick_rate,                   # 64 Hz
    use_smooth_prediction=config.use_smooth_prediction,
    sync_interval=config.sync_interval,           # ✓ NEW
)
```

## ЧАСТЬ 6: ОПТИМАЛЬНЫЕ ЗНАЧЕНИЯ ПАРАМЕТРОВ

| Параметр | Текущее | Рекомендуемое | Причина |
|----------|---------|---------------|---------|
| **polling_interval** | 0.25 | 0.25 | ✓ Хорошо (4 Hz) |
| **sync_interval** | 5.0 | **0.0** | Отключить, не нужен |
| **render_fps** | 60 | 60 | ✓ Хорошо |
| **tick_rate** | 64 | 64 | ✓ Правильно для CS2 |
| **smoothing_window** | 5 | 5 | ✓ Хорошо |
| **max_drift** | 10 | 10 | ✓ Хорошо |

**Почему sync_interval=0?**
- polling_interval=0.25 (4 Hz) уже достаточно для синхронизации
- demo_pause/resume ненадежны и прерывают playback
- get_demo_info() безопасна и регулярно вызывается
- Дополнительная force_sync каждые 5 сек не нужна

## ЧАСТЬ 7: МЕСТО ЛОГИРОВАНИЯ ДЛЯ ОТЛАДКИ

**Если тик все еще остается 0 после фиксов**:

1. Добавить в telnet_client.py::get_demo_info():
```python
print(f"[Telnet] demo_info response:\n{response_text}")
```

2. Добавить в orchestrator.py::_sync_loop():
```python
print(f"[Orchestrator] Sync tick: {self.sync_engine.get_last_tick()}")
```

3. Добавить в prediction_engine.py::get_current_tick():
```python
print(f"[Prediction] server_tick={predicted}, history={self._tick_history}")
```

4. Запустить с логированием:
```bash
python src/main.py --mode prod --demo demo.dem --debug
```
