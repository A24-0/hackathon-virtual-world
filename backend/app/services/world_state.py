"""
Глобальное состояние мира (скорость времени и т.д.)
"""
import asyncio

# Глобальная скорость времени (умножается на интервалы)
TIME_SPEED = 1.0

def get_time_speed() -> float:
    """Получить текущую скорость времени"""
    return TIME_SPEED

def set_time_speed(speed: float):
    """Установить скорость времени"""
    global TIME_SPEED
    TIME_SPEED = max(0.1, min(5.0, speed))  # Ограничиваем от 0.1 до 5.0

