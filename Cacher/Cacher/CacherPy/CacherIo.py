import os


class CacherIo:
    def __init__(self, max_size: int, temp_path: str):
        self.max_size: int = max_size
        self.temp_path: str = temp_path
        self.temp_file = open(self.temp_path, 'wb+')
        self.memory_data: bytearray = bytearray(0)
        self.write_position = 0
        self.read_position = 0
        self.memory_size = 0

    def start_read(self):
        self._flush()
        self.read_position = 0
        self.temp_file.seek(0)

    def restart_append(self):
        self.temp_file.seek(0, 2)

    def close(self):
        self._flush()
        self.temp_file.close()
        self.temp_file = None

    def read(self, size: int) -> bytes:
        start_position = self.read_position
        self.read_position += size
        if start_position < self.memory_size:
            return self.memory_data[start_position:self.read_position]
        else:
            return self.temp_file.read(size)

    def write(self, in_data: bytes):
        in_data_size = len(in_data)
        if self.write_position + in_data_size > self.max_size:
            self.temp_file.write(in_data)
        else:
            self.memory_data += in_data
            self.memory_size += in_data_size

        self.write_position += in_data_size

    def _flush(self):
        self.temp_file.flush()
        os.fsync(self.temp_file.fileno())
