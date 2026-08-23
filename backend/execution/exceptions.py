"""
Custom exceptions for the migration execution pipeline.

MigrationChunkError is raised when a specific data chunk fails to insert
into the target database, carrying structured context about exactly what
failed so callers can log it, update job status, and halt cleanly.
"""


class MigrationChunkError(Exception):
    """Raised when a bulk_insert_chunk operation fails on the target database.

    Attributes:
        table_name: The target table that was being written to.
        chunk_offset: The zero-based index of the chunk within the stream.
        rows_in_chunk: Number of rows in the failed chunk.
        original_error: The underlying database exception.
    """

    def __init__(
        self,
        table_name: str,
        chunk_offset: int,
        rows_in_chunk: int,
        original_error: Exception,
    ):
        self.table_name = table_name
        self.chunk_offset = chunk_offset
        self.rows_in_chunk = rows_in_chunk
        self.original_error = original_error
        super().__init__(
            f"Chunk #{chunk_offset} ({rows_in_chunk} rows) failed for table "
            f"'{table_name}': {original_error}"
        )
