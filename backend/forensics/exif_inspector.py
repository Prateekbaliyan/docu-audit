import io
from PIL import Image, ExifTags
from typing import Dict, Any


class EXIFInspector:
    """
    EXIF Camera, Hardware & GPS Metadata Forensic Engine.
    Extracts hardware camera profiles, software signatures, GPS coordinates, and timestamp audit trails.
    """

    @staticmethod
    def _parse_gps_location(gps_info: dict) -> Dict[str, float]:
        """Converts raw GPS DMS (Degrees, Minutes, Seconds) to decimal latitude and longitude."""
        try:
            def dms_to_decimal(dms, ref):
                deg = float(dms[0])
                minute = float(dms[1])
                sec = float(dms[2])
                dec = deg + (minute / 60.0) + (sec / 3600.0)
                if ref in ['S', 'W']:
                    dec = -dec
                return round(dec, 6)

            lat = dms_to_decimal(gps_info[2], gps_info[1])
            lon = dms_to_decimal(gps_info[4], gps_info[3])
            return {"latitude": lat, "longitude": lon}
        except Exception:
            return {}

    def analyze_image(self, pil_image: Image.Image) -> Dict[str, Any]:
        """
        Parses EXIF tags from a PIL Image object.
        """
        exif_raw = pil_image._getexif() if hasattr(pil_image, '_getexif') else None

        if not exif_raw:
            return {
                "has_exif": False,
                "camera_make": None,
                "camera_model": None,
                "software": None,
                "capture_date": None,
                "gps": {},
                "is_suspicious": False,
                "reason": "No EXIF camera metadata embedded (stripped or synthetic image)"
            }

        exif_dict = {}
        gps_info = {}

        for tag_id, val in exif_raw.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)
            if tag_name == "GPSInfo":
                gps_info = val
            else:
                exif_dict[tag_name] = str(val)

        camera_make = exif_dict.get("Make")
        camera_model = exif_dict.get("Model")
        software = exif_dict.get("Software")
        capture_date = exif_dict.get("DateTimeOriginal") or exif_dict.get("DateTime")

        gps_coords = self._parse_gps_location(gps_info) if gps_info else {}

        # Flag suspicious visual editor tags in EXIF
        suspicious_software = []
        if software:
            sw_lower = software.lower()
            for s in ["photoshop", "gimp", "lightroom", "canva", "paint", "pixlr"]:
                if s in sw_lower:
                    suspicious_software.append(software)

        is_suspicious = len(suspicious_software) > 0

        return {
            "has_exif": True,
            "camera_make": camera_make,
            "camera_model": camera_model,
            "software": software,
            "capture_date": capture_date,
            "gps": gps_coords,
            "suspicious_software": suspicious_software,
            "is_suspicious": is_suspicious,
            "reason": f"EXIF metadata indicates software alteration: {software}" if is_suspicious else "Valid camera hardware EXIF profile"
        }
