# 贡献指南 · Contributing

感谢你愿意为「吏部 · Libu」贡献力量！

## 开发环境

```bash
# 后端
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 前端
cd src/frontend
npm install

# 开发模式：先启动后端，再启动前端
PYTHONPATH=src python3 -m libu serve     # 终端 1
cd src/frontend && npm run dev           # 终端 2
```

浏览器访问 http://127.0.0.1:5173 即可。

## 目录约定

- `src/libu/` —— Python 后端（PDF/Word 生成、OCR 引擎、服务）
- `src/frontend/` —— Electron + React 前端
- `packaging/` —— deb / AppImage 打包脚本
- `pack/Windows/`、`pack/Loongarch/` —— 对应平台打包文件
- `tests/` —— 单元测试
- `源文件/` —— 需求与设计文档

## 代码规范

- Python 遵循 PEP 8，使用 4 空格缩进。
- 前端使用函数组件与 Hooks，遵循现有 CSS 命名（BEM 风格）。
- 新增 OCR 引擎：在 `src/libu/ocr_backends/` 下实现 `BaseOCRBackend` 子类并用 `@register_backend` 注册。
- 不要在任何源码或提交中写入 API Key、真实扫描文档。

## 提交测试

```bash
python -m unittest discover -s tests -v
```

## 提交说明

- 提交前请确保测试通过。
- 提交信息使用简洁的中文或英文描述。
- 采用 DCO：在提交信息末尾添加 `Signed-off-by: 你的名字 <邮箱>`，声明你有权提交该代码。
- 除非必要，不要新增大体积二进制文件；如需模型，请提供下载地址而非直接提交。

## 许可证

本项目以 GPL-3.0-or-later 发布。提交即表示你同意以该许可证授权你的贡献。
