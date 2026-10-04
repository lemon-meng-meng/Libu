# SPDX-License-Identifier: GPL-3.0-or-later
"""吏部命令行入口。"""
from __future__ import annotations

import argparse
import sys


def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    import uvicorn

    uvicorn.run("libu.api:app", host=host, port=port, reload=reload)


def run_ocr(args) -> None:
    from .service import run_ocr as _run

    results = _run(args.image, args.backend, lang=args.lang)
    for r in results:
        print(r.get("text", ""))


def generate_cli(args) -> None:
    from .service import generate

    outputs = generate(args.image, backend=args.backend, base_name=args.name)
    for k, v in outputs.items():
        print(f"{k}: {v}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="libu", description="吏部 · 图片转电子文档")
    parser.add_argument("--version", action="store_true", help="显示版本")
    sub = parser.add_subparsers(dest="cmd")

    p_serve = sub.add_parser("serve", help="启动本地 API 服务")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")

    p_ocr = sub.add_parser("ocr", help="命令行 OCR")
    p_ocr.add_argument("image")
    p_ocr.add_argument("--backend", default="wechat")
    p_ocr.add_argument("--lang", default="chi_sim+eng")

    p_gen = sub.add_parser("generate", help="命令行生成 PDF/Word")
    p_gen.add_argument("image")
    p_gen.add_argument("--backend", default="wechat")
    p_gen.add_argument("--name", default=None)

    args = parser.parse_args(argv)
    if args.version:
        from . import __version__

        print(f"吏部 Libu {__version__}")
        return 0
    if args.cmd == "serve" or args.cmd is None:
        serve(
            getattr(args, "host", "127.0.0.1"),
            getattr(args, "port", 8000),
            getattr(args, "reload", False),
        )
        return 0
    if args.cmd == "ocr":
        run_ocr(args)
        return 0
    if args.cmd == "generate":
        generate_cli(args)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
