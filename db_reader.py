from typing import List, Dict, Any
from sqlalchemy import text
import config


class DatabaseReader:
    """MySQL database reader for finding rows with empty image_url"""

    def __init__(self, table_name: str):
        if table_name not in config.DB_TABLES:
            raise ValueError(f"Unknown table: {table_name}. Available: {list(config.DB_TABLES.keys())}")

        self.table_name = table_name
        self.table_config = config.DB_TABLES[table_name]
        self.prompt_fields = self.table_config['prompt_fields']
        self.prompt_template = self.table_config['prompt_template']

    def find_empty_image_url_rows(self) -> List[Dict[str, Any]]:
        """Find all rows where image_url is empty or NULL"""
        engine = config.get_db_engine()

        query = text(f"""
            SELECT * FROM {self.table_name}
            WHERE image_url IS NULL OR image_url = ''
        """)

        with engine.connect() as conn:
            result = conn.execute(query)
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

        return rows

    def _sanitize_value(self, value: str) -> str:
        """Sanitize value to avoid DALL-E content policy violations"""
        if not value:
            return value

        # Replace problematic keywords
        replacements = {
            'SEXY': 'Sophisticated',
            'sexy': 'sophisticated',
            'SEXY_ELEGANT': 'Elegant and Sophisticated',
            'Sexy Elegant': 'Elegant and Sophisticated',
        }

        for old, new in replacements.items():
            value = value.replace(old, new)

        return value

    def generate_prompt_from_row(self, row: Dict[str, Any]) -> str:
        """Generate DALL-E prompt from row data"""
        prompt_parts = []

        if self.prompt_template == 'wedding_dress':
            prompt_parts.append("A professional product photograph of a beautiful wedding dress on a display.")
        elif self.prompt_template == 'wedding_dress_shop':
            prompt_parts.append("A professional photograph of a wedding dress shop interior.")
        elif self.prompt_template == 'wedding_hall':
            prompt_parts.append("A professional photograph of a wedding venue.")
        elif self.prompt_template == 'makeup_shop':
            prompt_parts.append("A professional photograph of a wedding makeup salon interior.")

        for field in self.prompt_fields:
            value = row.get(field)
            if value:
                # Sanitize text values
                if isinstance(value, str):
                    value = self._sanitize_value(value)

                if field in ['shop_name', 'name']:
                    # Skip name to avoid Korean text in prompt
                    pass
                elif field == 'description':
                    # Skip Korean description
                    pass
                elif field == 'features':
                    # Skip Korean features
                    pass
                elif field == 'specialty':
                    # Skip Korean specialty
                    pass
                elif field == 'venue_type':
                    venue_desc = value.replace('_', ' ').title()
                    prompt_parts.append(f"Venue type: {venue_desc}.")
                elif field == 'type':
                    prompt_parts.append(f"Style: {value.replace('_', ' ').title()}.")
                elif field == 'color':
                    # Skip color if Korean, only use if English
                    if value and all(ord(char) < 128 for char in value):
                        prompt_parts.append(f"Color: {value}.")
                elif field == 'shape':
                    # Skip shape if Korean
                    if value and all(ord(char) < 128 for char in value):
                        prompt_parts.append(f"Silhouette: {value}.")
                elif field == 'mood':
                    mood_text = value.replace('_', ' ').title()
                    prompt_parts.append(f"Mood: {mood_text}.")
                elif field == 'neck_line':
                    prompt_parts.append(f"Neckline: {value.replace('_', ' ').title()}.")
                elif field == 'fabric':
                    prompt_parts.append(f"Fabric: {value}.")
                elif field == 'parking':
                    # Handle both boolean and numeric parking values
                    if isinstance(value, (int, float)) and value > 0:
                        prompt_parts.append(f"Parking available for {int(value)} cars.")
                    elif str(value).lower() in ['true', 'yes', '1']:
                        prompt_parts.append("With parking available.")

        prompt_parts.append("High quality, professional, bright lighting, elegant atmosphere.")
        return " ".join(prompt_parts)

    def update_image_url(self, row_id: int, image_url: str) -> bool:
        """Update image_url for a specific row"""
        engine = config.get_db_engine()

        query = text(f"""
            UPDATE {self.table_name}
            SET image_url = :image_url
            WHERE id = :row_id
        """)

        try:
            with engine.connect() as conn:
                conn.execute(query, {'image_url': image_url, 'row_id': row_id})
                conn.commit()
            return True
        except Exception as e:
            print(f"✗ Failed to update DB: {str(e)}")
            return False


def get_empty_rows_from_all_tables() -> Dict[str, List[Dict[str, Any]]]:
    """Get all rows with empty image_url from all tables"""
    result = {}
    for table_name in config.DB_TABLES.keys():
        reader = DatabaseReader(table_name)
        empty_rows = reader.find_empty_image_url_rows()
        if empty_rows:
            result[table_name] = empty_rows
    return result
