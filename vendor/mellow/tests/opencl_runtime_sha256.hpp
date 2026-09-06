#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

// Streaming evidence digest for the native acceptance harness. Implements
// SHA-256 over bytes; uint buffers are serialized little-endian explicitly.
// The harness checks standard empty/abc vectors before touching a GPU, and the
// Python supervisor independently hashes every expected stress input/result.
class OpenCLTestSha256 {
public:
    void append(const uint8_t *input, size_t size) {
        bytes_ += size;
        for (size_t i = 0; i < size; ++i) {
            block_[used_++] = input[i];
            if (used_ == 64) { compress(); used_ = 0; }
        }
    }
    void words(const std::vector<uint32_t> &input) {
        for (uint32_t word : input) {
            uint8_t bytes[] {static_cast<uint8_t>(word), static_cast<uint8_t>(word >> 8),
                             static_cast<uint8_t>(word >> 16), static_cast<uint8_t>(word >> 24)};
            append(bytes, sizeof(bytes));
        }
    }
    std::string hex() const {
        auto copy = *this;
        const uint64_t bits = bytes_ * 8;
        uint8_t byte = 0x80;
        copy.append(&byte, 1);
        byte = 0;
        while (copy.used_ != 56) copy.append(&byte, 1);
        for (int shift = 56; shift >= 0; shift -= 8) {
            byte = static_cast<uint8_t>(bits >> shift);
            copy.append(&byte, 1);
        }
        constexpr char alphabet[] = "0123456789abcdef";
        std::string output;
        for (uint32_t word : copy.state_)
            for (int shift = 28; shift >= 0; shift -= 4) output += alphabet[(word >> shift) & 15];
        return output;
    }
private:
    static uint32_t rotate(uint32_t word, unsigned count) { return (word >> count) | (word << (32 - count)); }
    void compress() {
        constexpr uint32_t constants[] {
            0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
            0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
            0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
            0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
            0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
            0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
            0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
            0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
        uint32_t words[64] {};
        for (size_t i = 0; i < 16; ++i)
            words[i] = (static_cast<uint32_t>(block_[i * 4]) << 24) |
                       (static_cast<uint32_t>(block_[i * 4 + 1]) << 16) |
                       (static_cast<uint32_t>(block_[i * 4 + 2]) << 8) | block_[i * 4 + 3];
        for (size_t i = 16; i < 64; ++i) {
            const auto a = words[i - 15], b = words[i - 2];
            words[i] = words[i - 16] + (rotate(a, 7) ^ rotate(a, 18) ^ (a >> 3)) + words[i - 7] +
                       (rotate(b, 17) ^ rotate(b, 19) ^ (b >> 10));
        }
        auto a=state_[0], b=state_[1], c=state_[2], d=state_[3], e=state_[4], f=state_[5], g=state_[6], h=state_[7];
        for (size_t i = 0; i < 64; ++i) {
            const auto t1 = h + (rotate(e, 6) ^ rotate(e, 11) ^ rotate(e, 25)) + ((e & f) ^ (~e & g)) + constants[i] + words[i];
            const auto t2 = (rotate(a, 2) ^ rotate(a, 13) ^ rotate(a, 22)) + ((a & b) ^ (a & c) ^ (b & c));
            h=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
        }
        state_[0]+=a; state_[1]+=b; state_[2]+=c; state_[3]+=d;
        state_[4]+=e; state_[5]+=f; state_[6]+=g; state_[7]+=h;
    }
    uint32_t state_[8] {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    uint8_t block_[64] {};
    size_t used_ {};
    uint64_t bytes_ {};
};
