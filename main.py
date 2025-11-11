"""
Main application for generating images for database rows with empty image_url
"""
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any
from db_reader import DatabaseReader, get_empty_rows_from_all_tables
from image_generator import ImageGenerator
from server_uploader import ServerUploader
import config


class ImageGenerationApp:
    """Main application orchestrator"""

    def __init__(self):
        """Initialize the application"""
        self.generator = ImageGenerator()
        self.uploader = ServerUploader()
        self.results = {
            'success': [],
            'failed': [],
            'skipped': []
        }

    def process_table(
        self,
        table_name: str,
        limit: int = None,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Process a single table and generate images for empty image_url rows

        Args:
            table_name: Name of the table to process
            limit: Maximum number of rows to process (None for all)
            dry_run: If True, only show what would be done without generating images

        Returns:
            Dictionary with counts of success, failed, and skipped rows
        """
        print(f"\n{'='*60}")
        print(f"Processing table: {table_name}")
        print(f"{'='*60}\n")

        reader = DatabaseReader(table_name)
        empty_rows = reader.find_empty_image_url_rows()

        if not empty_rows:
            print(f"✓ No rows with empty image_url found in {table_name}")
            return {'success': 0, 'failed': 0, 'skipped': 0}

        print(f"Found {len(empty_rows)} rows with empty image_url")

        # Apply limit if specified
        rows_to_process = empty_rows[:limit] if limit else empty_rows
        skipped_count = len(empty_rows) - len(rows_to_process)

        if dry_run:
            print("\n--- DRY RUN MODE ---")
            for i, row in enumerate(rows_to_process, 1):
                row_id = row.get('id', 'unknown')
                prompt = reader.generate_prompt_from_row(row)
                print(f"\n[{i}/{len(rows_to_process)}] Row ID: {row_id}")
                print(f"Prompt: {prompt}")
            print(f"\n{skipped_count} rows would be skipped due to limit")
            return {'success': 0, 'failed': 0, 'skipped': len(empty_rows)}

        # Process each row
        success_count = 0
        failed_count = 0

        for i, row in enumerate(rows_to_process, 1):
            row_id = row.get('id', f'row_{i}')
            print(f"\n[{i}/{len(rows_to_process)}] Processing row ID: {row_id}")

            # Generate prompt from row data
            prompt = reader.generate_prompt_from_row(row)

            # Generate filename
            filename = f"{table_name}_{row_id}"

            # Generate and save image locally
            dalle_url = self.generator.generate_and_save(
                prompt=prompt,
                filename=filename
            )

            if not dalle_url:
                failed_count += 1
                self.results['failed'].append({
                    'table': table_name,
                    'row_id': row_id,
                    'reason': 'image_generation_failed'
                })
                continue

            # Upload to server
            local_file = config.OUTPUT_DIR / f"{filename}.png"
            server_url_path = self.uploader.upload_file(local_file, table_name, filename)

            if not server_url_path:
                failed_count += 1
                self.results['failed'].append({
                    'table': table_name,
                    'row_id': row_id,
                    'reason': 'server_upload_failed'
                })
                continue

            # Update database with server URL path
            if reader.update_image_url(row_id, server_url_path):
                print(f"✓ Database updated: {server_url_path}")
                success_count += 1
                self.results['success'].append({
                    'table': table_name,
                    'row_id': row_id,
                    'image_url': server_url_path,
                    'filename': filename
                })
            else:
                print(f"⚠ Uploaded but DB update failed")
                failed_count += 1
                self.results['failed'].append({
                    'table': table_name,
                    'row_id': row_id,
                    'reason': 'db_update_failed'
                })

        # Record skipped rows
        if skipped_count > 0:
            self.results['skipped'].append({
                'table': table_name,
                'count': skipped_count
            })

        return {
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count
        }

    def process_all_tables(
        self,
        limit: int = None,
        dry_run: bool = False
    ) -> None:
        """
        Process all tables and generate images

        Args:
            limit: Maximum number of rows to process per table
            dry_run: If True, only show what would be done
        """
        print("\n" + "="*60)
        print("STARTING IMAGE GENERATION FOR ALL TABLES")
        print("="*60)

        total_stats = {'success': 0, 'failed': 0, 'skipped': 0}

        for table_name in config.DB_TABLES.keys():
            stats = self.process_table(table_name, limit, dry_run)
            total_stats['success'] += stats['success']
            total_stats['failed'] += stats['failed']
            total_stats['skipped'] += stats['skipped']

        # Print summary
        self.print_summary(total_stats, dry_run)

    def print_summary(self, stats: Dict[str, int], dry_run: bool = False) -> None:
        """Print summary of the operation"""
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)

        if dry_run:
            print("Mode: DRY RUN (no images generated)")
        else:
            print(f"✓ Successfully generated: {stats['success']}")
            print(f"✗ Failed: {stats['failed']}")

        if stats['skipped'] > 0:
            print(f"⊝ Skipped: {stats['skipped']}")

        if not dry_run and self.results['success']:
            print("\n--- Successful Generations ---")
            for item in self.results['success']:
                print(f"  {item['table']} - Row {item['row_id']}: {item['filename']}.png")

        if not dry_run and self.results['failed']:
            print("\n--- Failed Generations ---")
            for item in self.results['failed']:
                print(f"  {item['table']} - Row {item['row_id']}")

        print(f"\nOutput directory: {config.OUTPUT_DIR}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate images for database rows with empty image_url using DALL-E 2'
    )
    parser.add_argument(
        '--table',
        type=str,
        choices=list(config.DB_TABLES.keys()) + ['all'],
        default='all',
        help='Table to process (default: all)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=config.DEFAULT_GENERATION_LIMIT,
        help=f'Maximum number of rows to process per table (default: {config.DEFAULT_GENERATION_LIMIT or "unlimited"})'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually generating images'
    )
    parser.add_argument(
        '--list-tables',
        action='store_true',
        help='List all available tables and exit'
    )

    args = parser.parse_args()

    # List tables if requested
    if args.list_tables:
        print("Available tables:")
        for table_name in config.DB_TABLES.keys():
            print(f"  - {table_name}")
        return

    # Create app instance
    app = ImageGenerationApp()

    try:
        if args.table == 'all':
            app.process_all_tables(limit=args.limit, dry_run=args.dry_run)
        else:
            stats = app.process_table(args.table, limit=args.limit, dry_run=args.dry_run)
            app.print_summary(stats, dry_run=args.dry_run)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
