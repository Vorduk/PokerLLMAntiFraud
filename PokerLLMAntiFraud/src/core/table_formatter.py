import openpyxl
from openpyxl.utils import get_column_letter
from .mydataclasses import FraudRecord
from typing import List

class TableFormatter:
    def __init__(self, filename: str = "../results.xlsx"):
        self.filename = filename

    def change_file_name(self, new_filename: str) -> None:
        self.filename = new_filename

    def save_result(self, records: List[FraudRecord]) -> None:
        """Saves list of records to the table with self.filename name"""
        if not records:
            return

        # Prepare table file
        wb, ws = self._prepare_workbook()

        # Amount of rows to insert
        num = len(records)
        ws.insert_rows(2, num)  # Insert empty rows aftwer header

        # Insert rows with sorting by time
        for i, record in enumerate(reversed(records)):
            row_data = self._record_to_row(record)
            for col_idx, value in enumerate(row_data, start=1):
                ws.cell(row=2 + i, column=col_idx, value=value)

        self._auto_fit_columns(ws)
        wb.save(self.filename)

    def _prepare_workbook(self):
        """Opens existing file or creates new."""
        try:
            wb = openpyxl.load_workbook(self.filename)
            ws = wb.active
        except FileNotFoundError:
            wb = openpyxl.Workbook()
            ws = wb.active
            headers = ['time', 'game_id', 'incident_types', 'player_nicknames', 'description']
            ws.append(headers)
        return wb, ws

    def _record_to_row(self, record: FraudRecord) -> list:
        """Convert FraudRecord to row list."""
        time_str = record.time.strftime('%Y-%m-%d %H:%M:%S')
        game_id_str = str(record.game_id)
        types_str = ', '.join(record.incident_types) if record.incident_types else ''
        players_str = ', '.join(record.player_nicknames) if record.player_nicknames else ''
        description_str = record.description
        return [time_str, game_id_str, types_str, players_str, description_str]

    def _insert_data_row(self, ws, record: FraudRecord) -> None:
        """Insert the data to the second position (after headers)."""
        row_data = self._record_to_row(record)
        ws.insert_rows(2)
        for col_idx, value in enumerate(row_data, start=1):
            ws.cell(row=2, column=col_idx, value=value)

    def _auto_fit_columns(self, ws) -> None:
        """Set column width based on the string length"""
        for col_idx in range(1, 6):
            max_length = 0
            col_letter = get_column_letter(col_idx)
            for row in ws.iter_rows(min_col=col_idx, max_col=col_idx, values_only=True):
                for cell_value in row:
                    if cell_value is not None:
                        max_length = max(max_length, len(str(cell_value)))
            adjusted_width = max_length + 5
            ws.column_dimensions[col_letter].width = adjusted_width

