# SPDX-License-Identifier: GPL-3.0-or-later
"""吏部 FastAPI 服务端。"""
from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import Body, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import __version__, provider_probe, screenshot, service, viewer
from .config import BACKGROUND_PRESETS, OUTPUT_DIR, SUPPORTED_IMAGE_SUFFIXES
from .settings import get_provider, load_settings, save_settings, update_settings

app = FastAPI(title="吏部 Libu API", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "app": "libu", "version": __version__}


@app.get("/engines")
def engines():
    return {"engines": service.engines()}


@app.get("/meta")
def meta():
    return {
        "version": __version__,
        "backgrounds": BACKGROUND_PRESETS,
        "image_suffixes": sorted(SUPPORTED_IMAGE_SUFFIXES),
    }


@app.get("/settings")
def get_settings():
    return load_settings()


@app.put("/settings")
def put_settings(patch: dict = Body(...)):
    return update_settings(patch)


@app.get("/projects")
def projects(include_hidden: bool = False):
    return {"projects": service.projects(include_hidden=include_hidden)}


@app.post("/projects/delete")
def delete_project(payload: dict = Body(...)):
    source = payload.get("source")
    if not source:
        raise HTTPException(400, "缺少 source")
    service.delete_project(source)
    return {"ok": True}


@app.post("/projects/hide")
def hide_project(payload: dict = Body(...)):
    source = payload.get("source")
    if not source:
        raise HTTPException(400, "缺少 source")
    service.hide_project(source)
    return {"ok": True}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return service.save_upload(file.filename or "image.png", content)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/import-path")
def import_path(payload: dict = Body(...)):
    path = payload.get("path")
    if not path:
        raise HTTPException(400, "缺少 path")
    try:
        return service.save_upload_from_path(path)
    except FileNotFoundError:
        raise HTTPException(404, "文件不存在")
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/preprocess")
def preprocess(payload: dict = Body(...)):
    source = payload.get("source")
    if not source:
        raise HTTPException(400, "缺少 source")
    try:
        return service.preprocess_source(
            source, payload.get("box"), payload.get("auto_enhance", True)
        )
    except FileNotFoundError:
        raise HTTPException(404, "源文件不存在")


@app.post("/ocr")
def ocr(payload: dict = Body(...)):
    source = payload.get("source")
    backend = payload.get("backend") or "wechat"
    if not source:
        raise HTTPException(400, "缺少 source")
    try:
        results = service.run_ocr(
            source,
            backend,
            box=payload.get("box"),
            lang=payload.get("lang", "chi_sim+eng"),
            auto_enhance=payload.get("auto_enhance", True),
        )
    except FileNotFoundError:
        raise HTTPException(404, "源文件不存在")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"OCR 失败：{exc}")
    return {"results": results, "backend": backend, "count": len(results)}


@app.post("/ocr/upload")
async def ocr_upload(
    image: UploadFile = File(...),
    backend: str = Form("wechat"),
    lang: str = Form("chi_sim+eng"),
):
    saved = service.save_upload(image.filename or "image.png", await image.read())
    results = service.run_ocr(saved["path"], backend, lang=lang)
    return {"results": results, "source": saved["path"]}


@app.post("/generate")
def generate(payload: dict = Body(...)):
    pages = payload.get("pages")
    source = payload.get("source")
    if not source and not pages:
        raise HTTPException(400, "缺少 source 或 pages")
    try:
        if pages:
            out = service.generate_batch(
                pages,
                backend=payload.get("backend") or "wechat",
                outputs=payload.get("outputs"),
                base_name=payload.get("base_name"),
                auto_enhance=payload.get("auto_enhance", True),
                enable_ocr=payload.get("enable_ocr", True),
            )
        else:
            out = service.generate(
                source,
                backend=payload.get("backend") or "wechat",
                box=payload.get("box"),
                ocr_results=payload.get("ocr_results") or payload.get("results"),
                outputs=payload.get("outputs"),
                base_name=payload.get("base_name"),
                auto_enhance=payload.get("auto_enhance", True),
                enable_ocr=payload.get("enable_ocr", True),
            )
    except FileNotFoundError:
        raise HTTPException(404, "源文件不存在")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"生成失败：{exc}")
    return {"outputs": out, "output_dir": str(OUTPUT_DIR)}


@app.post("/models/import")
async def import_model(file: UploadFile = File(...), name: str = Form("")):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix != ".zip":
        raise HTTPException(400, "仅支持导入 .zip 模型压缩包")
    tmp = Path(tempfile.gettempdir()) / f"libu_model_{file.filename}"
    tmp.write_bytes(await file.read())
    try:
        info = service.import_model(str(tmp), name or None)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"导入失败：{exc}")
    finally:
        tmp.unlink(missing_ok=True)
    return {"ok": True, "model": info}


@app.post("/providers/models")
def provider_models(payload: dict = Body(...)):
    """探测某提供商可用的模型列表（Ollama / LM Studio / OpenAI 兼容）。"""
    key = payload.get("provider")
    if not key:
        raise HTTPException(400, "缺少 provider")
    cfg = dict(get_provider(key) or {})
    cfg.update({k: v for k, v in (payload.get("config") or {}).items() if v is not None})
    try:
        return {"ok": True, "models": provider_probe.list_models(key, cfg)}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, str(exc))


