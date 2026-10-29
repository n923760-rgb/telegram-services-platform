"""Fictitious identities and synthetic plans, never live-provider evidence."""


def profile(**changes):
    return {
        "language": "ar",
        "name": "استوديو مدى",
        "role": "تصميم هويات وتجارب رقمية",
        "intro": "نساعد المشاريع على التعبير عن شخصيتها بوضوح. هوية متناسقة وتجربة تواصل أقرب.",
        "actions": [
            {"label": "لنتحدث عن مشروعك", "url": "https://wa.me/966501234567"},
            {"label": "شاهد أعمالنا", "url": "https://example.invalid/work?id=00123"},
            {"label": "إنستغرام", "url": "https://www.instagram.com/"},
        ],
        "sections": [
            {
                "title": "نبدأ من قصتك",
                "body": "لكل مشروع شخصية تستحق أن تظهر. نرتب الفكرة ثم نبني حولها تجربة واضحة.",
                "items": [],
            },
            {
                "title": "كيف نساعدك؟",
                "body": "",
                "items": [
                    "تصميم الهوية البصرية",
                    "تصميم الواجهات الرقمية",
                    "إخراج المواد التعريفية",
                ],
            },
        ],
        **changes,
    }


def plan(**changes):
    return {
        "theme": "light",
        "accent": "#2f5d50",
        "alignment": "leading",
        "hero": "open",
        "title_size": 72,
        "columns": 2,
        "corner_radius": 16,
        "primary": 0,
        "action_order": [0, 1, 2],
        "section_order": [0, 1],
        **changes,
    }
