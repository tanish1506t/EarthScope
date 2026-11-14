from typing import Optional


def _clean_html(raw_html: str) -> str:
    """Strip all leading and trailing whitespace from every line to prevent CommonMark code blocks."""
    return "\n".join(line.strip() for line in raw_html.strip().splitlines())



def render_metric_card_html(
    title: str,
    value: str,
    subtitle: str = "",
    delta: Optional[str] = None,
    delta_color: str = "normal",  # "positive", "negative", "neutral"
    icon: str = "📊",
    border_color: str = "#334155"
) -> str:
    """
    Returns HTML string for a glassmorphism metric card.
    Guaranteed clean of leading whitespace so it never triggers Markdown code blocks.
    """
    delta_html = ""
    if delta:
        if delta_color == "positive":
            pill_bg = "rgba(16, 185, 129, 0.15)"
            pill_fg = "#10b981"
            arrow = "▲"
        elif delta_color == "negative":
            pill_bg = "rgba(244, 63, 94, 0.15)"
            pill_fg = "#f43f5e"
            arrow = "▼"
        else:
            pill_bg = "rgba(56, 189, 248, 0.15)"
            pill_fg = "#38bdf8"
            arrow = "•"

        delta_html = f'<span style="display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 9999px; background: {pill_bg}; color: {pill_fg};">{arrow} {delta}</span>'

    sub_html = f'<div style="font-size: 11px; color: #64748b; margin-top: 6px;">{subtitle}</div>' if subtitle else ''

    html = f"""<div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.75) 0%, rgba(8, 18, 38, 0.9) 100%); border: 1px solid {border_color}; border-radius: 12px; padding: 16px 20px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4); backdrop-filter: blur(12px); margin-bottom: 12px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
<span style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8;">{title}</span>
<span style="font-size: 18px;">{icon}</span>
</div>
<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 8px;">
<span style="font-size: 26px; font-weight: 700; color: #f8fafc; font-family: 'Space Grotesk', Inter, sans-serif; letter-spacing: -0.02em;">{value}</span>
{delta_html}
</div>
{sub_html}
</div>"""
    return _clean_html(html)


def render_alert_callout(text: str, level: str = "info") -> str:
    """
    Renders styled scientific callout box.
    Guaranteed clean of leading whitespace.
    """
    color_map = {
        "info": ("#38bdf8", "rgba(56, 189, 248, 0.1)", "ℹ️"),
        "warning": ("#f59e0b", "rgba(245, 158, 11, 0.1)", "⚠️"),
        "success": ("#10b981", "rgba(16, 185, 129, 0.1)", "✅"),
        "caution": ("#f43f5e", "rgba(244, 63, 94, 0.1)", "🚨")
    }
    accent, bg, emoji = color_map.get(level, color_map["info"])

    html = f'<div style="background: {bg}; border-left: 3px solid {accent}; border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 12px 0; font-size: 13px; color: #e2e8f0; line-height: 1.5;"><span style="margin-right: 8px;">{emoji}</span> {text}</div>'
    return _clean_html(html)

