from telethon import events
import platform
import os
import subprocess
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dep = ["psutil"]  # зависимость

async def run(client, restart_userbot):
    logger.info("Sysinfo module started")
    
    @client.on(events.NewMessage(outgoing=True))
    async def sysinfo_handler(event):
        if event.message.text == '-sysinfo':
            try:
                # Собираем информацию
                info = await get_system_info()
                
                # Форматируем вывод
                output = format_system_info(info)
                
                await event.edit(output)
                
            except Exception as e:
                await event.edit(f"Error getting system info: {e}")
                logger.error(f"Error in sysinfo: {e}")

async def get_system_info():
    """Сбор информации о системе"""
    try:
        import psutil
        psutil_available = True
    except ImportError:
        psutil_available = False
        logger.warning("psutil not installed, some info will be missing")
    
    info = {}
    
    # Базовая информация
    info['system'] = platform.system()
    info['release'] = platform.release()
    info['version'] = platform.version()
    info['machine'] = platform.machine()
    info['processor'] = platform.processor()
    info['hostname'] = platform.node()
    info['python_version'] = platform.python_version()
    
    # Информация от psutil (если доступна)
    if psutil_available:
        # CPU
        info['cpu_count'] = psutil.cpu_count()
        info['cpu_count_logical'] = psutil.cpu_count(logical=True)
        info['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else None
        info['cpu_usage'] = psutil.cpu_percent(interval=1)
        
        # RAM
        mem = psutil.virtual_memory()
        info['ram_total'] = mem.total
        info['ram_available'] = mem.available
        info['ram_used'] = mem.used
        info['ram_percent'] = mem.percent
        
        # Disk
        disk = psutil.disk_usage('/')
        info['disk_total'] = disk.total
        info['disk_used'] = disk.used
        info['disk_free'] = disk.free
        info['disk_percent'] = disk.percent
        
        # Network (bytes sent/received)
        net = psutil.net_io_counters()
        info['net_sent'] = net.bytes_sent
        info['net_recv'] = net.bytes_recv
        
        # Uptime
        info['uptime'] = psutil.boot_time()
        
        # Processes
        info['process_count'] = len(psutil.pids())
    
    return info

def format_system_info(info):
    """Форматирование информации в красивый вывод"""
    output = []
    output.append("SYSTEM INFORMATION")
    output.append("")
    
    # Система
    output.append("SYSTEM:")
    output.append(f"   OS: {info.get('system', 'N/A')} {info.get('release', 'N/A')}")
    output.append(f"   Kernel: {info.get('version', 'N/A')[:50]}")
    output.append(f"   Architecture: {info.get('machine', 'N/A')}")
    output.append(f"   Hostname: {info.get('hostname', 'N/A')}")
    output.append("")
    
    # CPU
    output.append("CPU:")
    output.append(f"   Model: {info.get('processor', 'Unknown')[:50]}")
    if 'cpu_count' in info:
        output.append(f"   Cores: {info['cpu_count']} physical, {info['cpu_count_logical']} logical")
    if 'cpu_freq' in info and info['cpu_freq']:
        output.append(f"   Frequency: {info['cpu_freq']:.0f} MHz")
    if 'cpu_usage' in info:
        output.append(f"   Usage: {info['cpu_usage']:.1f}%")
    output.append("")
    
    # RAM
    if 'ram_total' in info:
        output.append("RAM:")
        output.append(f"   Total: {info['ram_total'] / (1024**3):.2f} GB")
        output.append(f"   Used: {info['ram_used'] / (1024**3):.2f} GB ({info['ram_percent']:.1f}%)")
        output.append(f"   Available: {info['ram_available'] / (1024**3):.2f} GB")
        output.append("")
    
    # Disk
    if 'disk_total' in info:
        output.append("DISK:")
        output.append(f"   Total: {info['disk_total'] / (1024**3):.2f} GB")
        output.append(f"   Used: {info['disk_used'] / (1024**3):.2f} GB ({info['disk_percent']:.1f}%)")
        output.append(f"   Free: {info['disk_free'] / (1024**3):.2f} GB")
        output.append("")
    
    # Network
    if 'net_sent' in info:
        output.append("  NETWORK:")
        output.append(f"   Sent: {info['net_sent'] / (1024**3):.2f} GB")
        output.append(f"   Received: {info['net_recv'] / (1024**3):.2f} GB")
        output.append("")
    
    # Other
    output.append("  PYTHON:")
    output.append(f"   Version: {info.get('python_version', 'N/A')}")
    
    if 'uptime' in info:
        import time
        uptime_seconds = time.time() - info['uptime']
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        output.append(f"   Uptime: {days}d {hours}h {minutes}m")
    
    if 'process_count' in info:
        output.append(f"   Processes: {info['process_count']}")
    
    return "\n".join(output)
