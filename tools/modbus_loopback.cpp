#include <iostream>
#include <vector>
#include <cstdint>
#include <iomanip>

static uint16_t crc16_calc_buf(const uint8_t *buf, size_t len) {
  uint16_t crc = 0xFFFF;
  for (size_t pos = 0; pos < len; pos++) {
    crc ^= (uint16_t)buf[pos];
    for (int i = 8; i != 0; i--) {
      if ((crc & 0x0001) != 0) {
        crc >>= 1;
        crc ^= 0xA001;
      } else
        crc >>= 1;
    }
  }
  return crc;
}

static void print_hex(const std::vector<uint8_t> &v) {
  for (auto b : v) std::cout << std::hex << std::setfill('0') << std::setw(2) << (int)b << " ";
  std::cout << std::dec << std::endl;
}

int main() {
  // Build a sample Read Holding Registers (0x03) request: slave 1, addr 2000, count 2
  std::vector<uint8_t> req = {0x01, 0x03, 0x07, 0xD0, 0x00, 0x02};
  uint16_t crc = crc16_calc_buf(req.data(), req.size());
  req.push_back(crc & 0xFF);
  req.push_back((crc >> 8) & 0xFF);
  std::cout << "Request frame:" << std::endl;
  print_hex(req);

  // Simulate a response: slave 1, func 3, bytecount 4, two registers (0x000A, 0x0014)
  std::vector<uint8_t> resp = {0x01, 0x03, 0x04, 0x00, 0x0A, 0x00, 0x14};
  uint16_t crc2 = crc16_calc_buf(resp.data(), resp.size());
  resp.push_back(crc2 & 0xFF);
  resp.push_back((crc2 >> 8) & 0xFF);
  std::cout << "Response frame:" << std::endl;
  print_hex(resp);

  // Verify CRC
  uint16_t read_crc = crc16_calc_buf(resp.data(), resp.size() - 2);
  uint16_t in_crc = resp[resp.size() - 2] | (resp[resp.size() - 1] << 8);
  std::cout << "Computed CRC: 0x" << std::hex << read_crc << ", in CRC: 0x" << in_crc << std::dec << std::endl;

  // Parse registers
  if (resp.size() >= 5) {
    uint8_t bytecount = resp[2];
    std::cout << "Bytecount: " << (int)bytecount << std::endl;
    for (size_t i = 0; i < bytecount / 2; ++i) {
      size_t idx = 3 + i * 2;
      uint16_t val = (resp[idx] << 8) | resp[idx + 1];
      std::cout << "Reg[" << i << "]=" << val << std::endl;
    }
  }
  return 0;
}
