"""Prompt presets for Tang Shifu's AI old photo studio MVP."""

from __future__ import annotations

from typing import Dict, List, Optional


IDENTITY_GUARDRAIL = (
    "Use the uploaded portrait as the identity reference. Preserve the person's "
    "facial identity, facial structure, age impression, natural expression, and "
    "recognizable features. Do not change identity, ethnicity, age, or gender."
)

PHOTO_REALISM_GUARDRAIL = (
    "Make it a realistic Chinese vintage photo studio portrait with natural skin "
    "texture, coherent lighting, authentic film grain, professional composition, "
    "and believable camera optics. Avoid cartoon, illustration, plastic skin, "
    "distorted face, extra people, text artifacts, watermark artifacts, and "
    "overly modern fashion details."
)


def _prompt(style_detail: str) -> str:
    return f"{IDENTITY_GUARDRAIL} Style: {style_detail}. {PHOTO_REALISM_GUARDRAIL}"


OLD_PHOTO_STYLES: List[Dict[str, object]] = [
    {
        "id": "worker_soldier_portrait",
        "name": "工农兵肖像",
        "description": "黑白做旧半身照，端正、朴素、有老档案馆质感。",
        "preview_url": "",
        "tags": ["black_and_white", "studio", "portrait", "1950s"],
        "recommended_count": 2,
        "prompts": [
            _prompt(
                "1950s Chinese worker-soldier studio portrait, black and white, "
                "plain cotton work jacket, upright half-body pose, simple cloth "
                "backdrop, modest expression, archival photo texture, slightly "
                "faded paper print"
            ),
            _prompt(
                "old Chinese state-owned photo studio portrait, monochrome film, "
                "buttoned workwear, direct frontal composition, soft overhead "
                "light, solemn but warm expression, subtle scratches and aged "
                "silver gelatin print feeling"
            ),
        ],
    },
    {
        "id": "hong_kong_star",
        "name": "港风女星",
        "description": "暖黄灯、蓬松发型、胶片颗粒感的港风明星照。",
        "preview_url": "",
        "tags": ["hong_kong", "cinematic", "warm_light", "1980s"],
        "recommended_count": 3,
        "prompts": [
            _prompt(
                "1980s Hong Kong movie star portrait, warm tungsten studio light, "
                "voluminous hair, elegant retro makeup, glossy magazine still, "
                "cinematic shallow depth of field, amber highlights, tasteful "
                "glamour without changing identity"
            ),
            _prompt(
                "classic Hong Kong film publicity portrait, warm yellow key light, "
                "soft rim light, retro blouse, expressive but natural pose, 35mm "
                "film grain, nostalgic color grading, realistic celebrity photo "
                "studio atmosphere"
            ),
        ],
    },
    {
        "id": "shanghai_lady",
        "name": "上海名媛",
        "description": "旗袍、柔光、老上海影楼氛围，适合精致半身照。",
        "preview_url": "",
        "tags": ["shanghai", "qipao", "soft_light", "republic_era"],
        "recommended_count": 3,
        "prompts": [
            _prompt(
                "1930s old Shanghai elegant qipao portrait, refined silk qipao, "
                "soft diffused studio lighting, side-facing three-quarter pose, "
                "painted studio backdrop, graceful expression, subtle sepia color, "
                "authentic Republican-era photo studio style"
            ),
            _prompt(
                "vintage Shanghai socialite photo, tailored qipao, delicate hair "
                "waves, pearl earrings, warm softbox lighting, seated portrait "
                "composition, old studio backdrop, faded color film, refined and "
                "realistic"
            ),
        ],
    },
    {
        "id": "republic_student",
        "name": "民国学生",
        "description": "蓝衫黑裙或学生长衫，清爽书卷气的民国学生照。",
        "preview_url": "",
        "tags": ["student", "republic_era", "clean", "youth"],
        "recommended_count": 2,
        "prompts": [
            _prompt(
                "Republican-era Chinese student portrait, simple blue student "
                "jacket and dark skirt or long gown, neat hairstyle, bookish and "
                "fresh temperament, school photo studio backdrop, soft daylight, "
                "slightly aged paper texture"
            ),
            _prompt(
                "old Chinese campus studio portrait from the 1920s to 1930s, "
                "clean student uniform, reserved natural smile, upright half-body "
                "composition, muted colors, gentle film grain, documentary realism"
            ),
        ],
    },
    {
        "id": "disco_80s",
        "name": "八零迪斯科",
        "description": "彩色灯光、动感姿势、复古舞厅味道的 80 年代照片。",
        "preview_url": "",
        "tags": ["disco", "color", "1980s", "dynamic"],
        "recommended_count": 3,
        "prompts": [
            _prompt(
                "1980s Chinese disco studio portrait, colorful neon party lights, "
                "retro patterned shirt or bright dress, confident dynamic pose, "
                "slightly glossy film look, dance hall atmosphere, realistic "
                "snapshot energy"
            ),
            _prompt(
                "old 1980s dance hall photo, saturated but faded colors, side "
                "lighting, stylish retro hair, lively pose, film flash effect, "
                "subtle motion feeling, authentic period clothing and background"
            ),
        ],
    },
    {
        "id": "model_opera",
        "name": "革命样板戏",
        "description": "军装或工装，昂首挺胸，舞台宣传照式的年代感。",
        "preview_url": "",
        "tags": ["stage", "red", "uniform", "1970s"],
        "recommended_count": 2,
        "prompts": [
            _prompt(
                "1970s Chinese revolutionary model opera publicity portrait, "
                "period military-style uniform or workwear, proud upright pose, "
                "red stage backdrop, dramatic but believable studio lighting, "
                "heroic composition, vintage propaganda photo realism"
            ),
            _prompt(
                "classic Chinese stage portrait inspired by revolutionary opera, "
                "structured uniform, chest lifted, determined gaze, red curtain "
                "background, theatrical side light, aged color print texture, "
                "realistic human proportions"
            ),
        ],
    },
    {
        "id": "studio_90s",
        "name": "九十年代影楼风",
        "description": "柔焦、纱巾、影楼布景，典型 90 年代写真质感。",
        "preview_url": "",
        "tags": ["studio", "soft_focus", "1990s", "portrait"],
        "recommended_count": 3,
        "prompts": [
            _prompt(
                "1990s Chinese photo studio glamour portrait, soft focus lens, "
                "light chiffon scarf, painted scenic backdrop, gentle pastel "
                "colors, romantic studio pose, realistic old studio print, "
                "tasteful and nostalgic"
            ),
            _prompt(
                "classic 1990s Chinese portrait studio photo, dreamy soft light, "
                "subtle vignette, decorative fabric prop, slightly overexposed "
                "film print, posed half-body composition, authentic period styling"
            ),
        ],
    },
    {
        "id": "beijing_photo_studio",
        "name": "老北京照相馆",
        "description": "长袍马褂、旗袍或正装，正襟危坐的老照相馆合影感。",
        "preview_url": "",
        "tags": ["beijing", "studio", "formal", "vintage"],
        "recommended_count": 2,
        "prompts": [
            _prompt(
                "old Beijing traditional photo studio portrait, formal seated "
                "pose, long gown or elegant qipao styling as appropriate, carved "
                "wood chair, plain studio curtain, calm expression, sepia toned "
                "paper print, realistic early studio photography"
            ),
            _prompt(
                "vintage Beijing family photo studio style single portrait, "
                "formal upright posture, traditional Chinese clothing details, "
                "classic wooden furniture, muted warm sepia, old lens softness, "
                "authentic aged photo surface"
            ),
        ],
    },
    {
        "id": "educated_youth",
        "name": "知青下乡",
        "description": "军帽、白衬衫、田野背景，60-70 年代知青上山下乡纪念照。",
        "preview_url": "",
        "tags": ["countryside", "youth", "1960s", "documentary"],
        "recommended_count": 2,
        "prompts": [
            _prompt(
                "1960s-1970s Chinese educated youth countryside portrait, plain "
                "white shirt, army green hat, rural farmland or village backdrop, "
                "earnest youthful expression, outdoor natural light, warm sepia "
                "documentary film tone, slightly faded and aged print"
            ),
            _prompt(
                "vintage Chinese sent-down youth commemorative photo, simple "
                "cotton work shirt, rolled-up sleeves, wheat field or terraced "
                "hillside background, half-body composition, candid natural pose, "
                "soft golden hour side light, realistic 1970s color film grain"
            ),
        ],
    },
]


STYLE_BY_ID: Dict[str, Dict[str, object]] = {
    str(style["id"]): style for style in OLD_PHOTO_STYLES
}


def get_old_photo_style(style_id: str) -> Optional[Dict[str, object]]:
    """Return a style preset by id."""
    return STYLE_BY_ID.get(style_id)


def list_old_photo_styles() -> List[Dict[str, object]]:
    """Return all old photo style presets."""
    return OLD_PHOTO_STYLES