@app.post("/providers/test")
def provider_test(payload: dict = Body(...)):
    key = payload.get("provider")
    if not key:
        raise HTTPException(400, "缺少 provider")
    cfg = dict(get_provider(key) or {})
    cfg.update({k: v for k, v in (payload.get("config") or {}).items() if v is not None})
    return provider_probe.test_provider(key, cfg)


@app.get("/models")
def list_models():
    return {"models": service.models()}


@app.delete("/models/{name}")
def remove_model(name: str):
    if not service.delete_model(name):
        raise HTTPException(404, "模型不存在")
    return {"ok": True}


# --------------------------------------------------------------------------- #
# OCR 图片查看器
# --------------------------------------------------------------------------- #
@app.get("/viewer/images")
def viewer_images():
    return {"images": viewer.list_images()}


@app.post("/viewer/add")
def viewer_add(payload: dict = Body(...)):
    path = payload.get("path")
    if not path:
        raise HTTPException(400, "缺少 path")
    try:
        return {"image": viewer.add_path(path)}
    except FileNotFoundError:
        raise HTTPException(404, "文件不存在")
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/viewer/paste")
async def viewer_paste(file: UploadFile = File(...)):
    try:
        return {"image": viewer.save_pasted(await file.read(), file.filename or "clipboard.png")}
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/viewer/remove")
def viewer_remove(payload: dict = Body(...)):
    source = payload.get("source")
    if not source:
        raise HTTPException(400, "缺少 source")
    viewer.remove(source)
    return {"ok": True}


@app.post("/viewer/ocr")
def viewer_ocr(payload: dict = Body(...)):
    source = payload.get("source")
    if not source:
        raise HTTPException(400, "缺少 source")
    backend = payload.get("backend") or None
    try:
        results = viewer.ocr(source, backend=backend, lang=payload.get("lang", "chi_sim+eng"))
    except FileNotFoundError:
        raise HTTPException(404, "源文件不存在")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"OCR 失败：{exc}")
    return {"results": results, "count": len(results)}


# --------------------------------------------------------------------------- #
# 截屏 OCR
# --------------------------------------------------------------------------- #
@app.get("/screenshot/state")
def screenshot_state():
    return screenshot.get_state()


@app.put("/screenshot/state")
def screenshot_update(payload: dict = Body(...)):
    return screenshot.update_text(payload.get("text", ""))


@app.post("/screenshot/ingest")
def screenshot_ingest(payload: dict = Body(...)):
    path = payload.get("path")
    if not path:
        raise HTTPException(400, "缺少 path")
    try:
        return screenshot.ingest_image(
            path,
            backend=payload.get("backend") or None,
            lang=payload.get("lang", "chi_sim+eng"),
        )
    except FileNotFoundError:
        raise HTTPException(404, "截图文件不存在")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"识别失败：{exc}")


@app.post("/screenshot/upload")
async def screenshot_upload(
    file: UploadFile = File(...),
    backend: str = Form(""),
    lang: str = Form("chi_sim+eng"),
):
    try:
        return screenshot.ingest_bytes(
            await file.read(),
            file.filename or "screenshot.png",
            backend=backend or None,
            lang=lang,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"识别失败：{exc}")


@app.post("/screenshot/clear")
def screenshot_clear():
    return screenshot.clear()


@app.post("/screenshot/capture")
def screenshot_capture():
    """请求托盘助手开始区域截屏（写入触发文件）。"""
    screenshot.request_capture()
    return {"ok": True, "pending": screenshot.has_request()}


@app.get("/thumbnail")
def thumbnail(source: str = Query(...)):
    try:
        path = service.thumbnail_for(source)
    except FileNotFoundError:
        raise HTTPException(404, "源文件不存在")
    return FileResponse(path, media_type="image/png")


@app.get("/preview")
def preview(path: str = Query(...)):
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "文件不存在")
    return FileResponse(p)


@app.get("/download")
def download(path: str = Query(...)):
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "文件不存在")
    return FileResponse(p, filename=p.name)


@app.post("/open-output-dir")
def open_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.Popen(["xdg-open", str(OUTPUT_DIR)])
        return {"ok": True, "path": str(OUTPUT_DIR)}
    except FileNotFoundError:
        return {"ok": False, "path": str(OUTPUT_DIR)}


@app.exception_handler(Exception)
async def unhandled(_, exc: Exception):  # pragma: no cover
    return JSONResponse(status_code=500, content={"error": str(exc)})


# --------------------------------------------------------------------------- #
# 静态前端（deb / AppImage / 浏览器模式）
# --------------------------------------------------------------------------- #
def _mount_frontend() -> None:
    import os

    from fastapi.staticfiles import StaticFiles

    project_root = Path(__file__).resolve().parents[2]
    candidates = [
        os.environ.get("LIBU_WEB_DIR", ""),
        str(project_root / "frontend" / "dist"),
        str(project_root / "src" / "frontend" / "dist"),
        str(project_root / "web"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate, "index.html").exists():
            app.mount("/", StaticFiles(directory=candidate, html=True), name="web")
            return


_mount_frontend()
