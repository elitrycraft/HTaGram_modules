from telethon import events
import subprocess
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dep = []  # нет зависимостей

# Ограничения
MAX_OUTPUT_LENGTH = 4000  # Telegram лимит
TIMEOUT = 60  # таймаут в секундах

async def run(client, restart_userbot):
    logger.info("Bash module started")
    
    @client.on(events.NewMessage(outgoing=True))
    async def bash_handler(event):
        if event.message.text.startswith('-bash '):
            command = event.message.text[6:].strip()
            
            if not command:
                await event.edit("**❌ Usage:** `-bash <command>`")
                return
            
            # Отправляем статус
            loading_msg = await event.edit(f"**🔄 Executing:** `{command}`...")
            
            try:
                # Выполняем команду
                result = await run_bash_command(command)
                
                # Форматируем вывод в markdown
                output = format_markdown_output(command, result)
                
                # Обрезаем если слишком длинный
                if len(output) > MAX_OUTPUT_LENGTH:
                    output = output[:MAX_OUTPUT_LENGTH - 100] + "\n\n**... (output truncated)**"
                
                await loading_msg.edit(output, parse_mode='markdown')
                
            except subprocess.TimeoutExpired:
                await loading_msg.edit(f"**⏰ Timeout:** Command `{command}` took more than {TIMEOUT} seconds")
            except Exception as e:
                await loading_msg.edit(f"**❌ Error:**\n```\n{str(e)}\n```", parse_mode='markdown')
                logger.error(f"Error in bash: {e}")

async def run_bash_command(command, timeout=TIMEOUT):
    """Выполнение bash команды с таймаутом"""
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True,
        executable='/bin/bash'
    )
    
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=timeout
        )
        
        return {
            'stdout': stdout.decode('utf-8', errors='ignore').strip(),
            'stderr': stderr.decode('utf-8', errors='ignore').strip(),
            'returncode': process.returncode
        }
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise subprocess.TimeoutExpired(command, timeout)

def format_markdown_output(command, result):
    """Форматирование вывода в markdown"""
    output_lines = []
    
    # Заголовок
    output_lines.append(f"**📟 Command:** `{command}`")
    output_lines.append(f"**🔚 Exit code:** `{result['returncode']}`")
    output_lines.append("")
    
    # Input блок
    output_lines.append("Input```" + command + "```")
    output_lines.append("")
    
    # Output блок (если есть stdout)
    if result['stdout']:
        output_lines.append("Output```" + result['stdout'][:3500] + "```")
    
    # STDERR блок (если есть ошибки)
    if result['stderr']:
        output_lines.append("Error```" + result['stderr'][:500] + "```")
    
    # Если нет вывода
    if not result['stdout'] and not result['stderr']:
        output_lines.append("Output```" + "✅ Command executed successfully (no output)" + "```")
    
    return "\n".join(output_lines)
