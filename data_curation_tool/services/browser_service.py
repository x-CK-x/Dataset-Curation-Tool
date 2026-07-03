from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from ..paths import AppPaths

GECKODRIVER_API_URL = 'https://api.github.com/repos/mozilla/geckodriver/releases/latest'
GECKODRIVER_FALLBACK_VERSION = 'v0.37.0'


class BrowserService:
    """Firefox/geckodriver helper for local source-review/download workflows."""

    def __init__(self, paths: AppPaths):
        self.paths = paths
        self.tools_dir = paths.runtime / 'tools' / 'geckodriver'
        self.profile_root = paths.runtime / 'firefox_profiles'
        self.log_dir = paths.runtime / 'logs'
        self._driver: Any | None = None

    def platform_key(self) -> str:
        system = platform.system().lower()
        machine = platform.machine().lower()
        is_64 = sys.maxsize > 2**32
        if system == 'windows':
            if 'arm' in machine or 'aarch' in machine:
                return 'win-aarch64'
            return 'win64' if is_64 else 'win32'
        if system == 'linux':
            if 'aarch64' in machine or 'arm64' in machine:
                return 'linux-aarch64'
            return 'linux64' if is_64 else 'linux32'
        if system == 'darwin':
            return 'macos-aarch64' if 'arm' in machine or 'aarch' in machine else 'macos'
        raise RuntimeError(f'Unsupported platform: {platform.system()} {platform.machine()}')

    def geckodriver_filename(self) -> str:
        return 'geckodriver.exe' if platform.system().lower() == 'windows' else 'geckodriver'

    def geckodriver_path(self) -> Path:
        explicit = os.environ.get('DCT_GECKODRIVER_PATH', '').strip()
        if explicit:
            return Path(explicit).expanduser()
        return self.tools_dir / self.platform_key() / self.geckodriver_filename()

    def find_firefox_binary(self) -> str:
        explicit = os.environ.get('DCT_FIREFOX_BINARY', '').strip()
        if explicit:
            return explicit
        candidates: list[str] = []
        system = platform.system().lower()
        if system == 'windows':
            for base in [os.environ.get('PROGRAMFILES'), os.environ.get('PROGRAMFILES(X86)'), os.environ.get('LOCALAPPDATA')]:
                if base:
                    candidates.extend([str(Path(base) / 'Mozilla Firefox' / 'firefox.exe'), str(Path(base) / 'Firefox Developer Edition' / 'firefox.exe')])
        elif system == 'darwin':
            candidates.extend(['/Applications/Firefox.app/Contents/MacOS/firefox', '/Applications/Firefox Developer Edition.app/Contents/MacOS/firefox'])
        else:
            candidates.extend(['firefox', 'firefox-esr', 'firefox-developer-edition'])
        for cand in candidates:
            if os.path.isabs(cand) and Path(cand).exists():
                return cand
            found = shutil.which(cand)
            if found:
                return found
        return ''

    @staticmethod
    def _version(path: str, args: list[str]) -> str:
        if not path:
            return '<not found>'
        try:
            proc = subprocess.run([path, *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=10)
            return (proc.stdout or '').strip().splitlines()[0] if proc.stdout else '<no version output>'
        except Exception as exc:
            return f'<version check failed: {exc}>'

    @staticmethod
    def selenium_available() -> bool:
        try:
            import selenium  # noqa: F401
            return True
        except Exception:
            return False

    def _log_tail(self, max_chars: int = 8000) -> str:
        path = self.log_dir / 'geckodriver.log'
        if not path.exists():
            return ''
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
            return text[-max_chars:]
        except Exception as exc:
            return f'<could not read geckodriver log: {exc}>'

    def status(self) -> dict[str, Any]:
        gd = self.geckodriver_path()
        fb = self.find_firefox_binary()
        return {
            'platform_key': self.platform_key(),
            'geckodriver_path': str(gd),
            'geckodriver_exists': gd.exists(),
            'geckodriver_version': self._version(str(gd), ['--version']) if gd.exists() else '<not installed>',
            'firefox_binary': fb or '<not found>',
            'firefox_found': bool(fb),
            'firefox_version': self._version(fb, ['--version']) if fb else '<not found>',
            'selenium_available': self.selenium_available(),
            'private_mode_default': True,
            'browser_active': self._driver is not None,
            'geckodriver_log': str(self.log_dir / 'geckodriver.log'),
            'geckodriver_log_tail': self._log_tail(),
            'test_url': 'about:privatebrowsing',
        }

    def _asset_suffix(self, key: str) -> str:
        return f'-{key}.zip' if key.startswith('win') else f'-{key}.tar.gz'

    def _fallback_geckodriver_asset(self, key: str) -> dict[str, str]:
        suffix = self._asset_suffix(key)
        name = f"geckodriver-{GECKODRIVER_FALLBACK_VERSION}{suffix}"
        return {
            'name': name,
            'browser_download_url': f"https://github.com/mozilla/geckodriver/releases/download/{GECKODRIVER_FALLBACK_VERSION}/{name}",
        }

    def _latest_geckodriver_release(self, key: str) -> tuple[dict[str, Any], dict[str, Any]]:
        suffix = self._asset_suffix(key)
        try:
            req = urllib.request.Request(GECKODRIVER_API_URL, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'DataCurationTool-geckodriver-installer'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                release = json.loads(resp.read().decode('utf-8'))
            for item in release.get('assets', []):
                name = item.get('name', '')
                if name.endswith(suffix) and not name.endswith('.asc'):
                    return release, item
            raise RuntimeError(f'No geckodriver release asset ending with {suffix!r} found in latest release.')
        except Exception as exc:
            # GitHub API rate-limits and corporate TLS filters are common on
            # Windows.  Keep a direct latest-known release fallback so the GUI
            # can still install geckodriver without silently doing nothing.
            return {'tag_name': GECKODRIVER_FALLBACK_VERSION, 'fallback_reason': str(exc)}, self._fallback_geckodriver_asset(key)

    def _download_archive(self, url: str, archive: Path) -> None:
        req = urllib.request.Request(url, headers={'User-Agent': 'DataCurationTool-geckodriver-installer'})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp, archive.open('wb') as f:
                shutil.copyfileobj(resp, f)
            return
        except Exception as urllib_exc:
            curl = shutil.which('curl')
            if not curl:
                raise
            cmd = [curl, '-L', '--fail', '--ssl-no-revoke', '-o', str(archive), url]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=240)
            if proc.returncode != 0:
                raise RuntimeError(f'geckodriver download failed via urllib and curl. urllib={urllib_exc}; curl={proc.stdout[-2000:]}') from urllib_exc

    def install_geckodriver(self, force: bool = False) -> dict[str, Any]:
        target = self.geckodriver_path()
        if target.exists() and not force:
            return {'installed': True, 'path': str(target), 'message': 'geckodriver already installed'}
        key = self.platform_key()
        release, asset = self._latest_geckodriver_release(key)
        install_dir = target.parent
        install_dir.mkdir(parents=True, exist_ok=True)
        archive = install_dir / asset['name']
        self._download_archive(asset['browser_download_url'], archive)
        if archive.suffix.lower() == '.zip':
            with zipfile.ZipFile(archive, 'r') as zf:
                zf.extractall(install_dir)
        elif archive.name.endswith('.tar.gz'):
            with tarfile.open(archive, 'r:gz') as tf:
                tf.extractall(install_dir)
        else:
            raise RuntimeError(f'Unknown geckodriver archive type: {archive.name}')
        if not target.exists():
            matches = list(install_dir.rglob(self.geckodriver_filename()))
            if not matches:
                raise RuntimeError(f'geckodriver binary was not found in {install_dir}')
            matches[0].replace(target)
        target.chmod(target.stat().st_mode | 0o111)
        try:
            archive.unlink()
        except OSError:
            pass
        (install_dir / 'VERSION.txt').write_text(f"{release.get('tag_name','latest')}\n{asset['browser_download_url']}\n", encoding='utf-8')
        return {'installed': True, 'path': str(target), 'version': release.get('tag_name', 'latest')}

    def _profile_download_dir(self) -> Path:
        out = self.paths.runtime / 'browser_downloads'
        out.mkdir(parents=True, exist_ok=True)
        return out

    def launch(self, url: str = 'about:blank', private: bool = True, headless: bool = False) -> dict[str, Any]:
        try:
            from selenium import webdriver
            from selenium.webdriver.firefox.options import Options
            from selenium.webdriver.firefox.service import Service
        except Exception as exc:
            raise RuntimeError('selenium is not installed. Run update.bat/update.sh or install selenium>=4.20 in the Conda environment.') from exc
        gd = self.geckodriver_path()
        if not gd.exists():
            self.install_geckodriver(force=False)
        gd = self.geckodriver_path()
        fb = self.find_firefox_binary()
        if not fb:
            raise RuntimeError('Firefox binary was not found. Install Firefox or set DCT_FIREFOX_BINARY to firefox.exe.')
        self.profile_root.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        opts = Options()
        opts.binary_location = fb
        opts.add_argument('-no-remote')
        if private:
            opts.add_argument('-private-window')
            opts.set_preference('browser.privatebrowsing.autostart', True)
        if headless:
            opts.add_argument('-headless')
        width = os.environ.get('DCT_FIREFOX_WIDTH', '1440').strip()
        height = os.environ.get('DCT_FIREFOX_HEIGHT', '1000').strip()
        if width:
            opts.add_argument(f'--width={width}')
        if height:
            opts.add_argument(f'--height={height}')
        download_dir = self._profile_download_dir()
        opts.set_preference('browser.download.folderList', 2)
        opts.set_preference('browser.download.dir', str(download_dir))
        opts.set_preference('browser.download.useDownloadDir', True)
        opts.set_preference('pdfjs.disabled', False)
        opts.set_preference('browser.shell.checkDefaultBrowser', False)
        opts.set_preference('browser.startup.homepage_override.mstone', 'ignore')
        opts.set_preference('browser.tabs.warnOnClose', False)
        service = Service(
            executable_path=str(gd),
            log_output=str(self.log_dir / 'geckodriver.log'),
            service_args=['--profile-root', str(self.profile_root)],
        )
        if self._driver is not None:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None
        try:
            self._driver = webdriver.Firefox(service=service, options=opts)
            self._driver.get(url or ('about:privatebrowsing' if private else 'about:blank'))
        except Exception as exc:
            raise RuntimeError(
                'Firefox/geckodriver launch failed. Check Source Browser → Check Status, ensure Firefox is installed, and inspect runtime/logs/geckodriver.log. '
                f'Underlying error: {exc}; geckodriver log tail: {self._log_tail(2000)}'
            ) from exc
        return {
            'launched': True,
            'url': url,
            'private': private,
            'headless': headless,
            'geckodriver': str(gd),
            'firefox': fb,
            'download_dir': str(download_dir),
            'log': str(self.log_dir / 'geckodriver.log'),
        }

    def test_launch(self, url: str = 'about:privatebrowsing', seconds: float = 5.0, private: bool = True, headless: bool = False) -> dict[str, Any]:
        result = self.launch(url=url, private=private, headless=headless)
        time.sleep(max(0.5, min(float(seconds or 5.0), 30.0)))
        stopped = self.stop()
        return {**result, 'test_seconds': seconds, 'stopped_after_test': stopped.get('stopped', False)}


    def test_private_launch(self, url: str = 'about:privatebrowsing', headless: bool = False, close_after_seconds: float = 3.0) -> dict[str, Any]:
        return self.test_launch(url=url, seconds=close_after_seconds, private=True, headless=headless)

    def self_test(self, install: bool = True, launch: bool = False, headless: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {'ok': False, 'checks': []}
        if install:
            try:
                result['install'] = self.install_geckodriver(force=False)
                result['checks'].append({'name': 'geckodriver_install', 'ok': True})
            except Exception as exc:
                result['checks'].append({'name': 'geckodriver_install', 'ok': False, 'error': str(exc)})
        st = self.status()
        result['status'] = st
        result['checks'].extend([
            {'name': 'geckodriver_exists', 'ok': bool(st.get('geckodriver_exists'))},
            {'name': 'firefox_found', 'ok': bool(st.get('firefox_found'))},
            {'name': 'selenium_available', 'ok': bool(st.get('selenium_available'))},
        ])
        if launch:
            try:
                result['launch'] = self.test_launch(headless=headless, seconds=3.0)
                result['checks'].append({'name': 'private_launch', 'ok': True})
            except Exception as exc:
                result['checks'].append({'name': 'private_launch', 'ok': False, 'error': str(exc)})
        result['ok'] = all(c.get('ok') for c in result['checks'])
        return result

    def launch_direct(self, url: str = 'about:blank', private: bool = True, headless: bool = False) -> dict[str, Any]:
        """Open Firefox directly without Selenium as a diagnostic fallback."""
        fb = self.find_firefox_binary()
        if not fb:
            raise RuntimeError('Firefox binary was not found. Install Firefox or set DCT_FIREFOX_BINARY.')
        args = [fb]
        if private:
            args.append('-private-window')
        if headless:
            args.append('-headless')
        args.append(url or 'about:blank')
        proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {'launched': True, 'mode': 'firefox_direct', 'pid': proc.pid, 'url': url, 'private': private, 'headless': headless, 'firefox': fb}

    def visible_self_test(self, url: str = 'about:blank') -> dict[str, Any]:
        """Install/check geckodriver and launch a visible private Firefox window."""
        before = self.status()
        if not before.get('geckodriver_exists'):
            self.install_geckodriver(force=False)
        result = self.launch(url=url or 'about:blank', private=True, headless=False)
        after = self.status()
        return {'ok': True, 'before': before, 'launch': result, 'after': after}

    def stop(self) -> dict[str, Any]:
        if self._driver is None:
            return {'stopped': False, 'message': 'No active browser session.'}
        try:
            self._driver.quit()
        finally:
            self._driver = None
        return {'stopped': True}
