from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from .deps import ctx

router = APIRouter(prefix='/browser', tags=['browser'])


class InstallPayload(BaseModel):
    force: bool = False


class LaunchPayload(BaseModel):
    url: str = 'about:blank'
    private: bool = True
    headless: bool = False


class DirectLaunchPayload(BaseModel):
    url: str = 'about:blank'
    private: bool = True
    headless: bool = False


class BrowserTestPayload(BaseModel):
    url: str = 'about:privatebrowsing'
    private: bool = True
    headless: bool = False
    seconds: float = 5.0


class TestLaunchPayload(BaseModel):
    url: str = 'about:privatebrowsing'
    headless: bool = False
    close_after_seconds: float = 3.0


class SelfTestPayload(BaseModel):
    install: bool = True
    launch: bool = False
    headless: bool = True


@router.get('/status')
def status(request: Request):
    return ctx(request).browser.status()


@router.post('/geckodriver/install')
def install(payload: InstallPayload, request: Request):
    return ctx(request).browser.install_geckodriver(payload.force)


@router.post('/launch')
def launch(payload: LaunchPayload, request: Request):
    return ctx(request).browser.launch(payload.url, payload.private, payload.headless)


@router.post('/self-test')
def self_test(payload: SelfTestPayload, request: Request):
    return ctx(request).browser.self_test(payload.install, payload.launch, payload.headless)


@router.post('/test-private-launch')
def test_private_launch(payload: TestLaunchPayload, request: Request):
    return ctx(request).browser.test_private_launch(payload.url, payload.headless, payload.close_after_seconds)




@router.post('/test')
def test(payload: BrowserTestPayload, request: Request):
    return ctx(request).browser.test_launch(payload.url, payload.seconds, payload.private, payload.headless)


@router.post('/launch-direct')
def launch_direct(payload: DirectLaunchPayload, request: Request):
    return ctx(request).browser.launch_direct(payload.url, payload.private, payload.headless)


@router.post('/visible-self-test')
def visible_self_test(payload: DirectLaunchPayload, request: Request):
    return ctx(request).browser.visible_self_test(payload.url)


@router.post('/stop')
def stop(request: Request):
    return ctx(request).browser.stop()
