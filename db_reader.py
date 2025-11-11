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

    def generate_prompt_from_row(self, row: Dict[str, Any]) -> str:
        """Generate DALL-E prompt from row data"""
        prompt_parts = []

        if self.prompt_template == 'wedding_dress':
            prompt_parts.append("A professional product photograph of a beautiful wedding dress on a mannequin.")
        elif self.prompt_template == 'wedding_dress_shop':
            prompt_parts.append("A professional photograph of a wedding dress shop interior.")
        elif self.prompt_template == 'wedding_hall':
            prompt_parts.append("A professional photograph of a wedding venue.")
        elif self.prompt_template == 'makeup_shop':
            prompt_parts.append("A professional photograph of a wedding makeup salon interior.")

        for field in self.prompt_fields:
            value = row.get(field)
            if value:
                if field in ['shop_name', 'name']:
                    prompt_parts.append(f"Named '{value}'.")
                elif field == 'description':
                    prompt_parts.append(value)
                elif field == 'features':
                    prompt_parts.append(f"Features: {value}.")
                elif field == 'specialty':
                    prompt_parts.append(f"Specializing in {value}.")
                elif field == 'venue_type':
                    prompt_parts.append(f"Type: {value}.")
                elif field == 'parking':
                    if str(value).lower() in ['true', 'yes', '1']:
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
