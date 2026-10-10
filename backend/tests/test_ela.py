from PIL import Image, ImageDraw
from backend.forensics.ela import ErrorLevelAnalysis


def test_ela_analysis():
    # Create test image
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill=(200, 50, 50))
    draw.text((60, 80), "TEST", fill=(255, 255, 255))

    ela = ErrorLevelAnalysis(quality=90, scale=15.0)
    result = ela.analyze(img)

    assert "mean_error" in result
    assert "variance_mean" in result
    assert "ela_image_b64" in result
    assert result["ela_image_b64"].startswith("data:image/png;base64,")
