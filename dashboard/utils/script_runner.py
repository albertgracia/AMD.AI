import subprocess
import os
import json
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ROCM_SDK_PATH = r'C:\Users\leobc\AppData\Local\Programs\Python\Python313\Lib\site-packages\_rocm_sdk_devel\bin'

def _to_cli_args(params: Dict[str, Any]) -> list:
    args: list = []
    mapping = {
        'model': '--model', 'backend': '--backend', 'profile': '--profile',
        'repetitions': '--repetitions', 'variable': '--variable', 'values': '--values',
        'config': '--config', 'config_a': '--config-a', 'config_b': '--config-b',
        'output': '--output', 'json_output': '--json-output', 'output_csv': '--output', 'output_json': '--json-output',
        'progress_file': '--progress-file',
    }
    flags = {'quick', 'yes', 'trace_chrome', 'trace-chrome', 'prometheus', 'scaling_analysis', 'scaling-analysis', 'compare_configs', 'compare-configs', 'save_presets', 'save-presets'}
    flag_map = {'trace_chrome': '--trace-chrome', 'scaling_analysis': '--scaling-analysis', 'compare_configs': '--compare-configs', 'save_presets': '--save-presets'}
    for key, value in params.items():
        if value is None or value == '':
            continue
        if key in flags:
            if str(value).lower() in ('true', '1', 'yes', 'on'):
                args.append(flag_map.get(key, '--' + key.replace('_', '-')))
            continue
        if key in mapping:
            args.extend([mapping[key], str(value)])
    if '--yes' not in args:
        args.append('--yes')
    return args


def build_command(script_path: str, params: Dict[str, Any]):
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    if ROCM_SDK_PATH not in env.get('PATH', ''):
        env['PATH'] = f'{ROCM_SDK_PATH};' + env.get('PATH', '')
    return ['python', script_path] + _to_cli_args(params), env


def run_skill_script(script_path: str, params: Dict[str, Any], timeout: int = 300) -> Optional[Dict[str, Any]]:
    cmd, env = build_command(script_path, params)
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout, check=True)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {'stdout': result.stdout}
    except Exception as e:
        logger.error(f'Error: {e}')
        return None
