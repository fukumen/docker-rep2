#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import argparse
import subprocess
import os
import sys

try:
    import argcomplete
except ImportError:
    argcomplete = None

DEFAULT_IMAGE_BASE = "ghcr.io/fukumen/rep2"
LOCAL_IMAGE_BASE = "rep2"

DEFAULT_P2_CONTEXT = "https://github.com/fukumen/p2-php.git#php8-merge-mbstring"
DEFAULT_PROXY_CONTEXT = "https://github.com/fukumen/2chproxy.pl.git#always-https-for-2ch-config"
LOCAL_P2_CONTEXT = "../p2-php"
LOCAL_PROXY_CONTEXT = "../2chproxy.pl"

SERVICE_NAME = "rep2php8"
REMOTE_HOST_NAME = "rep2"
REMOTE_PATH = "docker-rep2"

REMOTE_COMMAND = {
    "up": True,
    "build": False,
    "build-base": False,
    "down": True,
    "pull": True,
    "logs": True,
    "exec": True,
    "config": True,
    "update": True,
    "confdiff": True,
    "prune": True,
    "clean": False,
    "sync": False,
    "upload": False,
    "deploy": False,
}

def get_image_name(args):
    if args.local:
        image_name = LOCAL_IMAGE_BASE
    else:
        image_name = DEFAULT_IMAGE_BASE
    if args.extra:
        image_name += "-extra"
    if args.debug:
        image_name += "-dbg"
    return image_name + ":latest"

def get_base_image_name(args):
    if args.local:
        base_image_name = f"{LOCAL_IMAGE_BASE}-base"
    else:
        base_image_name = f"{DEFAULT_IMAGE_BASE}-base"
    if args.extra:
        base_image_name += "-extra"
    return base_image_name + ":latest"

