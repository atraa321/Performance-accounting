from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PdfRenderParams:
    paper: str = "A4"
    landscape: bool = True
    margin_mm: int = 10


class PdfRendererUnavailable(RuntimeError):
    pass


def render_pdf_from_html(*, html: str, params: PdfRenderParams) -> bytes:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # pragma: no cover
        raise PdfRendererUnavailable(
            "PDF 渲染依赖 Playwright/Chromium 未就绪。请在后端环境执行："
            "pip install -r requirements.txt；然后执行：python -m playwright install chromium"
        ) from e

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format=params.paper,
                landscape=params.landscape,
                print_background=True,
                margin={
                    "top": f"{params.margin_mm}mm",
                    "right": f"{params.margin_mm}mm",
                    "bottom": f"{params.margin_mm}mm",
                    "left": f"{params.margin_mm}mm",
                },
            )
            browser.close()
            return pdf_bytes
    except Exception as e:  # pragma: no cover
        raise PdfRendererUnavailable(
            "PDF 渲染失败（Chromium/系统依赖/权限问题）。若在 Docker/CI 中运行，请确保已安装浏览器与依赖。"
        ) from e