def run_cmd(cmd, env=None, shell=False):
    print(f"==> Executing: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        res = subprocess.run(cmd, env=env, shell=shell)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    if res.returncode != 0:
        print(f"\nError: Command failed with exit code {res.returncode}")
        sys.exit(res.returncode)

def get_compose_args(args):
    cmd = ["docker", "compose", "-f", "docker-compose.yml"]
    if args.debug:
        cmd.extend(["-f", "docker-compose.debug.yml"])
    if os.path.exists("docker-compose.override.yml"):
        cmd.extend(["-f", "docker-compose.override.yml"])
    return cmd

def execute_command(cmd_name, args, extra_args=None):
    is_remote = args.remote if args.remote is not None else REMOTE_COMMAND.get(cmd_name, False)
    image_name = get_image_name(args)
    env = os.environ.copy()
    env["REP2_IMAGE"] = image_name
    if is_remote:
        env["DOCKER_HOST"] = f"ssh://{REMOTE_HOST_NAME}"

    compose_base = get_compose_args(args)

    if cmd_name == "up":
        if is_remote:
            flags = []
            if args.extra: flags.append("--extra")
            if args.local: flags.append("--local")
            if args.debug: flags.append("--debug")
            argv0 = os.path.basename(sys.argv[0])
            remote_cmd = f"cd {REMOTE_PATH} && ./{argv0} --noremote up {' '.join(flags)}"
            run_cmd(["ssh", "-t", REMOTE_HOST_NAME, remote_cmd])
        else:
            run_cmd(compose_base + ["up", "-d"], env=env)
            
    elif cmd_name == "build":
        flag_extra = "true" if args.extra else "false"
        flag_local = "true" if args.local else "false"
        flag_debug = "true" if args.debug else "false"
        context_p2 = LOCAL_P2_CONTEXT if args.local else DEFAULT_P2_CONTEXT
        context_proxy = LOCAL_PROXY_CONTEXT if args.local else DEFAULT_PROXY_CONTEXT
        build_cmd = [
            "docker", "build",
            "-t", image_name,
            "--build-arg", f"FLAG_EXTRA={flag_extra}",
            "--build-arg", f"FLAG_LOCAL={flag_local}",
            "--build-arg", f"FLAG_DEBUG={flag_debug}",
            "--build-context", f"p2-rep2={context_p2}",
            "--build-context", f"2chproxy.pl={context_proxy}",
            "-f", "docker/Dockerfile",
            "."
        ]
        run_cmd(build_cmd, env=env)
        run_cmd(["docker", "image", "prune", "-f"], env=env)

    elif cmd_name == "build-base":
        if args.local:
            base_image_name = f"{LOCAL_IMAGE_BASE}-base"
        else:
            base_image_name = f"{DEFAULT_IMAGE_BASE}-base"
        if args.extra:
            base_image_name += "-extra"
        base_image_name += ":latest"
        
        base_image_name = get_base_image_name(args)
        flag_extra = "true" if args.extra else "false"
        build_cmd = [
            "docker", "build",
            "-t", base_image_name,
            "--build-arg", f"FLAG_EXTRA={flag_extra}",
            "-f", "docker/Dockerfile.base",
            "."
        ]
        run_cmd(build_cmd, env=env)
        run_cmd(["docker", "image", "prune", "-f"], env=env)

    elif cmd_name == "down":
        run_cmd(compose_base + ["down"], env=env)
        
    elif cmd_name == "pull":
        run_cmd(compose_base + ["pull"], env=env)
        
    elif cmd_name == "logs":
        run_cmd(compose_base + ["logs"] + extra_args, env=env)
        
    elif cmd_name == "exec":
        run_cmd(compose_base + ["exec", SERVICE_NAME, "/bin/sh"], env=env)

    elif cmd_name == "config":
        run_cmd(compose_base + ["config"], env=env)

    elif cmd_name == "update":
        run_cmd(compose_base + ["cp", f"{LOCAL_P2_CONTEXT}/lib", f"{SERVICE_NAME}:/var/www"], env=env)
        run_cmd(compose_base + ["cp", f"{LOCAL_P2_CONTEXT}/rep2", f"{SERVICE_NAME}:/var/www"], env=env)
        run_cmd(compose_base + ["exec", SERVICE_NAME, "chown", "-R", "root:root", "/var/www/lib"], env=env)
        run_cmd(compose_base + ["exec", SERVICE_NAME, "chown", "-R", "root:root", "/var/www/rep2"], env=env)

    elif cmd_name == "confdiff":
        compose_str = " ".join(compose_base)
        sh_cmd = f"{compose_str} exec {SERVICE_NAME} diff /var/www/conf.orig /ext/conf | iconv -f SHIFT_JIS -t UTF-8"
        run_cmd(sh_cmd, env=env, shell=True)

    elif cmd_name == "prune":
        run_cmd(["docker", "image", "prune", "-f"], env=env)

    elif cmd_name == "clean":
        run_cmd(["docker", "image", "prune", "-f"], env=env)
        run_cmd(["docker", "builder", "prune", "-a"], env=env)
            
    elif cmd_name == "sync":
        run_cmd(["rsync", "-av", "-i", "--exclude", ".git", "--exclude", "rep2-data", "./", f"{REMOTE_HOST_NAME}:{REMOTE_PATH}/"])

    elif cmd_name == "upload":
        print(f"==> Uploading image {image_name} to {REMOTE_HOST_NAME}...")
        sh_cmd = f"docker save {image_name} | ssh {REMOTE_HOST_NAME} 'docker load'"
        run_cmd(sh_cmd, shell=True)

    elif cmd_name == "deploy":
        print("==> Starting deploy sequence...")

        deploy_steps = [
            "down",
            "build",
            "upload",
            "up",
            "prune"
        ]

        for i, cmd in enumerate(deploy_steps, 1):
            print(f"\n--- [{i}/{len(deploy_steps)}] {cmd} ---")
            execute_command(cmd, args)

        print("\n==> Deploy completed successfully!")

    else:
        print(f"Unknown command: {cmd_name}")
        sys.exit(1)

def main():
    command_descriptions = {
        "up": "docker compose up を実行",
        "build": "docker build を実行してイメージを作成",
        "build-base": "docker/Dockerfile.base を使用してベースイメージを作成",
        "down": "docker compose down を実行",
        "pull": "docker compose pull を実行",
        "logs": "docker compose logs を実行",
        "exec": "コンテナ内でシェル (/bin/sh) を実行",
        "config": "docker compose config を実行",
        "update": "ローカルのソースコードをコンテナ内にコピーして権限を修正",
        "confdiff": "コンテナ内の conf.orig と conf の差分を表示",
        "prune": "不要な Docker イメージを削除 (docker image prune -f)",
        "clean": "Docker のイメージとビルドキャッシュをすべて削除",
        "sync": "rsync でローカルディレクトリをリモートホストへ同期",
        "upload": "ビルドしたイメージをリモートホストへ転送",
        "deploy": "down -> build -> upload -> up のデプロイシーケンスを一括実行",
    }

    command_help = "コマンド一覧:\n"
    for cmd, desc in command_descriptions.items():
        remote_status = "--remote" if REMOTE_COMMAND.get(cmd, False) else "--noremote"
        command_help += f"  {cmd:<10} : {desc} (default: {remote_status})\n"

    parser = argparse.ArgumentParser(
        description="docker-rep2 build script",
        epilog=command_help,
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('command', choices=sorted(REMOTE_COMMAND.keys()), help="実行するコマンド")
    parser.add_argument('--extra', action='store_true', help="全部入りイメージにする")
    parser.add_argument('--local', action='store_true', default=True, help=f"ローカルのソースコードを使用する ({LOCAL_P2_CONTEXT}, {LOCAL_PROXY_CONTEXT}) / ローカルのイメージ名を使用する (default)")
    parser.add_argument('--nolocal', dest='local', action='store_false', help="githubのソースコードを使用する / githubと同じイメージ名を使用する")
    parser.add_argument('--debug', action='store_true', default=True, help="デバッグを有効にする (default)")
    parser.add_argument('--nodebug', dest='debug', action='store_false', help="デバッグを無効にする")
    parser.add_argument('--remote', action='store_true', default=None, help=f"リモートホストで実行する (SSH経由 / DOCKER_HOST=ssh://{REMOTE_HOST_NAME})")
    parser.add_argument('--noremote', dest='remote', action='store_false', help="ローカルホストで実行する")

    if argcomplete:
        argcomplete.autocomplete(parser)
    args, extra_args = parser.parse_known_args()

    execute_command(args.command, args, extra_args)

if __name__ == "__main__":
    main()
